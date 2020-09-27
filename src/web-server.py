import falcon
from view import announcement
from announcements.announcement import AnnouncementService
from cache.announcements_cache import CacheManager
app = falcon.API()
acs = AnnouncementService()
cache_manager = CacheManager()
app.add_route(
    '/announcements',
    announcement.Announcements(cache_manager=cache_manager)
)
app.add_route(
    '/announcements/{announcement_id}',
    announcement.AnnouncementsById(announcement_service=acs)
)
app.add_route(
    '/announcements/add',
    announcement.AnnouncementsAdd(
        cache_manager=cache_manager,
        announcement_service=acs
    )
)
app.add_route(
    '/announcements/update/{announcement_id}',
    announcement.AnnouncementsUpdate(
        cache_manager=cache_manager,
        announcement_service=acs
    )
)
app.add_route(
    '/announcements/delete/{announcement_id}',
    announcement.AnnouncementsRemove(
        cache_manager=cache_manager,
        announcement_service=acs
    )
)
