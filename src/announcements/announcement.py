
import datetime
import json

import falcon
import redis

from utils.time_tool import time_format
from utils.config import REDIS_URL

red_news = redis.StrictRedis.from_url(
    url=REDIS_URL, db=8, charset="utf-8", decode_responses=True)


def get_news(news_id, all_news=None):
    """get a news.
    Args:
        all_news ([list]): must be sorted, get this data from _get_all_news.
        news_id ([int]): news id
    Returns:
        [dict]: news data
        [bool]: False
        [None]: not found news.
    """
    if not all_news:
        all_news = _get_all_news()
    if len(all_news) < 1:
        return None
    temp_news_index = -1
    news_next = {}
    news_last = {}

    for index, value in enumerate(all_news):
        if value['id'] == news_id:
            temp_news_index = index
            try:
                news_next = all_news[index+1]
            except:
                news_next = {}
            try:
                news_last = all_news[index-1]
                if index-1 < 0:
                    news_last = {}
            except:
                news_last = {}

    if temp_news_index < 0:
        # not found news
        return None

    # mix news next id and news last id to dict
    all_news[temp_news_index]['nextId'] = news_next.get('id', None)
    all_news[temp_news_index]['lastId'] = news_last.get('id', None)

    return all_news[temp_news_index]


def get_all_news():
    # public
    all_news_data = _get_all_news()
    return [get_news(news_id=i['id'], all_news=all_news_data) for i in all_news_data]


def _get_all_news():
    # private
    news = sorted([json.loads(red_news.get(i))
                   for i in red_news.scan_iter()], key=lambda k: k['id'])
    return news


def add_news(**kwargs):
    """Add news to redis.
    Kwargs:
        title   [str]:     Required.
        imgUrl [str]:     Optional.
        url     [str]:     Link, optional.
        weight  [int]:     news weight,optional.
        description [str]: Optional.
        expireTime  [str]: ISO 8601, must have timezone at last character.
            2019-09-2T11:33:29H
            2019-09-2T11:33:29Z
            2019-09-2T11:33:29A
            ...
    Returns:
        [bool]: False
        [int]: Success, return news id.
    """
    title = kwargs.get('title', False)
    if not title:
        return False

    news_name = "news_{news_id}_{tag}"
    news_list = [i for i in red_news.scan_iter()]
    news_id = 0
    news_list.sort(key=lambda x: int(x.split("_")[1]))

    news_list.append("news_0_null")  # need null data to create new id
    for id_, key_name in zip(range(len(news_list)+1), news_list):
        id_from_key_name = key_name.split('_')[1]
        if id_ != int(id_from_key_name):
            news_id = id_
            break

    news_data = {
        "title": title,
        "id": news_id,
        "publishedAt": datetime.datetime.utcnow().isoformat(timespec="seconds")+"Z",
        "weight": int(kwargs.get('weight', 0)),
        "imgUrl": kwargs.get('imgUrl', None),
        "url": kwargs.get('url', None),
        "description": kwargs.get('description', None),
        'tag': kwargs.get('tag', [])
    }
    if kwargs.get('location', False):
        location = kwargs.get('location', {})
        if isinstance(location.get('title', False), str) and isinstance(location.get('lat', False), int) and isinstance(location.get('lng', False), int):
            news_data['location'] = {
                'title': location.get('title', None),
                'lng': location.get('lng', None),
                'lat': location.get('lat', None)
            }
    expire_time_seconds = kwargs.get('expireTime', None)
    if kwargs.get('expireTime', False):
        utc = time_format(kwargs.get('expireTime', False))
        expire_time_seconds = (utc-datetime.datetime.utcnow()).seconds
    data_dumps = json.dumps(news_data, ensure_ascii=False)

    red_news.set(name=news_name.format(news_id=news_id,
                                       tag=json.dumps(kwargs.get('tag', []))),
                 value=data_dumps, ex=expire_time_seconds)
    return news_id


def update_news(news_id=None, **kwargs):
    """Update news.
    Args:
        news_id ([int]): news id.
    Kwargs:
        title   [str]:     Optional.
        img_url [str]:     Optional.
        url     [str]:     URL, optional.
        weight  [int]:     news weight,optional.
        description [str]: Optional.
        expireTime  [str]: ISO 8601, must have timezone at last character.
            2019-09-2T11:33:29H
            2019-09-2T11:33:29Z
            2019-09-2T11:33:29A
            ...
    Returns:
        [bool]: True
    Raise:
        400:miss param.
        404:not found announcement.
    """
    if news_id == None:
        raise falcon.HTTPMissingParam("news_id")

    news_name = f"news_{news_id}"
    if not red_news.exists(news_name):
        raise falcon.HTTPNotFound(description="Not found announcement id.")

    origin_news = json.loads(red_news.get(news_name))

    news_data = {
        "title": kwargs.get('title', origin_news.get('title', "")),
        "id": int(news_id),
        "publishedAt": datetime.datetime.utcnow().isoformat(timespec="seconds")+"Z",
        "weight": int(kwargs.get('weight', int(origin_news.get('weight', 0)))),
        "imgUrl": kwargs.get('img_url', origin_news.get('imgUrl', None)),
        "url": kwargs.get('url', origin_news.get('url', None)),
        "description": kwargs.get('description', origin_news.get('description', None))
    }
    expire_time_seconds = kwargs.get(
        'expireTime', origin_news.get('expireTime', None))
    if kwargs.get('expireTime', origin_news.get('expireTime', False)):
        utc = time_format(kwargs.get(
            'expireTime', origin_news.get('expireTime', False)))
        expire_time_seconds = (utc-datetime.datetime.utcnow()).seconds
    data_dumps = json.dumps(news_data, ensure_ascii=False)

    red_news.set(name=news_name,
                 value=data_dumps, ex=expire_time_seconds)
    return True


def remove_news(news_id=None):
    """remove news.
    Args:
        news_id ([int]): news id.
    Returns:
        [bool]: True
        [int]: NEWS_NOT_FOUND
               NEWS_ERROR
    """
    if news_id is None:
        raise falcon.HTTPMissingParam("news_id")

    news_name = "news_{news_id}".format(news_id=news_id)
    if not red_news.exists(news_name):
        raise falcon.HTTPNotFound()

    red_news.delete(news_name)
    return True


def get_all_by_tag(tag_list):

    # About key name length.
    # https://stackoverflow.com/questions/6320739/does-name-length-impact-performance-in-redis

    news_list = [i for i in red_news.scan_iter()]
    news_list.sort(key=lambda x: int(x.split("_")[1]))
    temp_news_key_name = []
    for news_key_name in news_list:
        tags = json.loads(
            news_key_name[news_key_name.index("_", 5)+1:], encoding='utf-8')
        for news_tag in tags:
            if news_tag in tag_list:
                temp_news_key_name.append(news_key_name)
                break

    news_data = sorted([json.loads(red_news.get(i))
                        for i in temp_news_key_name], key=lambda k: k['id'])

    for index, value in enumerate(news_data):
        try:
            value['nextId'] = news_data[index+1]['id']
        except:
            value['nextId'] = None
        try:
            if index-1 != -1:
                value['lastId'] = news_data[index-1]['id']
            else:
                value['lastId'] = None
        except:
            value['lastId'] = None
    return news_data
