import requests
import falcon
from utils.config import (GOOGLE_OAUTH2_CLIENT_ID,
                          GOOGLE_OAUTH2_CLIENT_SECRET,
                          GOOGLE_OAUTH2_REDIRECT_URI,)

GOOGLE_OAUTH2_AUTH_URL = 'https://www.googleapis.com/oauth2/v3/token'
GOOGLE_OAUTH2_AUTH_USER_INFO = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_OAUTH2_TOKEN_INFO = 'https://oauth2.googleapis.com/tokeninfo'


def google_sign_in(code: str) -> dict:
    """get user info by google oauth2

    Args:
        code (str): user redirect params "code".

    Returns:
        dict: {
            "id": <str>,
            "email": <str>@taki.dog,
            "verified_email": <bool>true,
            "picture": "<str> image url",
            "hd": "<str>"
            }
    """
    get_id_token_request = requests.post(url=GOOGLE_OAUTH2_AUTH_URL, data={
        "code": code,
        "client_id": GOOGLE_OAUTH2_CLIENT_ID,
        "client_secret": GOOGLE_OAUTH2_CLIENT_SECRET,
        "redirect_uri": GOOGLE_OAUTH2_REDIRECT_URI,
        "grant_type": "authorization_code"
    })

    if get_id_token_request.status_code != 200 or get_id_token_request.json().get("error", "") != "":
        raise falcon.HTTPUnauthorized(
            description="Google sign in error, please retry.")
        # raise ValueError("Invalid token")

    _token_json = get_id_token_request.json()

    get_user_profile = requests.get(
        url=GOOGLE_OAUTH2_AUTH_USER_INFO,
        headers={
            "Authorization": f"{_token_json.get('token_type')} {_token_json.get('access_token')}"
        })
    if get_user_profile.status_code != 200:
        raise falcon.HTTPForbidden(
            description="something error on get user info.")
        # raise ValueError("Get user info error")

    return get_user_profile.json()


def get_user_profile_from_id_token(id_token: str) -> dict:

    get_user_profile = requests.get(
        url=GOOGLE_OAUTH2_TOKEN_INFO,
        params={
            "id_token": id_token
        })
    if get_user_profile.status_code != 200:
        raise falcon.HTTPForbidden(
            description="something error on get user info.")

    return get_user_profile.json()
