import falcon
import json

from auth.auth_service import AuthService
from utils.config import JWT_EXPIRE_TIME
from auth.falcon_auth_decorator import PermissionRequired


class Login:

    auth = {
        'exempt_methods': ['POST']
    }

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def on_post(self, req, resp):
        "/login"
        req_json = json.loads(req.bounded_stream.read(), encoding='utf-8')
        for key in req_json.keys():
            if key not in ['username', 'password']:
                raise falcon.HTTPBadRequest(
                    description=f"{key}, key error, not in allow field.")

        # 401 error will raise in auth_service
        login_jwt = self.auth_service.login(username=req_json['username'],
                                            password=req_json['password']
                                            )
        resp.set_cookie('Authorization',
                        f'Bearer {login_jwt}', max_age=JWT_EXPIRE_TIME)
        resp.media = {
            'key': login_jwt
        }
        resp.status = falcon.HTTP_200
        return True


class Register:
    auth = {
        'exempt_methods': ['POST']
    }

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def on_post(self, req, resp):
        "/register"
        req_json = json.loads(req.bounded_stream.read(), encoding='utf-8')
        for key in req_json.keys():
            if key not in ['username', 'password']:
                raise falcon.HTTPBadRequest(
                    description=f"{key}, key error, not in allow field.")

        # 401 error will raise in auth_service
        register_status = self.auth_service.register(username=req_json['username'],
                                                     password=req_json['password']
                                                     )
        if register_status:
            # register success and login.
            login_jwt = self.auth_service.login(username=req_json['username'],
                                                password=req_json['password']
                                                )
            resp.set_cookie('Authorization',
                            f'Bearer {login_jwt}', max_age=JWT_EXPIRE_TIME)
            resp.media = {
                'key': login_jwt
            }
            resp.status = falcon.HTTP_200
            return True

        raise falcon.HTTPUnauthorized()


class Editor:
    "/auth/editor"

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    @falcon.before(PermissionRequired(permission_level=2))
    def on_get(self, req, resp):
        # get editor list
        resp.body = json.dumps(self.auth_service.get_editor_list())
        resp.media = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200
        return True

    @falcon.before(PermissionRequired(permission_level=2))
    def on_post(self, req, resp):
        req_json = json.loads(
            req.bounded_stream.read(), encoding='utf-8')
        for key in req_json.keys():
            if key not in ["username"]:
                raise falcon.HTTPBadRequest(
                    description=f"{key}, key error, not in allow field.")
        if isinstance(req_json['username'], list):
            for username in req_json['username']:
                self.auth_service.add_editor(username)
            resp.status = falcon.HTTP_200
            return True
        self.auth_service.add_editor(req_json['username'])
        return True

    @falcon.before(PermissionRequired(permission_level=2))
    def on_delete(self, req, resp):
        req_json = json.loads(
            req.bounded_stream.read(), encoding='utf-8')
        for key in req_json.keys():
            if key not in ["username"]:
                raise falcon.HTTPBadRequest(
                    description=f"{key}, key error, not in allow field.")
        if isinstance(req_json['username'], list):
            for username in req_json['username']:
                self.auth_service.remove_editor(username)
            resp.status = falcon.HTTP_200
            return True
        self.auth_service.remove_editor(req_json['username'])
        return True


class UserInfo:
    """/user/info
    Just check JWT and return payload data.
    """

    def on_get(self, req, resp):
        resp.media = req.context['user']['user']
        resp.status = falcon.HTTP_200
        return True


class GoogleOauthLogin:

    auth = {
        'exempt_methods': ['POST']
    }

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def on_post(self, req, resp):
        "/oauth2/google/login"
        req_json = json.loads(req.bounded_stream.read(), encoding='utf-8')
        for key in req_json.keys():
            if key not in ['code']:
                raise falcon.HTTPBadRequest(
                    description=f"{key}, key error, not in allow field.")

        # 401 error will raise in auth_service
        login_jwt = self.auth_service.google_oauth_login(code=req_json['code'])
        resp.set_cookie('Authorization',
                        f'Bearer {login_jwt}', max_age=JWT_EXPIRE_TIME)
        resp.media = {
            'key': login_jwt
        }
        resp.status = falcon.HTTP_200
        return True


class GoogleOauthLoginByIdToken:

    auth = {
        'exempt_methods': ['POST']
    }

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def on_post(self, req, resp):
        "/oauth2/google/token"
        req_json = json.loads(req.bounded_stream.read(), encoding='utf-8')
        for key in req_json.keys():
            if key not in ['token']:
                raise falcon.HTTPBadRequest(
                    description=f"{key}, key error, not in allow field.")

        # 401 error will raise in auth_service
        login_jwt = self.auth_service.google_oauth_login_by_id_token(
            id_token=req_json['token'])
        resp.set_cookie('Authorization',
                        f'Bearer {login_jwt}', max_age=JWT_EXPIRE_TIME)
        resp.media = {
            'key': login_jwt
        }
        resp.status = falcon.HTTP_200
        return True
