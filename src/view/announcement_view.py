import falcon
import json

from utils.config import ANNOUNCEMENT_FIELD
from utils.config import LANGUAGE_TAG
from auth.falcon_auth_decorator import PermissionRequired


class Announcements:

    auth = {
        'exempt_methods': ['GET']
    }

    def __init__(self, cache_manager):
        self.cache_manager = cache_manager

    def on_get(self, req, resp):
        '/announcements'
        # tag query
        if req.params.get("tag", False) or req.params.get('lang', False):
            query_tags = []

            if req.params.get("tag", False):
                query_tags.extend(req.params.get("tag", "").split(','))

            for lang, value in LANGUAGE_TAG.items():
                if req.params.get('lang', "") in value:
                    query_tags.append(lang)
            resp.body = self.cache_manager.cache_get_announcement_by_tags(
                tags=query_tags)
            resp.media = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
            return True
        # normal query
        resp.body = self.cache_manager.cache_get_all_announcements()
        resp.media = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200
        return True

    def on_post(self, req, resp):
        # only tag query use POST.
        req_json = json.loads(req.bounded_stream.read(), encoding='utf-8')
        for key in req_json.keys():
            if key not in ['tag', 'lang']:
                raise falcon.HTTPBadRequest(
                    description=f"{key}, key error, not in allow field.")

        query_tags = []
        query_tags.extend(req_json.get('tag', []))
        query_tags.append(req_json.get('lang', "zh"))
        resp.body = self.cache_manager.cache_get_announcement_by_tags(
            tags=query_tags)
        resp.media = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200
        return True


class AnnouncementsById:

    auth = {
        'exempt_methods': ['GET']
    }

    def __init__(self, announcement_service):
        self.acs = announcement_service

    def on_get(self, req, resp, announcement_id):
        '/announcements/{announcement_id}'
        try:
            announcement_id = int(announcement_id)
        except:
            raise falcon.HTTPBadRequest(
                description="announcement_id must be int.")

        resp.body = self.acs.get_announcement_by_id(announcement_id)
        resp.media = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200
        return True


class AnnouncementsAdd:

    def __init__(self, cache_manager, announcement_service):
        self.cache_manager = cache_manager
        self.acs = announcement_service

    @falcon.before(PermissionRequired(permission_level=1))
    def on_post(self, req, resp):

        req_json = json.loads(req.bounded_stream.read(), encoding='utf-8')
        for key in req_json.keys():
            if key not in ANNOUNCEMENT_FIELD.keys():
                raise falcon.HTTPBadRequest(
                    description=f"{key}, key error, not in allow field.")

        result = self.acs.add_announcement(**req_json)
        if isinstance(result, int):
            resp.media = {
                'id': result
            }
            self.cache_manager.clear_cache()
            resp.status = falcon.HTTP_200
            return True
        elif result is False:
            raise falcon.HTTPBadRequest()
        raise falcon.HTTPInternalServerError()


class AnnouncementsUpdate:

    def __init__(self, cache_manager, announcement_service):
        self.cache_manager = cache_manager
        self.acs = announcement_service

    @falcon.before(PermissionRequired(permission_level=1))
    def on_put(self, req, resp, announcement_id):

        req_json = json.loads(req.bounded_stream.read(), encoding='utf-8')
        for key in req_json.keys():
            if key not in ANNOUNCEMENT_FIELD.keys():
                raise falcon.HTTPBadRequest(
                    description=f"{key}, key error, not in allow field.")

        result = self.acs.update_announcement(announcement_id=announcement_id,
                                              **req_json)
        if result is True:
            resp.media = {
                'id': announcement_id
            }
            self.cache_manager.clear_cache()
            resp.status = falcon.HTTP_200
            return True
        elif result is False:
            raise falcon.HTTPBadRequest()
        raise falcon.HTTPInternalServerError()


class AnnouncementsRemove:

    def __init__(self, cache_manager, announcement_service):
        self.cache_manager = cache_manager
        self.acs = announcement_service

    @falcon.before(PermissionRequired(permission_level=1))
    def on_delete(self, req, resp, announcement_id):
        result = self.acs.delete_announcement(announcement_id)
        if result is True:
            resp.media = {
                "id": announcement_id,
                "message": f"Remove success,id {announcement_id}."
            }
            self.cache_manager.clear_cache()
            resp.status = falcon.HTTP_200
            return True

        raise falcon.HTTPInternalServerError()


class AnnouncementsTagCount:
    auth = {
        'exempt_methods': ['GET']
    }

    def __init__(self, cache_manager):
        self.cache_manager = cache_manager

    def on_get(self, req, resp):
        '/announcements/tags'

        resp.body = self.cache_manager.cache_get_tags_count_dict()
        resp.media = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200
        return True
