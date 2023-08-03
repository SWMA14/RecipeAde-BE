from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from youtube_transcript_api import YouTubeTranscriptApi

from schema.schemas import RecipeCreate,TagCreate

from dotenv import load_dotenv
from typing import List
from datetime import datetime
import pickle
import isodate
import pickle
import os

from schema.schemas import ChannelCreate


def convert_seconds_to_time_str(seconds: float) -> str:
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"({minutes:02d}:{seconds:02d})"


def process_data(data_list):
    result = []
    for item in data_list:
        time_str = convert_seconds_to_time_str(item["start"])
        new_text = f"{time_str} {item['text']}"
        result.append(new_text)
    return result


def get_auth():
    load_dotenv()

    creds = None
    current_script_path = os.path.abspath(__file__)
    current_script_dir = os.path.dirname(current_script_path)
    credentials_path = os.path.join(current_script_dir, "credentials.json")

    if os.path.exists("./auto_token.pickle"):
        with open("auto_token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path,
                scopes=[
                    "openid",
                    "https://www.googleapis.com/auth/userinfo.email",
                    "https://www.googleapis.com/auth/userinfo.profile",
                    "https://www.googleapis.com/auth/youtube.force-ssl",
                ],
            )
            creds = flow.run_local_server()
        with open("auto_token.pickle", "wb") as token:
            pickle.dump(creds, token)

    youtube = build(
        os.getenv("YOUTUBE_API_SERVICE_NAME"),
        os.getenv("YOUTUBE_API_VERSION"),
        developerKey=os.getenv("API_KEY"),
        credentials=creds,
    )

    return youtube


class YoutubeAPI:
    def __init__(self):
        self.youtube = get_auth()

    # 원하는 채널 명을 검색하면 채널 id를 반환함
    def findChannelId(self, channel: str) -> str:
        findChannel = (
            self.youtube.search().list(part="id", q=channel, type="channel").execute()
        )

        channel_id = findChannel["items"][0]["id"]["channelId"]
        return channel_id

    # 채널 Id를 통해 date 별로 가장 최근에 나온 영상 순서대로 video 검색
    def findVideoByChannelId(self, channelID: str) -> List[str]:
        videos = (
            self.youtube.search()
            .list(part="id", channelId=channelID, maxResults=5, order="date")
            .execute()
        )

        video_ids = []
        short_ids = []

        for video in videos["items"]:
            if video["id"]["kind"] == "youtube#video":
                video_id = video["id"]["videoId"]
                video_ids.append("%s" % video_id)
            if video["id"]["kind"] == "youbue#short":
                short_id = video["id"]["videoID"]
                short_ids.append("%s" % short_id)
        return video_ids, short_ids

    def get_RecipeInfo(self, channelName: str) -> List[object]:
        try:
            channelId = self.findChannelId(channelName)
            arr = self.findVideoByChannelId(channelId)
            results = self.getVideoInfoById(arr)
            return results
        except HttpError as e:
            print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
            return None

    def getTagById(self,videoId: str) -> List[str]:
        #videoId를 받으면 Tag의 리스프 리턴
        youtube_response = (
            self.youtube.videos()
            .list(
                part="snippet",
                id=videoId,
            )
            .execute()
        )
         
        tags = youtube_response["items"][0]["snippet"].get("tags")

        return tags



    # 영상 Id를 통해 필요한 데이터 수집
    def getVideoInfoById(self, videoId: str) -> tuple[RecipeCreate, List[str],str]:
        youtube_response = (
            self.youtube.videos()
            .list(
                part="snippet,statistics,topicDetails,contentDetails,status",
                id=videoId,
            )
            .execute()
        )
        

        view_count = youtube_response["items"][0]["statistics"]["viewCount"]
        like_count = youtube_response["items"][0]["statistics"]["likeCount"]

        title = youtube_response["items"][0]["snippet"]["title"]
        published_at = youtube_response["items"][0]["snippet"]["publishedAt"]
        #descriptioin = youtube_response["items"][0]["snippet"]["description"]
        thumbnail = youtube_response["items"][0]["snippet"]["thumbnails"]["default"]["url"]
        channel_id = youtube_response["items"][0]["snippet"]["channelId"]
        duration = youtube_response["items"][0]["contentDetails"]["duration"]
        parsed_duration = isodate.parse_duration(duration)
        run_time = parsed_duration.total_seconds()

        if run_time > 60:  # 쇼츠는 tags가 없는 것도 있던데...?
            tags = youtube_response["items"][0]["snippet"]["tags"]
        else:
            tags = []
        #category = youtube_response["items"][0]["topicDetails"]["topicCategories"]

        # transcript_list = YouTubeTranscriptApi.list_transcripts(videoId)
        # transcript = transcript_list.find_transcript(["ko", "en"])
        # if transcript == None:
        #     script = []
        # else:
        #     script = transcript.fetch()
        # processed_data = process_data(script)

        recipe_data = RecipeCreate(
            youtubeVideoId=videoId,
            youtubeTitle=title,
            youtubeViewCount=view_count,
            difficulty=0,
            category="",
            youtubePublishedAt=published_at,
            youtubeLikeCount=like_count,
            youtubeChannel=channel_id,
            youtubeThumbnail=thumbnail
            #youtubeTag=tags
            #youtubeDescription=descriptioin,  # 추후 빼야함
            #youtubeCaption=(processed_data),  # 추후 빼야함
        )


        return (
            recipe_data,
            tags,
            channel_id,
        )

    def get_channelInfo(self, channelID: str) -> ChannelCreate:
        try:
            channel_request = self.youtube.channels().list(part="snippet", id=channelID)

            channel_response = channel_request.execute()

            channel_name = channel_response["items"][0]["snippet"]["title"]
            thumbnail_url = channel_response["items"][0]["snippet"]["thumbnails"][
                "high"
            ]["url"]

            channel_object = ChannelCreate(
                channelID=channelID,
                ChannelName=channel_name,
                ChannelThumbnail=thumbnail_url,
            )
            return channel_object
        except HttpError as error:
            print(f"An HTTP error {error.resp.status} occurred: {error.content}")
            return None

    def get_subscriptions(self) -> List[str]:
        # 유저가 구독한 채널 정보를 가져옵니다.
        try:
            channelLists = []
            nextPageToken = None
            while True:
                subscriptions_request = self.youtube.subscriptions().list(
                    part="snippet", mine=True, maxResults=50, pageToken=nextPageToken
                )
                subscription_response = subscriptions_request.execute()

                subscriptions = subscription_response["items"]
                for subscription in subscriptions:
                    channel_title = subscription["snippet"]["title"]
                    channel_id = subscription["snippet"]["resourceId"]["channelId"]
                    channel_thumnail = subscription["snippet"]["thumbnails"]["default"][
                        "url"
                    ]
                    channelLists.append(
                        {
                            "id": channel_id,
                            "title": channel_title,
                            "thumbnail": channel_thumnail,
                        }
                    )
                nextPageToken = subscription_response.get("nextPageToken")

                if not nextPageToken:
                    break
        except HttpError as error:
            print(f"An HTTP error {error.resp.status} occurred: {error.content}")
            return None

        return channelLists

    def get_videos_by_date(
        self, published_after: datetime, subscriptions: List[str]
    ) -> List[str]:
        # 특정 날짜와 구독자 목록이 주어지면 이를 바탕으로 해당 날짜 이후에 나온 구독자의 영상이 나온다
        video_ids = []
        for subscription in subscriptions:
            search_request = self.youtube.search().list(
                part="snippet",
                channelId=subscription,
                type="video",
                maxResults=50,
                publishedAfter=published_after,
            )
            search_response = search_request.execute()

            video_id = search_response["items"][0]["id"]["videoId"]

            video_ids.append(video_id)

        return video_ids
