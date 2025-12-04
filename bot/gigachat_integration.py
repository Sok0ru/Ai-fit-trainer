import os
import uuid
import logging
from datetime import datetime, timedelta
import requests
import requests.packages.urllib3.util.connection as conn

logger = logging.getLogger(__name__)

# ---------- ваши ключи ----------
AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY")   # Basic ... из личного кабинета
SCOPE    = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")

# ---------- фикс-IP + официальные пути ----------
TOKEN_URL = "https://185.157.96.168:9443/api/v2/oauth"
CHAT_URL  = "https://185.157.96.168:443/api/v1/chat/completions"

_token = None
_expires = None

_orig_create_connection = conn.create_connection
def patched_create_connection(address, *args, **kwargs):
    host, port = address
    if host == "ngw.devices.sberbank.ru":
        host = "185.157.96.168"
    elif host == "gigachat.devices.sberbank.ru":
        host = "185.157.96.168"
    return _orig_create_connection((host, port), *args, **kwargs)

conn.create_connection = patched_create_connection
# ---------- получение токена (30 мин) ----------
def _get_token() -> str:
    global _token, _expires
    if _token and _expires and datetime.utcnow() < _expires:
        return _token

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": AUTH_KEY,
        "Host": "ngw.devices.sberbank.ru"      # SNI
    }
    data = {"scope": SCOPE}

    try:
        resp = requests.post(TOKEN_URL, headers=headers, data=data, verify=False, timeout=10)
        resp.raise_for_status()
        j = resp.json()
        _token = j["access_token"]
        _expires = datetime.utcnow() + timedelta(seconds=j["expires_at"] - 10)
        logger.info("GigaChat токен получен")
        return _token
    except Exception as e:
        logger.exception("Ошибка получения токена")
        raise RuntimeError("Не удалось получить токен GigaChat") from e

# ---------- генерация плана ----------
def generate_plan(prompt: str) -> str:
    token = _get_token()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "Host": "gigachat.devices.sberbank.ru"   # SNI
    }
    payload = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }

    try:
        resp = requests.post(CHAT_URL, headers=headers, json=payload, verify=False, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.exception("Ошибка генерации плана")
        raise RuntimeError("Не удалось подключиться к GigaChat API. Проверьте сетевые настройки.") from e
