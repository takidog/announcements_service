
import datetime
import json
import logging

import falcon
import redis
from falcon_auth import FalconAuthMiddleware, JWTAuthBackend

from utils.config import REDIS_URL, JWT_EXPIRE_TIME, ADMIN
import secrets
import hashlib
import os


class AuthService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.redis_account = redis.StrictRedis.from_url(
            url=REDIS_URL, db=7, charset="utf-8", decode_responses=True)
        self.redis_auth = redis.StrictRedis.from_url(
            url=REDIS_URL, db=6, charset="utf-8", decode_responses=True)
        try:
            self._secret_key = os.environ['ANNOUNCEMENTS_SECRET_KEY']
        except KeyError:
            if self.redis_auth.exists('secret_key'):
                self._secret_key = self.redis_auth.get('secret_key')
            else:
                self.redis_auth.set('secret_key', secrets.token_hex())
                self._secret_key = self.redis_auth.get('secret_key')

        self.jwt_auth = JWTAuthBackend(self.jwt_user_loader,
                                       secret_key=self._secret_key,
                                       auth_header_prefix='Bearer',
                                       leeway=60,
                                       expiration_delta=JWT_EXPIRE_TIME)
        self.auth_middleware = FalconAuthMiddleware(self.jwt_auth)

    def register(self, username: str, password: str) -> bool:
        """Very basic user register function.

        Args:
            username (str): username.
            password (str): password, support sha-256 length.

        Raises:
            falcon.HTTPUnauthorized: username too long.
            falcon.HTTPUnauthorized: password length error. (support sha-256 length)
            falcon.HTTPUnauthorized: already register.

        Returns:
            bool: True, success register.
        """
        if len(username) < 8 and len(username) > 64:
            raise falcon.HTTPUnauthorized(description="username length error")
        if len(password) < 50 and len(password) > 80:
            raise falcon.HTTPUnauthorized(description="password length error")

        if self.redis_account.exists(username):
            raise falcon.HTTPUnauthorized(description="already register")
        s = hashlib.sha256()
        s.update(password.encode('utf-8'))
        _password = s.hexdigest()

        data = {
            'username': username,
            'password': _password
        }
        user_data = json.dumps(data)
        self.redis_account.set(name=username, value=user_data)
        return True

    def login(self, username: str, password: str) -> str:
        """basic login function

        Args:
            username (str): username
            password (str): password

        Raises:
            falcon.HTTPUnauthorized: 401, username or password error

        Returns:
            str: jwt payload.

        JWT_Payload:
            {
                username
                permission_level
            }
            permission_level:
            - 0 is user
            - 1 is editor/reviewer
            - 2 is admin
        """
        if self.redis_account.exists(username):
            user_data = json.loads(self.redis_account.get(username))
            s = hashlib.sha256()
            s.update(password.encode('utf-8'))
            _password = s.hexdigest()

            if user_data['password'] == _password:
                _user_level = 0
                if username in ADMIN:
                    _user_level = 2
                elif username in self.get_editor_list():
                    _user_level = 1

                jwt_string = self.jwt_auth.get_auth_token(user_payload={
                    "username": username,
                    "permission_level": _user_level
                })

                return jwt_string

        raise falcon.HTTPUnauthorized()

    def get_editor_list(self) -> list:
        if self.redis_auth.exists("editor"):
            return json.loads(self.redis_auth.get('editor'))
        self.redis_auth.set(name='editor', value="[]")
        return []

    def add_editor(self, username: str) -> bool:
        if not self.redis_account.exists(username):
            raise falcon.HTTPNotAcceptable(
                description="This user isn't register")
        if username in self.get_editor_list():
            raise falcon.HTTPNotAcceptable(
                description="user already is editor")
        if not self.redis_auth.exists("editor"):
            editor_list = [username]
            self.redis_auth.set(name='editor', value=json.dumps(editor_list))
            return True
        editor_list = self.get_editor_list()
        editor_list.append(username)
        self.redis_auth.set(name='editor', value=json.dumps(editor_list))
        return True

    def remove_editor(self, username: str) -> bool:
        if not self.redis_account.exists(username):
            raise falcon.HTTPNotAcceptable(
                description="This user isn't register")

        editor_list = self.get_editor_list()
        try:
            editor_list.remove(username)
        except ValueError:
            raise falcon.HTTPNotAcceptable(
                description="This user not in editor")
        self.redis_auth.set(name='editor', value=json.dumps(editor_list))
        return True

    def jwt_user_loader(self, client_submitted_jwt: dict) -> dict:
        """can make basic check in this function.

        Args:
            client_submitted_jwt ([dict]): after decode by JWT

        Returns:
            [dict]: after check raw_data
        """

        return client_submitted_jwt
