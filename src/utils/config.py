import os

try:
    REDIS_URL = os.environ['REDIS_URL']
except KeyError:
    REDIS_URL = 'redis://127.0.0.1:6379'

ALLOW_APPLICATION_OWNER_MODIFY = True
ANNOUNCEMENT_REQUIRED_FIELD = ["title"]

ANNOUNCEMENT_FIELD = {
    "title": {"type": str, "allow_user_set": True, "default": "Title not set"},
    "id": {"type": int, "allow_user_set": False, "default": 0},
    "publishedAt": {"type": str, "allow_user_set": False, "default": None},
    "weight": {"type": int, "allow_user_set": True, "default": 0},
    "url": {"type": str, "allow_user_set": True, "default": None},
    "imgUrl": {"type": str, "allow_user_set": True, "default": None},
    "description": {"type": str, "allow_user_set": True, "default": None},
    "location": {"type": str, "allow_user_set": True, "default": None},
    "expireTime": {"type": str, "allow_user_set": True, "default": None},
    "tag": {"type": list, "allow_user_set": True, "default": []},
    "applicant": {"type": str, "allow_user_set": False, "default": None}
}

APPLICANT_HOSTNAME_LIMIT = []

# copy announcement field because application field have different config.
APPLICATION_FIELD = ANNOUNCEMENT_FIELD
del APPLICATION_FIELD['id']
APPLICATION_FIELD['application_id'] = {
    "type": str, "allow_user_set": False, "default": ""}
APPLICATION_FIELD['fcm'] = {
    "type": str, "allow_user_set": False, "default": ""}
MAX_TAGS_LIMIT = 20
CACHE_EXPIRE_SEC = 120

LANGUAGE_TAG = {'zh': ['zh', 'zh-tw', 'zh-hant'], "en": ['en']}

try:
    ADMIN = [i for i in os.environ['ADMIN'].split(';') if i != ""]
except KeyError:
    ADMIN = []

JWT_EXPIRE_TIME = 3600

# SS_SUPPORT_GOOGLE_OAUTH2 is for server-side apps sign in with google
# Detail : https://developers.google.com/identity/sign-in/web/server-side-flow
try:
    SS_SUPPORT_GOOGLE_OAUTH2 = os.environ['SS_SUPPORT_GOOGLE_OAUTH2'].lower(
    ) == "true"
except KeyError:
    SS_SUPPORT_GOOGLE_OAUTH2 = False

GOOGLE_OAUTH2_CLIENT_ID = None
GOOGLE_OAUTH2_CLIENT_SECRET = None
GOOGLE_OAUTH2_REDIRECT_URI = None

if SS_SUPPORT_GOOGLE_OAUTH2:
    GOOGLE_OAUTH2_CLIENT_ID = os.environ['GOOGLE_OAUTH2_CLIENT_ID']
    GOOGLE_OAUTH2_CLIENT_SECRET = os.environ['GOOGLE_OAUTH2_CLIENT_SECRET']
    GOOGLE_OAUTH2_REDIRECT_URI = os.environ['GOOGLE_OAUTH2_REDIRECT_URI']

APPLICATION_EXPIRE_TIME_AFTER_APPROVE = 60*60*24*30

# The audience registered claim identifies the
# intended recipient of the client secret.
# Since the client secret is sent to the validation
# server, use https://appleid.apple.com.
APPLE_SIGN_IN_AUD = None
try:
    APPLE_SIGN_IN_AUD = os.environ['APPLE_SIGN_IN_AUD']
except KeyError:
    APPLE_SIGN_IN_AUD = None

FCM_SERVER_TOKEN = None
try:
    FCM_SERVER_TOKEN = os.environ['FCM_SERVER_TOKEN']
except KeyError:
    FCM_SERVER_TOKEN = None
DISCORD_WEBHOOK_URL = None
try:
    DISCORD_WEBHOOK_URL = os.environ['DISCORD_WEBHOOK_URL']
except KeyError:
    DISCORD_WEBHOOK_URL = None
