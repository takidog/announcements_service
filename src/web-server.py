import falcon

from announcements.announcement import AnnouncementService
from announcements.review import ReviewService
from auth.auth import AuthService
from cache.announcements_cache import CacheManager
from view import announcement_view, application_view, auth_view

app = falcon.API()
auth_service = AuthService()
acs = AnnouncementService()
cache_manager = CacheManager()
review_service = ReviewService()

app = falcon.API(middleware=[auth_service.auth_middleware])

app.add_route(
    '/announcements',
    announcement_view.Announcements(cache_manager=cache_manager)
)
app.add_route(
    '/announcements/{announcement_id}',
    announcement_view.AnnouncementsById(announcement_service=acs)
)
app.add_route(
    '/announcements/tags',
    announcement_view.AnnouncementsTagCount(cache_manager=cache_manager)
)
app.add_route(
    '/announcements/add',
    announcement_view.AnnouncementsAdd(
        cache_manager=cache_manager,
        announcement_service=acs
    )
)
app.add_route(
    '/announcements/update/{announcement_id}',
    announcement_view.AnnouncementsUpdate(
        cache_manager=cache_manager,
        announcement_service=acs
    )
)
app.add_route(
    '/announcements/delete/{announcement_id}',
    announcement_view.AnnouncementsRemove(
        cache_manager=cache_manager,
        announcement_service=acs
    )
)
app.add_route(
    '/login',
    auth_view.Login(auth_service=auth_service)
)
app.add_route(
    '/register',
    auth_view.Register(auth_service=auth_service)
)
app.add_route(
    '/auth/editor',
    auth_view.Editor(auth_service=auth_service)
)
app.add_route(
    '/application',
    application_view.GetApplication(
        review_service=review_service
    )
)
app.add_route(
    '/user/application/{username}',
    application_view.GetApplicationByUsername(
        review_service=review_service
    )
)
app.add_route(
    '/application/{application_id}',
    application_view.ApplicationById(
        review_service=review_service
    )
)
