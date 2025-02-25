import requests
from fastapi import HTTPException
import os
from dotenv import load_dotenv

load_dotenv("app/env.env")

YANDEX_CLIENT_ID_ENV = os.getenv("YANDEX_CLIENT_ID")
YANDEX_CLIENT_SECRET_ENV = os.getenv("YANDEX_CLIENT_SECRET")
YANDEX_REDIRECT_URI_ENV = os.getenv("YANDEX_REDIRECT_URI")

def get_ya_access_token(code: str):

    token_url = "https://oauth.yandex.ru/token"
    data = {
        "code": code,
        "client_id": YANDEX_CLIENT_ID_ENV,
        "client_secret": YANDEX_CLIENT_SECRET_ENV,
        "redirect_uri": YANDEX_REDIRECT_URI_ENV,
        "grant_type": "authorization_code",
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Ошибка во время получения токена Яндекса")
    
    return response.json()


def get_user_info(access_token: str):

    user_info_url = "https://login.yandex.ru/info"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(user_info_url, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Ошибка во время получения данных пользователя из Яндекса")
    
    return response.json()
