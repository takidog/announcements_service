import os

try:
    REDIS_URL = os.environ['REDIS_URL']
except KeyError:
    REDIS_URL = 'redis://127.0.0.1:6379'

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
    "tag": {"type": list, "allow_user_set": True, "default": []}
}

MAX_TAGS_LIMIT = 20
CACHE_EXPIRE_SEC = 120
