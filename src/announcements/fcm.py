import requests
from utils.config import FCM_SERVER_TOKEN


def send_message(fcm_token: str, title: str, description: str):
    # firebase cloud message send.
    if FCM_SERVER_TOKEN == None:
        return False
    req = requests.post(
        'https://fcm.googleapis.com/fcm/send',
        json={
            'notification': {
                'body': description,
                'title': title
            },
            'priority': 'high',
            'data': {
                'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                'id': '1',
                'status': 'done'
            },
            'to': fcm_token
        }, headers={
            'Content-Type': 'application/json',
            'Authorization': f'key={FCM_SERVER_TOKEN}'
        })
    return req
