import json

import redis
from announcements.announcement import AnnouncementService
from utils.config import CACHE_EXPIRE_SEC, REDIS_URL


class CacheManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.acs = AnnouncementService()
        self.redis_cache = redis.StrictRedis.from_url(
            url=REDIS_URL, db=9, charset="utf-8", decode_responses=True)

    def _get_all_announcements_without_last_next_id(self) -> list:
        cache_key = "All_announcements_wo_id"
        if self.redis_cache.exists(cache_key):
            return json.loads(self.redis_cache.get(cache_key))
        data = self.acs._get_all_announcement()
        self.redis_cache.set(name=cache_key,
                             value=json.dumps(data),
                             ex=CACHE_EXPIRE_SEC
                             )
        return data

    def cache_get_all_announcements(self) -> str:
        cache_key = "All_announcements"
        if self.redis_cache.exists(cache_key):
            return self.redis_cache.get(cache_key)
        data = json.dumps(
            self.acs.get_all_announcement(
                raw_announcements=self._get_all_announcements_without_last_next_id()
            )
        )
        self.redis_cache.set(name=cache_key,
                             value=data,
                             ex=CACHE_EXPIRE_SEC
                             )
        return data

    def cache_get_announcement_by_tags(self, tags: list) -> str:
        sorted(tags)
        cache_key = f"tag_search_{json.dumps(tags)}"
        if self.redis_cache.exists(cache_key):
            return self.redis_cache.get(cache_key)

        data = json.dumps(
            self.acs.get_announcement_by_tags(
                tags=tags,
                announcements=self._get_all_announcements_without_last_next_id())
        )
        self.redis_cache.set(name=cache_key,
                             value=data,
                             ex=CACHE_EXPIRE_SEC)
        return data

    def cache_get_tags_count_dict(self) -> str:
        cache_key = "tag_count"
        if self.redis_cache.exists(cache_key):
            return self.redis_cache.get(cache_key)

        data = json.dumps(
            self.acs.get_tags_count_dict()
        )
        self.redis_cache.set(name=cache_key,
                             value=data,
                             ex=CACHE_EXPIRE_SEC
                             )
        return data

    def clear_cache(self):
        data = self.redis_cache.keys()
        if len(data) > 0:
            self.redis_cache.delete(*data)
