
import datetime
import json
import logging

import falcon
import redis
from utils.time_tool import time_format_iso8601
from utils.config import (ANNOUNCEMENT_FIELD, ANNOUNCEMENT_REQUIRED_FIELD,
                          MAX_TAGS_LIMIT, REDIS_URL)


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
        if len(announcement_data) == 0:
            return []
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

    def get_announcement_by_id(self, announcement_id) -> str:
        announcement_name = f"announcement_{announcement_id}"
        if self.redis_announcement.exists(announcement_name):
            return self.redis_announcement.get(announcement_name)
        raise falcon.HTTPNotFound()

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
            utc = time_format_iso8601(kwargs.get('expireTime', False))
            expire_time_seconds = int(
                (utc-datetime.datetime.utcnow()).total_seconds())
            if expire_time_seconds < 0:
                raise falcon.HTTPBadRequest(
                    description="expeire time set error")
            else:
                announcement_data["expireTime"] = time_format_iso8601(kwargs.get(
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
        
        if not self.redis_announcement.exists(f"announcement_{announcement_id}"):
            raise falcon.HTTPNotFound()
        announcement_name = f"announcement_{announcement_id}"

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
        announcement_data['id'] = origin_announcement.get('id')
        if kwargs.get('tag', False):
            kwargs['tag'] = list(set(kwargs['tag']))
            if len(kwargs['tag']) > MAX_TAGS_LIMIT:
                announcement_data['tag'] = kwargs['tag'][:MAX_TAGS_LIMIT]
            else:
                announcement_data['tag'] = kwargs['tag']
        expire_time_seconds = None
        if kwargs.get('expireTime', False):
            utc = time_format_iso8601(kwargs.get('expireTime', False))
            expire_time_seconds = int(
                (utc-datetime.datetime.utcnow()).total_seconds())
            if expire_time_seconds < 0:
                raise falcon.HTTPBadRequest(
                    description="expeire time set error")
            else:
                announcement_data["expireTime"] = time_format_iso8601(kwargs.get(
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

        if not self.redis_announcement.exists(f"announcement_{announcement_id}"):
            raise falcon.HTTPNotFound()
        announcement_name = f"announcement_{announcement_id}"

        self.redis_announcement.delete(announcement_name)

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
            match=f"announcement_{announcement_id}")[1]
        if len(announcement_name_search) < 1 and raise_error:
            raise falcon.HTTPNotFound()
        if len(announcement_name_search) > 1:
            logging.warning(
                msg="Announcement conflict, have same id on database")
            if raise_error:
                raise falcon.HTTPServiceUnavailable(
                    title="announcement have same id conflict")

        return announcement_name_search

    def get_tags_count_dict(self, announcements=None) -> dict:
        """Get all announcements tag count.

        Args:
            announcements ([type], optional): count by cache. Defaults to None.

        Returns:
            dict: count dict.
        """
        if announcements is None:
            announcements = self._get_all_announcement()
        result = {}
        for announcement in announcements:
            for tag in announcement['tag']:
                if not result.get(tag, False):
                    result[tag] = 1
                    continue
                result[tag] += 1
        return result

    def get_announcement_by_tags(self, tags=None, announcements=None) -> list:
        """search by tag.

        Args:
            tags (list, optional): [description]. Defaults to [].
            announcements ([type], optional): search by cache. Defaults to None.

        Returns:
            list: announcement list.
        """
        if announcements is None:
            announcements = self._get_all_announcement()
        if tags is None or not isinstance(tags, list):
            return announcements
        tags = list(set(tags))
        result = []
        if len(tags) == 1:
            for announcement in announcements:
                if tags[0] in announcement['tag']:
                    result.append(announcement)
            return self._mix_index_id(result)
        for announcement in announcements:
            if not any([None if x in announcement['tag'] else True for x in tags]):
                result.append(announcement)
        return self._mix_index_id(result)
