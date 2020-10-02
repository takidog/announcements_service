import falcon
import json

from auth.auth import AuthService
from utils.config import JWT_EXPIRE_TIME


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
