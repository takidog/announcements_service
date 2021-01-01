
import datetime
import json
import logging

import falcon
import redis
from utils.time_tool import time_format_iso8601
from utils.tools import rand_str
from utils.config import (APPLICATION_FIELD, ANNOUNCEMENT_REQUIRED_FIELD,
                          MAX_TAGS_LIMIT, REDIS_URL, APPLICATION_EXPIRE_TIME_AFTER_APPROVE)
from announcements.announcement import AnnouncementService


class ReviewService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.redis_review_announcement = redis.StrictRedis.from_url(
            url=REDIS_URL, db=3, charset="utf-8", decode_responses=True)
        self.acs = AnnouncementService()

    def get_user_application(self, username: str) -> str:
        """Get applications by username

        Args:
            username (str): username

        Returns:
            str: json_string
        """
        username = self._clear_match_pattern(username)
        result = []
        for i in self.redis_review_announcement.scan_iter(f"application_{username}_*"):
            result.append(self.redis_review_announcement.get(i))
        json_string = f"[{','.join(result)}]"
        return json_string

    def _clear_match_pattern(self, key: str) -> str:
        for i in ['*', "?", "[", "]", "-"]:
            key = key.replace(i, "")
        return key

    def get_all_application(self) -> str:
        """Get all application.

        Returns:
            str: json string
        """
        result = []
        for i in self.redis_review_announcement.scan_iter(f"application_*"):
            result.append(self.redis_review_announcement.get(i))
        json_string = f"[{','.join(result)}]"
        return json_string

    def add_application(self, username, **kwargs) -> bool:
        """Add announcement application to redis(db:3).
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
            [str]: Success, application id.
        """

        # check required field
        compare_list = [
            True for x in kwargs.keys() if x in ANNOUNCEMENT_REQUIRED_FIELD]

        if not any(compare_list) or len(compare_list) != len(ANNOUNCEMENT_REQUIRED_FIELD):
            return False

        application_id = rand_str(16)
        application_name = f"application_{username}_{application_id}"

        application_data = {}
        for key, value in APPLICATION_FIELD.items():
            if isinstance(kwargs.get(key, None), value['type']) and value['allow_user_set']:
                application_data[key] = kwargs.get(key, None)
                continue
            if not isinstance(kwargs.get(key, None), value['type']) and value['allow_user_set']:
                if kwargs.get(key, None) is not None:
                    logging.info("Add Announcements field type error :{key}")
                application_data[key] = value['default']

        application_data['publishedAt'] = datetime.datetime.utcnow(
        ).isoformat(timespec="seconds")+"Z"
        application_data['application_id'] = application_id
        application_data['applicant'] = username
        application_data['reviewStatus'] = None
        application_data['reviewDescription'] = None

        if kwargs.get('expireTime', False):
            application_data["expireTime"] = time_format_iso8601(kwargs.get(
                'expireTime', False)).isoformat(timespec="seconds")+"Z"

        if kwargs.get('tag', False):
            kwargs['tag'] = list(set(kwargs['tag']))
            if len(kwargs['tag']) > MAX_TAGS_LIMIT:
                application_data['tag'] = kwargs['tag'][:MAX_TAGS_LIMIT]
            else:
                application_data['tag'] = kwargs['tag']
        data_dumps = json.dumps(application_data, ensure_ascii=False)

        self.redis_review_announcement.set(name=application_name,
                                           value=data_dumps)
        return application_id

    def get_application_by_id(self, application_id: str) -> str:
        result = None
        application_id = self._clear_match_pattern(application_id)
        for i in self.redis_review_announcement.scan_iter(f"application_*_{application_id}"):
            result = self.redis_review_announcement.get(i)
        return result

    def get_application_key_name_by_id(self, application_id: str) -> str:
        result = None
        application_id = self._clear_match_pattern(application_id)
        for i in self.redis_review_announcement.scan_iter(f"application_*_{application_id}"):
            return i
        return result

    def update_application(self, application_id: str, **kwargs) -> dict:
        """Update application.
        Args:
            application_id ([int]): application id.
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
        if application_id == None:
            raise falcon.HTTPMissingParam("application_id")
        if self.get_application_by_id(application_id=application_id) is None:
            raise falcon.HTTPNotFound()
        origin_application = json.loads(
            self.get_application_by_id(application_id=application_id))

        application_data = {}
        for key, value in APPLICATION_FIELD.items():
            if isinstance(kwargs.get(key, None), value['type']) and value['allow_user_set']:
                application_data[key] = kwargs.get(key, None)
                continue
            if not isinstance(kwargs.get(key, None), value['type']) and value['allow_user_set']:
                if kwargs.get(key, None) is not None:
                    logging.info("Add application field type error :{key}")
                application_data[key] = origin_application.get(
                    key, value['default'])

        application_data['publishedAt'] = datetime.datetime.utcnow(
        ).isoformat(timespec="seconds")+"Z"
        application_data['application_id'] = origin_application.get(
            'application_id')
        application_data['applicant'] = origin_application.get('applicant')
        if kwargs.get('tag', False):
            kwargs['tag'] = list(set(kwargs['tag']))
            if len(kwargs['tag']) > MAX_TAGS_LIMIT:
                application_data['tag'] = kwargs['tag'][:MAX_TAGS_LIMIT]
            else:
                application_data['tag'] = kwargs['tag']

        if kwargs.get('expireTime', False):
            application_data["expireTime"] = time_format_iso8601(kwargs.get(
                'expireTime', False)).isoformat(timespec="seconds")+"Z"

        application_data['reviewStatus'] = None
        application_data['reviewDescription'] = "Application already updated, need review."

        data_dumps = json.dumps(application_data, ensure_ascii=False)

        self.redis_review_announcement.set(name=self.get_application_key_name_by_id(application_id),
                                           value=data_dumps)
        return True

    def delete_application(self, application_id: str) -> bool:
        if application_id is None:
            raise falcon.HTTPMissingParam("application id")

        key_name = self.get_application_key_name_by_id(application_id)
        if key_name is None:
            raise falcon.HTTPNotFound()
        self.redis_review_announcement.delete(key_name)
        return True

    def approve_application(self, application_id: str, review_description=None) -> bool:
        """approve_application

        Args:
            application_id (str): [description]

        Returns:
            bool: False
            int: Success, return announcement id.
        """
        application_data = self.get_application_by_id(application_id)
        if application_data is None:
            return False
        data = json.loads(application_data)
        origin_data = dict(data)  # copy object

        if data['reviewStatus'] is True:
            # Application is already approved. can't duplicate approve.
            return False

        if data.get('applicant'):
            del data['applicant']
        del data['reviewStatus']
        del data['reviewDescription']
        del data['application_id']
        add_status = self.acs.add_announcement(**data)
        if isinstance(add_status, bool):
            return False
        # approve status
        origin_data['reviewStatus'] = True
        # clear review message
        origin_data['reviewDescription'] = review_description
        self.redis_review_announcement.set(
            name=self.get_application_key_name_by_id(
                application_id=application_id),
            value=json.dumps(origin_data),
            ex=APPLICATION_EXPIRE_TIME_AFTER_APPROVE
        )

        return add_status

    def reject_application(self, application_id: str, review_description: str) -> bool:
        """reject_application

        Args:
            application_id (str): [description]
            review_description (str): [description]
        Returns:
            bool: True (Update reject success)
            bool: False (Not found application)
        """
        application_data = self.get_application_by_id(application_id)
        if application_data is None:
            return False
        data = json.loads(application_data)

        if data['reviewStatus'] is True:
            # This application is approved, can't reject.
            return False
        # Reject status.
        data['reviewStatus'] = False
        data['reviewDescription'] = review_description

        self.redis_review_announcement.set(
            name=self.get_application_key_name_by_id(
                application_id=application_id),
            value=json.dumps(data)
        )

        return True
