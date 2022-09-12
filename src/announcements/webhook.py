from multiprocessing import pool
import requests
from utils.config import DISCORD_WEBHOOK_URL
async_pool = pool.ThreadPool()


def send_all_webhook(**kwargs):
    """Send message to all webhook.
    Kwargs: webhook content.

    """
    webhook_function = [discord_webhook]
    for i in webhook_function:
        async_pool.apply_async(
            func=i,
            kwds=kwargs
        )

def discord_message(message:str):
    if DISCORD_WEBHOOK_URL == None:
        return False
    requests.post(
        url=DISCORD_WEBHOOK_URL,
        json={
            "content": message
        }
    )

def discord_webhook(**kwargs):
    if DISCORD_WEBHOOK_URL == None:
        return False
    requests.post(
        url=DISCORD_WEBHOOK_URL,
        json={
            "content": f'New application, \n{kwargs.get("application_id","null")}\n {kwargs.get("title","No title")}',
            "embeds": [
                {"description":
                    f"""
                    Application_id: {kwargs.get("application_id","null")}
                    Title: **{kwargs.get("title","No title")}**
                    Description: {kwargs.get("description","No description :(")}
                    applicant: {kwargs.get("applicant","null")}
                    fcm: {kwargs.get("fcm_token","null")}
                    """,
                 "image": {"url": kwargs.get("imgUrl", None)}
                 }
            ]
        }
    )
