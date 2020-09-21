import falcon
from auth import auth_middleware
from view import api
from view import user
from view import library
from view import leave
from view import bus
from view import news
# pylint: disable=invalid-name
app = falcon.API(middleware=[auth_middleware])

# app.add_route('/oauth/token', )
app.add_route('/news/announcements', news.Announcements())
app.add_route('/news/announcements/{news_id}', news.AnnouncementsById())
app.add_route('/news/announcements/all', news.AnnouncementsAll())
# app.add_route('/news/school', news.acadNews())
app.add_route('/news/announcements/add', news.NewsAdd())
app.add_route('/news/announcements/update/{news_id}', news.NewsUpdate())
app.add_route('/news/announcements/remove/{news_id}', news.NewsRemove())
