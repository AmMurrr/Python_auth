import json
from kafka import KafkaConsumer
import requests
import os
from dotenv import load_dotenv

load_dotenv("app/env.env")

TELEGRAM_BOT_TOKEN_ENV=os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID_ENV=os.getenv("TELEGRAM_CHAT_ID")
KAFKA_BOOTSTRAP_SERVERS_ENV=os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC_ENV=os.getenv("KAFKA_TOPIC")


consumer = KafkaConsumer(
    KAFKA_TOPIC_ENV,  
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS_ENV,
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN_ENV}/"

def send_tg_message(text):
    data = {"chat_id": TELEGRAM_CHAT_ID_ENV, "text": text}
    response = requests.post(TELEGRAM_API_URL + "sendMessage", data=data)
    print("Ответ от Telegram:", response.json())  
    return response.json()


print("Worker is running")

for message in consumer:
    event = message.value
    print(f"Cобытие Kafka: {event}")

    if event.get("event") == "user_registered":
        user_email = event.get("user_email", "no email")

        telegram_text = f" Новый пользователь зарегистрирован\nEmail: {user_email}"
        send_tg_message(telegram_text)

    if event.get("event") == "user_auth_yandex":
        user_email = event.get("user_email", "no email")

        telegram_text = f" Пользователь авторизовался через Яндекс\n\nEmail: {user_email}"
        send_tg_message(telegram_text)


