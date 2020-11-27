import falcon
import json

from utils.config import ANNOUNCEMENT_FIELD, ALLOW_APPLICATION_OWNER_MODIFY
from utils.config import LANGUAGE_TAG
from auth.falcon_auth_decorator import PermissionRequired
from announcements.review import ReviewService


def only_owner_modify(
        review_service: ReviewService,
        application_id: str,
        applicant_username: str):

    origin_application = review_service.get_application_by_id(
        application_id=application_id
    )
    if origin_application is None:
        raise falcon.HTTPNotFound()

    if json.loads(origin_application)['applicant'] != applicant_username:
        raise falcon.HTTPForbidden(title="no permission to update")


class GetApplication:

    def __init__(self, review_service: ReviewService):
        self.review_service = review_service

    @falcon.before(PermissionRequired(permission_level=1))
    def on_get(self, req, resp):
        '/application'
        resp.body = self.review_service.get_all_application()
        resp.media = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200
        return True

    def on_post(self, req, resp):
        # submit application for review.
        '/application'
        jwt_payload = req.context['user']['user']

        req_json = json.loads(req.bounded_stream.read(), encoding='utf-8')
        for key in req_json.keys():
            if key not in ANNOUNCEMENT_FIELD.keys():
                raise falcon.HTTPBadRequest(
                    description=f"{key}, key error, not in allow field.")
        reslut = self.review_service.add_application(
            username=jwt_payload['username'], **req_json)
        if isinstance(reslut, bool):
            raise falcon.HTTPBadRequest(
                description="Maybe request data not allow.")

        resp.media = {
            'application_id': reslut
        }
        resp.status = falcon.HTTP_200
        return True


class GetApplicationByUsername:

    def __init__(self, review_service: ReviewService):
        self.review_service = review_service

    def on_get(self, req, resp, username: str):
        '/user/application/{username}'
        # If account have permission, can review all username.
        jwt_payload = req.context['user']['user']
        if jwt_payload['username'] != username and jwt_payload['permission_level'] < 1:
            raise falcon.HTTPForbidden(description=":)")

        resp.body = self.review_service.get_user_application(
            username=username)
        resp.media = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200
        return True


class ApplicationById:
    def __init__(self, review_service: ReviewService):
        self.review_service = review_service

    def on_put(self, req, resp, application_id: str):
        '/application/{application_id}'
        'Update application info, not approve method.'

        jwt_payload = req.context['user']['user']
        if ALLOW_APPLICATION_OWNER_MODIFY:
            # If not owner or admin will raise falcon Error.
            only_owner_modify(
                review_service=self.review_service,
                application_id=application_id,
                applicant_username=jwt_payload['username']
            )

        req_json = json.loads(req.bounded_stream.read(), encoding='utf-8')
        for key in req_json.keys():
            if key not in ANNOUNCEMENT_FIELD.keys():
                raise falcon.HTTPBadRequest(
                    description=f"{key}, key error, not in allow field.")
        reslut = self.review_service.update_application(
            application_id=application_id, **req_json)
        if not isinstance(reslut, bool):
            raise falcon.HTTPBadRequest(
                description="Maybe request data not allow.")

        resp.media = {
            'application_id': application_id
        }
        resp.status = falcon.HTTP_200
        return True

    def on_delete(self, req, resp, application_id: str):
        '/application/{application_id}'
        'delete application by application_id'

        jwt_payload = req.context['user']['user']
        if ALLOW_APPLICATION_OWNER_MODIFY:
            only_owner_modify(
                review_service=self.review_service,
                application_id=application_id,
                applicant_username=jwt_payload['username']
            )

        delete_status = self.review_service.delete_application(application_id)

        if delete_status is False:
            falcon.HTTPNotFound()

        resp.status = falcon.HTTP_200
        return True


class ApplicationAction:
    def __init__(self, review_service: ReviewService):
        self.review_service = review_service

    @falcon.before(PermissionRequired(permission_level=1))
    def on_put(self, req, resp, application_id: str, action: str):

        if action == "approve":
            '/application/{application_id}/approve'
            'approve application by application_id'
            approve_status = self.review_service.approve_application(
                application_id)
            if approve_status is False:
                # Not found application
                raise falcon.HTTPNotFound()
            if isinstance(approve_status, int):
                resp.media = {
                    'id': approve_status
                }
                resp.status = falcon.HTTP_200
                return True
        elif action == "reject":
            '/application/{application_id}/reject'
            'reject application by application_id'

            req_json = json.loads(req.bounded_stream.read(), encoding='utf-8')

            reject_status = self.review_service.reject_application(
                application_id=application_id,
                review_description=req_json.get("description", None)
            )
            if reject_status is False:
                # Not found application
                raise falcon.HTTPNotFound()

            if reject_status:
                return True

        raise falcon.HTTPInternalServerError()
