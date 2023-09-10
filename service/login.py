from dotenv import load_dotenv
from datetime import timezone, timedelta
from jose import jwt
from starlette.responses import RedirectResponse
from fastapi import Request
import requests
import os

load_dotenv()


class AppleOauth2:
    """
    Apple Authentication Backend
    """

    __name__ = "apple"
    ACCESS_TOKEN_URL = "https://appleid.apple.com/auth/token"

    def do_auth(self, access_token):
        response_data = {}
        client_id = "net.recipeade.svelte"
        client_secret = self.get_key_and_secret()

        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": access_token,
            "grant_type": "authorization_code",
            "redirect_uri": "https://recipeade.net/login/oauth_apple",
        }

        res = requests.post(AppleOauth2.ACCESS_TOKEN_URL, data=data, headers=headers)
        response_dict = res.json()
        id_token = response_dict.get("id_token", None)

        if id_token:
            decoded = jwt.decode(id_token, "", verify=False)
            response_data.update(
                {"email": decoded["email"]} if "email" in decoded else None
            )
            response_data.update({"name": decoded["sub"]} if "sub" in decoded else None)

        response = {}
        response.update(response_data)
        response.update(
            {"access_token": access_token} if "access_token" not in response else None
        )

        return response

    def get_key_and_secret(self):
        """
        Get Key and Secret from settings
        """
        headers = {"kid": os.getenv("SOCIAL_AUTH_APPLE_KEY_ID")}

        payload = {
            "iss": "49AL3MH8WT",
            "iat": timezone.now(),
            "exp": timezone.now() + timedelta(days=180),
            "aud": "https://appleid.apple.com",
            "sub": os.getenv("SOCIAL_AUTH_CLIENT_ID"),
        }

        client_secret = jwt.encode(
            payload,
            os.getenv("SOCIAL_AUTH_APPLE_PRIVATE_KEY"),
            algorithm="ES256",
            headers=headers,
        ).decode("utf-8")

        return client_secret
