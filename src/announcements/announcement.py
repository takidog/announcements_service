
import datetime
import json

import falcon
import redis

from utils.time_tool import time_format
from utils.config import REDIS_URL


class Announcements_service:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.redis_announcement = redis.StrictRedis.from_url(
            url=REDIS_URL, db=8, charset="utf-8", decode_responses=True)

    def _mix_index_id(self, announcement_id: int):
        """Mix next id and last id into announcement.

        Args:
            announcement_id ([int]): announcement id
        Returns:
            [dict]: news data
            [None]: not found announcement.
        """

        announcements = self._get_all_announcement()
        if len(announcements) < 1:
            return None
        temp_announcements_index = -1
        announcement_next = {}
        announcement_last = {}

        for index, value in enumerate(announcements):
            if value['id'] == announcement_id:
                temp_announcements_index = index
                try:
                    announcement_next = announcements[index+1]
                except IndexError:
                    announcement_next = {}
                try:
                    announcement_last = announcements[index-1]
                    if index-1 < 0:
                        announcement_last = {}
                except IndexError:
                    announcement_last = {}

        if temp_announcements_index < 0:
            # not found announcement
            return None

        # mix announcement next id and announcement last id to dict
        announcements[temp_announcements_index]['nextId'] = announcement_next.get(
            'id', None)
        announcements[temp_announcements_index]['lastId'] = announcement_last.get(
            'id', None)

        return announcements[temp_announcements_index]

    def _get_all_announcement(self):
        # TODO Add cache on here.
        # private
        announcement = sorted([json.loads(self.redis_announcement.get(i))
                               for i in self.redis_announcement.scan_iter()], key=lambda k: k['id'])
        return announcement

    def get_all_announcement(self):
        # public
        return [self._mix_index_id(announcement_id=i['id']) for i in self._get_all_announcement()]

    def add_announcement(self, **kwargs):
        """Add announcement to redis.
        Kwargs:
            title   [str]:     Required.
            imgUrl [str]:     Optional.
            url     [str]:     Link, optional.
            weight  [int]:     announcement weight,optional.
            description [str]: Optional.
            expireTime  [str]: ISO 8601, must have timezone at last character.
                2019-09-2T11:33:29H
                2019-09-2T11:33:29Z
                2019-09-2T11:33:29A
                ...
        Returns:
            [bool]: False
            [int]: Success, return announcement id.
        """
        title = kwargs.get('title', False)
        if not title:
            return False

        announcement_name = "announcement_{announcement_id}_{tag}"
        announcement_list = [i for i in self.redis_announcement.scan_iter()]
        announcement_id = 0
        announcement_list.sort(key=lambda x: int(x.split("_")[1]))

        # need null data to create new id
        announcement_list.append("announcement_0_null")
        for id_, key_name in zip(range(len(announcement_list)+1), announcement_list):
            id_from_key_name = key_name.split('_')[1]
            if id_ != int(id_from_key_name):
                announcement_id = id_
                break

        announcement_data = {
            "title": title,
            "id": announcement_id,
            "publishedAt": datetime.datetime.utcnow().isoformat(timespec="seconds")+"Z",
            "weight": int(kwargs.get('weight', 0)),
            "imgUrl": kwargs.get('imgUrl', None),
            "url": kwargs.get('url', None),
            "description": kwargs.get('description', None),
            'tag': kwargs.get('tag', [])
        }
        if kwargs.get('location', False):
            location = kwargs.get('location', {})
            if isinstance(location.get('title', False), str) and \
                    isinstance(location.get('lat', False), int) and \
                    isinstance(location.get('lng', False), int):
                announcement_data['location'] = {
                    'title': location.get('title', None),
                    'lng': location.get('lng', None),
                    'lat': location.get('lat', None)
                }
        expire_time_seconds = kwargs.get('expireTime', None)
        if kwargs.get('expireTime', False):
            utc = time_format(kwargs.get('expireTime', False))
            expire_time_seconds = (utc-datetime.datetime.utcnow()).seconds
        data_dumps = json.dumps(announcement_data, ensure_ascii=False)

        self.redis_announcement.set(name=announcement_name.format(announcement_id=announcement_id,
                                                                  tag=json.dumps(kwargs.get('tag', []))),
                                    value=data_dumps, ex=expire_time_seconds)
        return announcement_id

    def update_announcement(self, announcement_id: int, **kwargs):
        """Update announcement.
        Args:
            announcement_id ([int]): announcement id.
        Kwargs:
            title   [str]:     Optional.
            img_url [str]:     Optional.
            url     [str]:     URL, optional.
            weight  [int]:     announcement weight,optional.
            description [str]: Optional.
            expireTime  [str]: ISO 8601, must have timezone at last character.
                2019-09-2T11:33:29H
                2019-09-2T11:33:29Z
                2019-09-2T11:33:29A
                ...
        Returns:
            [bool]: True
        Raise:
            400:miss param.
            404:not found announcement.
        """
        if announcement_id == None:
            raise falcon.HTTPMissingParam("announcement_id")

        announcement_name = f"announcement_{announcement_id}"
        if not self.redis_announcement.exists(announcement_name):
            raise falcon.HTTPNotFound(description="Not found announcement id.")

        origin_announcement = json.loads(
            self.redis_announcement.get(announcement_name))

        announcement_data = {
            "title": kwargs.get('title', origin_announcement.get('title', "")),
            "id": int(announcement_id),
            "publishedAt": datetime.datetime.utcnow().isoformat(timespec="seconds")+"Z",
            "weight": int(kwargs.get('weight', int(origin_announcement.get('weight', 0)))),
            "imgUrl": kwargs.get('img_url', origin_announcement.get('imgUrl', None)),
            "url": kwargs.get('url', origin_announcement.get('url', None)),
            "description": kwargs.get('description', origin_announcement.get('description', None))
        }
        expire_time_seconds = kwargs.get(
            'expireTime', origin_announcement.get('expireTime', None))
        if kwargs.get('expireTime', origin_announcement.get('expireTime', False)):
            utc = time_format(kwargs.get(
                'expireTime', origin_announcement.get('expireTime', False)))
            expire_time_seconds = (utc-datetime.datetime.utcnow()).seconds
        data_dumps = json.dumps(announcement_data, ensure_ascii=False)

        self.redis_announcement.set(name=announcement_name,
                                    value=data_dumps, ex=expire_time_seconds)
        return True

    def remove_announcement(self, announcement_id: int):
        """remove announcement.
        Args:
            announcement_id ([int]): announcement id.
        Returns:
            [bool]: True
        """
        if announcement_id is None:
            raise falcon.HTTPMissingParam("announcement id")

        announcement_name = "announcement_{announcement_id}".format(
            announcement_id=announcement_id)
        if not self.redis_announcement.exists(announcement_name):
            raise falcon.HTTPNotFound()

        self.redis_announcement.delete(announcement_name)
        return True


def get_all_by_tag(tag_list):
    # TODO Tag function need change better search method.
    # About key name length.
    # https://stackoverflow.com/questions/6320739/does-name-length-impact-performance-in-redis

    news_list = [i for i in red_news.scan_iter()]
    news_list.sort(key=lambda x: int(x.split("_")[1]))
    temp_news_key_name = []
    for news_key_name in news_list:
        tags = json.loads(
            news_key_name[news_key_name.index("_", 5)+1:], encoding='utf-8')
        for news_tag in tags:
            if news_tag in tag_list:
                temp_news_key_name.append(news_key_name)
                break

    news_data = sorted([json.loads(red_news.get(i))
                        for i in temp_news_key_name], key=lambda k: k['id'])

    for index, value in enumerate(news_data):
        try:
            value['nextId'] = news_data[index+1]['id']
        except:
            value['nextId'] = None
        try:
            if index-1 != -1:
                value['lastId'] = news_data[index-1]['id']
            else:
                value['lastId'] = None
        except:
            value['lastId'] = None
    return news_data
