import falcon
from view import announcement_view
from view import auth
from announcements.announcement import AnnouncementService
from cache.announcements_cache import CacheManager
from auth.auth import AuthService
app = falcon.API()
auth_service = AuthService()
acs = AnnouncementService()
cache_manager = CacheManager()
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
