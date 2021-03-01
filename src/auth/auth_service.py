
import datetime
import hashlib
import json
import logging
import os
import secrets

import falcon
import redis
from falcon_auth import FalconAuthMiddleware, JWTAuthBackend
from flanker.addresslib import address
from utils.config import ADMIN, JWT_EXPIRE_TIME, REDIS_URL, APPLICANT_HOSTNAME_LIMIT

from auth.apple_sign_in import verify_id_token as apple_verify_id_token
from auth.google_oauth import get_user_profile_from_id_token, google_sign_in


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
        if len(username) < 8 or len(username) > 64:
            raise falcon.HTTPUnauthorized(description="username length error")
        if len(password) < 50 or len(password) > 80:
            raise falcon.HTTPUnauthorized(description="password length error")

        if self.redis_account.exists(username):
            raise falcon.HTTPUnauthorized(description="already register")

        if self.is_banned(username):
            raise falcon.HTTPForbidden(
                title="banned", description="Your account is banned, any question please ask Facebook fan page.")

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

    def login(self, username: str, password: str, fcm_token=None) -> str:
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

            if self.is_banned(username):
                raise falcon.HTTPForbidden(
                    title="banned", description="Your account is banned, any question please ask Facebook fan page.")

            if user_data['password'] == _password:
                _user_level = 0
                if username in ADMIN:
                    _user_level = 2
                elif username in self.get_editor_list():
                    _user_level = 1

                jwt_string = self.jwt_auth.get_auth_token(user_payload={
                    "username": username,
                    "login_type": "General",
                    "permission_level": _user_level,
                    "fcm": fcm_token
                })

                return jwt_string

        raise falcon.HTTPUnauthorized()

    def get_editor_list(self) -> list:
        if self.redis_auth.exists("editor"):
            return json.loads(self.redis_auth.get('editor'))
        self.redis_auth.set(name='editor', value="[]")
        return []

    def is_banned(self, username: str) -> bool:
        """is user banned ?

        Args:
            username (str): username

        Returns:
            bool: True is banned, False is not.
        """
        banned_list = self.get_banned_list()
        try:
            banned_list.index(username)
        except ValueError:
            return False
        return True

    def get_banned_list(self) -> list:
        if self.redis_auth.exists("banned"):
            return json.loads(self.redis_auth.get('banned'))
        self.redis_auth.set(name='banned', value="[]")
        return []

    def ban_user(self, username: str) -> bool:
        banned_list = self.get_banned_list()
        banned_list.append(username)
        self.redis_auth.set(
            name='banned', value=json.dumps(list(set(banned_list))))
        return True

    def remove_banned(self, username: str) -> bool:
        banned_list = self.get_banned_list()
        try:
            banned_list.remove(username)
        except ValueError:
            return False
        self.redis_auth.set(
            name='banned', value=json.dumps(list(set(banned_list))))
        return True

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

        if self.is_banned(client_submitted_jwt.get("user", {}).get("username", "")):
            raise falcon.HTTPForbidden(
                title="banned", description="Your account is banned, any question please ask Facebook fan page.")

        return client_submitted_jwt

    def google_oauth_login(self, code: str, fcm_token=None) -> str:

        user_info_by_google = google_sign_in(code=code)

        if user_info_by_google.get("verified_email", False) == False:
            falcon.HTTPForbidden("Your email need verified.")
        user_mail = user_info_by_google.get('email', False)
        if user_mail is False:
            falcon.HTTPServiceUnavailable(
                description="Get user email error :(")
        user_mail = user_mail.lower()
        if APPLICANT_HOSTNAME_LIMIT != []:
            user_mail_parse = address.parse(user_mail, addr_spec_only=True)
            if user_mail_parse is not None:
                if isinstance(user_mail_parse, address.EmailAddress) and \
                        user_mail_parse.hostname not in APPLICANT_HOSTNAME_LIMIT:
                    raise falcon.HTTPForbidden(
                        title="mail organization not allow")

        if self.is_banned(user_mail):
            raise falcon.HTTPForbidden(
                title="banned", description="Your account is banned, any question please ask Facebook fan page.")

        _user_level = 0
        if user_mail in ADMIN:
            _user_level = 2
        elif user_mail in self.get_editor_list():
            _user_level = 1

        jwt_string = self.jwt_auth.get_auth_token(user_payload={
            "username": user_mail,
            "login_type": "Oauth2",
            "permission_level": _user_level,
            "fcm": fcm_token
        })
        return jwt_string

    def google_oauth_login_by_id_token(self, id_token: str, fcm_token=None) -> str:
        user_info_by_google = get_user_profile_from_id_token(id_token=id_token)
        if user_info_by_google.get("verified_email", False) == False:
            falcon.HTTPForbidden("Your email need verified.")
        user_mail = user_info_by_google.get('email', False)
        if user_mail is False:
            falcon.HTTPServiceUnavailable(
                description="Get user email error :(")
        user_mail = user_mail.lower()
        if APPLICANT_HOSTNAME_LIMIT != []:
            user_mail_parse = address.parse(user_mail, addr_spec_only=True)
            if user_mail_parse is not None:
                if isinstance(user_mail_parse, address.EmailAddress) and \
                        user_mail_parse.hostname not in APPLICANT_HOSTNAME_LIMIT:
                    raise falcon.HTTPForbidden(
                        title="mail organization not allow")
        if self.is_banned(user_mail):
            raise falcon.HTTPForbidden(
                title="banned", description="Your account is banned, any question please ask Facebook fan page.")

        _user_level = 0
        if user_mail in ADMIN:
            _user_level = 2
        elif user_mail in self.get_editor_list():
            _user_level = 1

        jwt_string = self.jwt_auth.get_auth_token(user_payload={
            "username": user_mail,
            "login_type": "Oauth2",
            "permission_level": _user_level,
            "fcm": fcm_token
        })
        return jwt_string

    def apple_sign_in_by_id_token(self, id_token: str, bundle_id=None, fcm_token=None) -> str:
        jwt_payload = apple_verify_id_token(
            id_token=id_token, bundle_id=bundle_id)
        if jwt_payload.get("email", False) == False:
            falcon.HTTPServiceUnavailable(
                description="Get user email error :(")

        user_mail = jwt_payload.get("email", "").lower()

        if APPLICANT_HOSTNAME_LIMIT != []:
            user_mail_parse = address.parse(user_mail, addr_spec_only=True)
            if user_mail_parse is not None:
                if isinstance(user_mail_parse, address.EmailAddress) and \
                        user_mail_parse.hostname not in APPLICANT_HOSTNAME_LIMIT:
                    raise falcon.HTTPForbidden(
                        title="mail organization not allow")
        if self.is_banned(user_mail):
            raise falcon.HTTPForbidden(
                title="banned", description="Your account is banned, any question please ask Facebook fan page.")

        _user_level = 0
        if user_mail in ADMIN:
            _user_level = 2
        elif user_mail in self.get_editor_list():
            _user_level = 1

        jwt_string = self.jwt_auth.get_auth_token(user_payload={
            "username": user_mail,
            "login_type": "Apple_sign_in",
            "permission_level": _user_level,
            "fcm": fcm_token
        })
        return jwt_string
