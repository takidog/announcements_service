import falcon


class PermissionRequired(object):
    """This function is for falcon.before to use, like a decorator,
    to limit api access by permission_level.

    Args:
        req ([type]): falcon default.
        resp ([type]): falcon default.
        resource ([type]): falcon default.
        params ([type]): falcon default.
        permission_level ([int]):
                                 0: user
                                 1: editor/reviewer
                                 2: admin
    """

    def __init__(self, permission_level):
        self._permission_level = permission_level

    def __call__(self, req, resp, resource, params):
        payload = req.context['user']['user']
        if payload['permission_level'] < self._permission_level:
            raise falcon.HTTPUnauthorized(description="permission error.")
