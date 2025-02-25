from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse  
from sqlalchemy.orm import Session
from kafka import KafkaProducer
import requests
import jwt
import datetime
import os
from dotenv import load_dotenv
from app.models import User, LoginHistory, SessionLocal, init_db
from app.ya_oauth import get_ya_access_token, get_user_info  
import json

load_dotenv("app/env.env")

TELEGRAM_BOT_TOKEN_ENV = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID_ENV = os.getenv("TELEGRAM_CHAT_ID")

KAFKA_BOOTSTRAP_SERVERS_ENV = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC_ENV = os.getenv("KAFKA_TOPIC")

YANDEX_CLIENT_ID_ENV = os.getenv("YANDEX_CLIENT_ID")
YANDEX_CLIENT_SECRET_ENV = os.getenv("YANDEX_CLIENT_SECRET")
YANDEX_REDIRECT_URI_ENV = os.getenv("YANDEX_REDIRECT_URI")


SECRET_KEY_ENV = os.getenv("SECRET_KEY")

kafka_producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS_ENV],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

app = FastAPI()

init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.post("/register")
def register_user(email: str, password: str, db: Session = Depends(get_db)):
    try:

        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Пользователь уже существует")

        user_data = User(email=email, password_hash=password, role="user")
        db.add(user_data)
        db.commit()
        db.refresh(user_data)


        event = {"event": "user_registered", "user_email": email}
        kafka_producer.send(KAFKA_TOPIC_ENV, event)
        kafka_producer.flush()

        history = LoginHistory(user_id=user_data.id, ip_address="127.0.0.1",action="registration")
        db.add(history)
        db.commit()

        return {f" {user_data.id} успешно зарегистрировался"}

    except Exception as e:
        print(f"Ошибка при регистрации пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка на сервере")

@app.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or user.password_hash != password:
            raise HTTPException(status_code=401, detail="Неверные данные")

        token = jwt.encode(
            {"user_id": user.id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
            SECRET_KEY_ENV,
            algorithm="HS256",
        )

        history = LoginHistory(user_id=user.id, ip_address="127.0.0.1",action="login")
        db.add(history)
        db.commit()

        return {"access_token": token}

    except Exception as e:
        print(f"Ошибка при попытке входа: {e}")
        raise HTTPException(status_code=500, detail="Ошибка на сервере")

@app.get("/auth/ya")
def yandex_auth():
    yandex_auth_url = f"https://oauth.yandex.ru/authorize?response_type=code&client_id={YANDEX_CLIENT_ID_ENV}&redirect_uri={YANDEX_REDIRECT_URI_ENV}"
    return RedirectResponse(url=yandex_auth_url)

@app.get("/auth/ya/callback")
def yandex_callback(code: str, db: Session = Depends(get_db)):
    try:
        token_response = get_ya_access_token(code)
        access_token = token_response["access_token"]
        
        user_data = get_user_info(access_token)
        
        existing_user = db.query(User).filter(User.email == user_data["default_email"]).first()
        if not existing_user:

            user = User(email=user_data["default_email"], password_hash="", role="user") ###
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            
            user = existing_user

        token = jwt.encode(
            {"user_id": user.id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
            SECRET_KEY_ENV,
            algorithm="HS256",
        )

        event = {"event": "user_auth_yandex", "user_email": user_data['default_email']}
        kafka_producer.send(KAFKA_TOPIC_ENV, event)
        kafka_producer.flush()

        

        return {"access_token": token}
    
    except Exception as e:
        print(f"Ошибка при авторизации через Яндекс: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при авторизации через Яндекс")






