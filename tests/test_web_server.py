from falcon import testing
import pytest
import logging
import sys
import os
import json


myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../src/')

if True:
    import web_server
    from utils import config

"""
A Integrated Testing on falcon framework
"""

USER_ACCOUNT_JWT = None
ADMIN_ACCOUNT_JWT = None


def setup_module(module):
    global USER_ACCOUNT_JWT, ADMIN_ACCOUNT_JWT
    logging.warning(
        "This test will clear redis, please don't use on product.")
    flush_all()

    web_server.auth_service.register(
        username="user_level_account",
        password="".join(['1' for i in range(64)])
    )

    USER_ACCOUNT_JWT = web_server.auth_service.login(
        username="user_level_account",
        password="".join(['1' for i in range(64)])
    )

    web_server.auth_service.register(
        username="admin_level_account",
        password="".join(['2' for i in range(64)])
    )

    # set admin in config
    config.ADMIN.append("admin_level_account")

    ADMIN_ACCOUNT_JWT = web_server.auth_service.login(
        username="admin_level_account",
        password="".join(['2' for i in range(64)])
    )


def flush_all():
    os.system(f'redis-cli -u {config.REDIS_URL} FLUSHALL')


def flush_db(target_db):
    os.system(f'redis-cli -u {config.REDIS_URL} -n {target_db} FLUSHDB')


@pytest.fixture()
def client():
    return testing.TestClient(web_server.app)


def test_register(client):

    # register test
    result = client.simulate_post('/register', json={
        "username": "testtest1",
        "password": "".join(['1' for i in range(64)])
    })
    assert isinstance(result.json.get("key"), str)
    # test register same account
    result = client.simulate_post('/register', json={
        "username": "testtest1",
        "password": "".join(['1' for i in range(64)])
    })
    assert result.status_code == 401

    # test username and password in limit
    result = client.simulate_post('/register', json={
        "username": "testtes",
        "password": "".join(['1' for i in range(64)])
    })
    assert result.status_code == 401

    result = client.simulate_post('/register', json={
        "username": "testtest_password_<50length",
        "password": "".join(['1' for i in range(49)])
    })
    assert result.status_code == 401
    result = client.simulate_post('/register', json={
        "username": "testtest_password_>80length",
        "password": "".join(['1' for i in range(81)])
    })
    assert result.status_code == 401

    result = client.simulate_post('/register', json={
        "username": "testtest_password_>80length",
        "password": "".join(['1' for i in range(81)]),
        "test": "test not allow key"
    })
    assert result.status_code == 400


def test_login(client):
    # register test
    result = client.simulate_post('/login', json={
        "username": "user_level_account",
        "password": "".join(['1' for i in range(64)])
    })
    assert isinstance(result.json.get("key"), str)

    result = client.simulate_post('/login', json={
        "username": "fail_login_test",
        "password": "".join(['1' for i in range(64)])
    })
    assert result.status_code == 401

    # not allow key test
    result = client.simulate_post('/login', json={
        "username": "fail_login_test",
        "password": "".join(['1' for i in range(64)]),
        "this_key_not_allow": ":)"
    })
    assert result.status_code == 400


def test_get_user_info(client):
    # test user level account
    result = client.simulate_get('/user/info', headers={
        "Authorization": f"Bearer {USER_ACCOUNT_JWT}"
    })
    assert result.json == {
        "username": "user_level_account",
        "login_type": "General",
        "permission_level": 0
    }

    # test user admin account
    result = client.simulate_get('/user/info', headers={
        "Authorization": f"Bearer {ADMIN_ACCOUNT_JWT}"
    })
    assert result.json == {
        "username": "admin_level_account",
        "login_type": "General",
        "permission_level": 2
    }


def test_add_editor(client):

    # create temp user
    web_server.auth_service.register(
        username="user_for_add_editor_test",
        password="".join(['1' for i in range(64)])
    )

    before_add_editor_list = web_server.auth_service.get_editor_list()
    # test not permission
    permission_test = client.simulate_post('/auth/editor',
                                           json={
                                               'username': "user_for_add_editor_test"}
                                           )
    assert permission_test.status_code == 401
    # test user level permission
    permission_test = client.simulate_post(
        '/auth/editor',
        json={
            'username': "user_for_add_editor_test"},
        headers={"Authorization": f"Bearer {USER_ACCOUNT_JWT}"}
    )
    assert permission_test.status_code == 403

    # test admin add
    permission_test = client.simulate_post(
        '/auth/editor',
        json={
            'username': "user_for_add_editor_test"},
        headers={"Authorization": f"Bearer {ADMIN_ACCOUNT_JWT}"}
    )
    assert permission_test.status_code == 200

    after_add_editor_list = web_server.auth_service.get_editor_list()

    assert list(set(after_add_editor_list) -
                set(before_add_editor_list))[0] == "user_for_add_editor_test"


def test_get_editor(client):

    permission_test = client.simulate_get('/auth/editor')
    assert permission_test.status_code == 401

    # test user level permission
    permission_test = client.simulate_get(
        '/auth/editor',
        headers={"Authorization": f"Bearer {USER_ACCOUNT_JWT}"}
    )
    assert permission_test.status_code == 403

    # test admin add
    permission_test = client.simulate_get(
        '/auth/editor',
        headers={"Authorization": f"Bearer {ADMIN_ACCOUNT_JWT}"}
    )
    assert permission_test.status_code == 200
    assert permission_test.json == web_server.auth_service.get_editor_list()


def test_get_null_announcement(client):
    result = client.simulate_get('/announcements')
    assert result.json == []
    assert result.status_code == 200


def test_add_announcements(client):
    body = {}
    for field, field_config in config.ANNOUNCEMENT_FIELD.items():
        if field_config['allow_user_set']:
            if field_config['type'] == str:
                body[field] = "test add"
            elif field_config['type'] == int:
                body[field] = 123
            elif field_config['type'] == list:
                body[field] = []
            elif field_config['type'] == dict:
                body[field] = {}
    if body.get("expireTime"):
        body['expireTime'] = None

    # test not permission
    permission_test = client.simulate_post('/announcements/add',
                                           json=body)
    assert permission_test.status_code == 401
    # test user level permission
    permission_test = client.simulate_post(
        '/announcements/add',
        json=body,
        headers={"Authorization": f"Bearer {USER_ACCOUNT_JWT}"}
    )
    assert permission_test.status_code == 403

    # test admin add
    test_add = client.simulate_post(
        '/announcements/add',
        json=body,
        headers={"Authorization": f"Bearer {ADMIN_ACCOUNT_JWT}"}
    )

    assert test_add.status_code == 200
    check = {}
    temp = json.loads(
        web_server.acs.get_announcement_by_id(test_add.json['id']))

    for k in body.keys():
        assert body[k] == temp[k]
    assert temp.get("publishedAt")


def test_get_announcements(client):
    result = client.simulate_get('/announcements')
    assert result.json[0] == web_server.acs.get_all_announcement()[0]
    assert result.status_code == 200

    for i in result.json:
        test_get_deleted_data = client.simulate_get(
            f'/announcements/{i["id"]}',
            headers={"Authorization": f"Bearer {USER_ACCOUNT_JWT}"}
        )
        assert test_get_deleted_data.status_code == 200


def test_update_announcements(client):
    body = {}
    for field, field_config in config.ANNOUNCEMENT_FIELD.items():
        if field_config['allow_user_set']:
            if field_config['type'] == str:
                body[field] = "test update"
            elif field_config['type'] == int:
                body[field] = 123
            elif field_config['type'] == list:
                body[field] = []
            elif field_config['type'] == dict:
                body[field] = {}
    if body.get("expireTime"):
        body['expireTime'] = None

    # admin add
    test_add = client.simulate_post(
        '/announcements/add',
        json=body,
        headers={"Authorization": f"Bearer {ADMIN_ACCOUNT_JWT}"}
    )

    assert test_add.status_code == 200
    add_id = test_add.json['id']

    body['title'] = "Updateeeeee"
    # test update
    test_add = client.simulate_put(
        f'/announcements/update/{add_id}',
        json=body,
        headers={"Authorization": f"Bearer {ADMIN_ACCOUNT_JWT}"}
    )

    temp = json.loads(
        web_server.acs.get_announcement_by_id(add_id))
    assert temp['title'] == 'Updateeeeee'


def test_delete_announcements(client):
    body = {}
    for field, field_config in config.ANNOUNCEMENT_FIELD.items():
        if field_config['allow_user_set']:
            if field_config['type'] == str:
                body[field] = "test update"
            elif field_config['type'] == int:
                body[field] = 123
            elif field_config['type'] == list:
                body[field] = []
            elif field_config['type'] == dict:
                body[field] = {}
    if body.get("expireTime"):
        body['expireTime'] = None

    # admin add
    test_add = client.simulate_post(
        '/announcements/add',
        json=body,
        headers={"Authorization": f"Bearer {ADMIN_ACCOUNT_JWT}"}
    )

    assert test_add.status_code == 200
    add_id = test_add.json['id']

    web_server.acs.get_announcement_by_id(test_add.json['id'])

    test_delete = client.simulate_delete(
        f'/announcements/delete/{add_id}',
        headers={"Authorization": f"Bearer {ADMIN_ACCOUNT_JWT}"}
    )
    assert test_delete.status_code == 200
    # test get deleted id
    test_get_deleted_data = client.simulate_get(
        f'/announcements/{add_id}',
        headers={"Authorization": f"Bearer {USER_ACCOUNT_JWT}"}
    )
    assert test_get_deleted_data.status_code == 404
