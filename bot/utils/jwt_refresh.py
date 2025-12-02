import os
import requests, json, datetime
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("GIGA_CLIENT_ID")  # добавь в .env
JWT_FILE = "/opt/ai-fit/.jwt"

def refresh_jwt():
    resp = requests.post(
        "https://gigachat.api.sberbank.ru/v1/token",
        headers={"Authorization": f"Bearer {CLIENT_ID}"},
        data={"scope": "GIGACHAT_API_PERS"}
    )
    resp.raise_for_status()
    jwt = resp.json()["access_token"]
    with open(JWT_FILE, "w") as f:
        f.write(jwt)
    print("JWT обновлён:", datetime.datetime.now())

if __name__ == "__main__":
    refresh_jwt()