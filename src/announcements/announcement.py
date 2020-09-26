
import datetime
import json

import falcon
import redis

from utils import time_tool
from utils.config import REDIS_URL
from utils.config import ANNOUNCEMENT_REQUIRED_FIELD
from utils.config import ANNOUNCEMENT_FIELD
from utils.config import MAX_TAGS_LIMIT
import logging


class AnnouncementService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.redis_announcement = redis.StrictRedis.from_url(
            url=REDIS_URL, db=8, charset="utf-8", decode_responses=True)

    def _mix_index_id(self, announcement_data: list) -> list:
        """Mix next id and last id into announcement.
        
        Args:
            announcement_data ([list]): announcements after sort.
        Returns:
            [dict]: news data
            [None]: not found announcement.
        """
        if len(announcement_data) == 1:
            announcement_data[0]['nextId'] = None
            announcement_data[0]['lastId'] = None
            return announcement_data
        announcement_data[0]['lastId'] = None
        announcement_data[0]['nextId'] = announcement_data[1]['id']
        for index in range(1, len(announcement_data)-1):
            announcement_data[index]['nextId'] = announcement_data[index+1]['id']
            announcement_data[index]['lastId'] = announcement_data[index-1]['id']
        announcement_data[len(announcement_data)-1]['lastId'] = announcement_data[len(
            announcement_data)-1]['id']
        announcement_data[len(announcement_data)-1]['nextId'] = None

        return announcement_data

    def _get_all_announcement(self) -> list:
        # private
        announcement = sorted([json.loads(self.redis_announcement.get(i))
                               for i in self.redis_announcement.scan_iter()], key=lambda k: k['id'])
        return announcement

    def get_all_announcement(self, raw_announcements=None) -> list:
        # public
        if raw_announcements is None:
            raw_announcements = self._get_all_announcement()

        return self._mix_index_id(raw_announcements)

    def add_announcement(self, **kwargs) -> bool:
        """Add announcement to redis.
        set required field list on config.py
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

        # check required field
        compare_list = [
            True for x in kwargs.keys() if x in ANNOUNCEMENT_REQUIRED_FIELD]

        if not any(compare_list) or len(compare_list) != len(ANNOUNCEMENT_REQUIRED_FIELD):
            return False

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
        announcement_name = f"announcement_{announcement_id}"

        announcement_data = {}
        for key, value in ANNOUNCEMENT_FIELD.items():
            if isinstance(kwargs.get(key, None), value['type']) and value['allow_user_set']:
                announcement_data[key] = kwargs.get(key, None)
                continue
            if not isinstance(kwargs.get(key, None), value['type']) and value['allow_user_set']:
                if kwargs.get(key, None) is not None:
                    logging.info("Add Announcements field type error :{key}")
                announcement_data[key] = value['default']

        announcement_data['publishedAt'] = datetime.datetime.utcnow(
        ).isoformat(timespec="seconds")+"Z"
        announcement_data['id'] = announcement_id

        expire_time_seconds = None
        if kwargs.get('expireTime', False):
            utc = time_tool.time_format(kwargs.get('expireTime', False))
            expire_time_seconds = int(
                (utc-datetime.datetime.utcnow()).total_seconds())
            if expire_time_seconds < 0:
                expire_time_seconds = None
            else:
                announcement_data["expireTime"] = time_tool.time_format(kwargs.get(
                    'expireTime', False)).isoformat(timespec="seconds")+"Z"

        if kwargs.get('tag', False):
            kwargs['tag'] = list(set(kwargs['tag']))
            if len(kwargs['tag']) > MAX_TAGS_LIMIT:
                announcement_data['tag'] = kwargs['tag'][:MAX_TAGS_LIMIT]
            else:
                announcement_data['tag'] = kwargs['tag']
        data_dumps = json.dumps(announcement_data, ensure_ascii=False)

        self.redis_announcement.set(name=announcement_name,
                                    value=data_dumps, ex=expire_time_seconds)
        return announcement_id

    def update_announcement(self, announcement_id: int, **kwargs) -> bool:
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
        try:
            announcement_name = self._get_announcement_key_name_by_id(
                announcement_id)[0]
        except IndexError:
            raise falcon.HTTPNotFound()

        origin_announcement = json.loads(
            self.redis_announcement.get(announcement_name))

        announcement_data = {}
        for key, value in ANNOUNCEMENT_FIELD.items():
            if isinstance(kwargs.get(key, None), value['type']) and value['allow_user_set']:
                announcement_data[key] = kwargs.get(key, None)
                continue
            if not isinstance(kwargs.get(key, None), value['type']) and value['allow_user_set']:
                if kwargs.get(key, None) is not None:
                    logging.info("Add Announcements field type error :{key}")
                announcement_data[key] = origin_announcement.get(
                    key, value['default'])

        announcement_data['publishedAt'] = datetime.datetime.utcnow(
        ).isoformat(timespec="seconds")+"Z"
        announcement_data['id'] = announcement_id
        if kwargs.get('tag', False):
            kwargs['tag'] = list(set(kwargs['tag']))
            if len(kwargs['tag']) > MAX_TAGS_LIMIT:
                announcement_data['tag'] = kwargs['tag'][:MAX_TAGS_LIMIT]
            else:
                announcement_data['tag'] = kwargs['tag']
        expire_time_seconds = None
        if kwargs.get('expireTime', False):
            utc = time_tool.time_format(kwargs.get('expireTime', False))
            expire_time_seconds = int(
                (utc-datetime.datetime.utcnow()).total_seconds())
            if expire_time_seconds < 0:
                expire_time_seconds = None
            else:
                announcement_data["expireTime"] = time_tool.time_format(kwargs.get(
                    'expireTime', False)).isoformat(timespec="seconds")+"Z"

        data_dumps = json.dumps(announcement_data, ensure_ascii=False)

        self.redis_announcement.set(name=announcement_name,
                                    value=data_dumps, ex=expire_time_seconds)
        return True

    def delete_announcement(self, announcement_id: int, force_delete=False) -> bool:
        """delete announcement.
        Args:
            announcement_id ([int]): announcement id.
        Returns:
            [bool]: True
        """
        if announcement_id is None:
            raise falcon.HTTPMissingParam("announcement id")
        try:
            announcement_name_search = self._get_announcement_key_name_by_id(
                announcement_id, raise_error=not force_delete)
        except falcon.HTTPServiceUnavailable as e:
            falcon.falcon.HTTPServiceUnavailable(
                title=e.title, description="Add force delete to dismiss this error, and delete same id announcements.")

        for name in announcement_name_search:
            self.redis_announcement.delete(name)

        return True

    def _get_announcement_key_name_by_id(self, announcement_id: int, raise_error=False) -> list:
        """Get announcement key name from redis.

        Args:
            announcement_id (int): announcement id.
            raise_same_id_conflict (bool, optional): raise error by falcon. Defaults to False.

        Raises:
            falcon.HTTPNotFound: Not found announcement by id.
            falcon.HTTPServiceUnavailable: Found same id on database.

        Returns:
            list: key name list
        """
        announcement_name_search = self.redis_announcement.scan(
            match=f"announcement_{announcement_id}_*")[1]
        if len(announcement_name_search) < 1 and raise_error:
            raise falcon.HTTPNotFound()
        if len(announcement_name_search) > 1:
            logging.warning(
                msg="Announcement conflict, have same id on database")
            if raise_error:
                raise falcon.HTTPServiceUnavailable(
                    title="announcement have same id conflict")

        return announcement_name_search
