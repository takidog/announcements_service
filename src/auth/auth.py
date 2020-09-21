def falcon_admin_required(req, resp, resource, params):
    """This function is for falcon.before to use, like a decorator,
    check user status, for news use.
    Args:
        req ([type]): falcon default.
        resp ([type]): falcon default.
        resource ([type]): falcon default.
        params ([type]): falcon default.
    Raises:
        falcon.HTTPUnauthorized: HTTP_401, login fail,or maybe NKUST server is down.
        falcon.HTTPInternalServerError: HTTP_500, something error.
    Returns:
        [bool]: True.
    """
    # jwt payload
    payload = req.context['user']['user']

    if payload['username'] in config.NEWS_ADMIN:
        return True
    else:
        # 401
        raise falcon.HTTPUnauthorized(description='not a admin :( ')
    raise falcon.HTTPInternalServerError()
