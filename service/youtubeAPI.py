from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import isodate
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
import os
from typing import List
import pickle
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
import os
from google.auth.transport.requests import Request
import pickle


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
                os.getenv("SCOPES"),
            )
            creds = flow.run_local_server(port=0)

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
            .list(part="id", channelId=channelID, maxResults=1, order="date")
            .execute()
        )

        video_ids = []

        for video in videos["items"]:
            if video["id"]["kind"] == "youtube#video":
                video_id = video["id"]["videoId"]
                video_ids.append("%s" % video_id)

        return video_ids

    def get_RecipeInfo(self, channelName: str) -> List[object]:
        try:
            channelId = self.findChannelId(channelName)
            arr = self.findVideoByChannelId(channelId)
            results = self.getVideoInfoById(arr)
            return results
        except HttpError as e:
            print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
            return None

    # 영상 Id를 통해 필요한 데이터 수집
    def getVideoInfoById(self, videoIds: List[str]) -> List[object]:
        video_info = []

        for videoId in videoIds:
            getInfo = (
                self.youtube.videos()
                .list(
                    part="snippet,statistics,topicDetails,contentDetails,status",
                    id=videoId,
                )
                .execute()
            )

            view_count = getInfo["items"][0]["statistics"]["viewCount"]
            like_count = getInfo["items"][0]["statistics"]["likeCount"]

            title = getInfo["items"][0]["snippet"]["title"]
            published_at = getInfo["items"][0]["snippet"]["publishedAt"]
            descriptioin = getInfo["items"][0]["snippet"]["description"]
            thumnail = getInfo["items"][0]["snippet"]["thumbnails"]["default"]["url"]

            duration = getInfo["items"][0]["contentDetails"]["duration"]
            parsed_duration = isodate.parse_duration(duration)
            run_time = parsed_duration.total_seconds()

            if run_time > 60:  # 쇼츠는 tags가 없는 것도 있던데...?
                tags = getInfo["items"][0]["snippet"]["tags"]
            else:
                tags = []

            category = getInfo["items"][0]["topicDetails"]["topicCategories"]

            transcript_list = YouTubeTranscriptApi.list_transcripts(videoId)
            transcript = transcript_list.find_transcript(["ko", "en"])
            if transcript == None:
                script = []
            else:
                script = transcript.fetch()
            processed_data = process_data(script)

            video_info_seed = {
                "id": videoId,
                "title": title,
                "publishedAt": published_at,
                "description": descriptioin,
                "thumnail": thumnail,
                "category": category,
                "tags": tags,
                "viewCount": view_count,
                "like_count": like_count,
                "run_time": run_time,
                "script": processed_data,
            }

            video_info.append(video_info_seed)

        return video_info
