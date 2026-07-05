import requests
import time
import os
from flask import Flask
from threading import Thread

# --- تنظیمات بات ---
TOKEN = os.environ.get("Bot_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
API_URL = f"https://tapi.bale.ai/bot{TOKEN}"

# برای ذخیره وضعیت هر کاربر
user_data = {}

# --- وب‌سرور برای زنده نگه داشتن Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running! 🚀"

def run_flask():
    # استفاده از پورتی که Render تعیین می‌کند
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- توابع بات ---
def send_message(chat_id, text, keyboard=None):
    payload = {"chat_id": chat_id, "text": text}
    if keyboard:
        payload["reply_markup"] = keyboard
    requests.post(f"{API_URL}/sendMessage", data=payload)

def get_updates(offset=None):
    params = {"offset": offset}
    try:
        response = requests.get(f"{API_URL}/getUpdates", params=params)
        print (f"get_updates status: {response.status_code}")
        if response.status_code == 200:
            print(f"get_updates response : {response.status_code} - {response.text[:200]}")
            
            return response.json()
        return {}
    except Exception as e:
        print(f"خطا در اتصال: {e}")
        return {}

def bot_loop():
    print("بات روشن شد... در حال گوش دادن به پیام‌ها 🚀")
    print("Bot loop is running...!")
    last_update_id = 0
    while True:
        try:
            updates = get_updates(last_update_id + 1)
             print(f"updates result: {updates}")
            print(f"updates received: {updates}")
            if "result" in updates:
                for update in updates["result"]:
                    last_update_id = update["update_id"]
                    if "message" in update:
                        message = update["message"]
                        chat_id = message["from"]["id"]
                        text = message.get("text", "")

                        if text == "/start" or text == "🛍️ ثبت سفارش":
                            user_data[chat_id] = {"state": "WAITING_NAME"}
                            send_message(chat_id, "سلام! خوش آمدید. 😊\nلطفاً نام و نام خانوادگی خود را ارسال کنید:")
                            continue

                        state = user_data.get(chat_id, {}).get("state")
                        if state == "WAITING_NAME":
                            user_data[chat_id]["name"] = text
                            user_data[chat_id]["state"] = "WAITING_PHONE"
                            send_message(chat_id, "ممنون! حالا لطفاً شماره تلفن خود را بفرستید:")
                        elif state == "WAITING_PHONE":
                            user_data[chat_id]["phone"] = text

                            user_data[chat_id]["state"] = "WAITING_ADDRESS"
                            send_message(chat_id, "سپاس. در مرحله آخر، لطفاً آدرس دقیق* خود را ارسال کنید:")
                        elif state == "WAITING_ADDRESS":
                            user_data[chat_id]["address"] = text
                            user_data[chat_id]["state"] = "FINISHED"
                            order_summary = (
                                f"📦 سفارش جدید دریافت شد!\n\n"
                                f"👤 نام: {user_data[chat_id]['name']}\n"
                                f"📞 تلفن: {user_data[chat_id]['phone']}\n"
                                f"📍 آدرس: {user_data[chat_id]['address']}\n"
                                f"🆔 آیدی کاربر: {chat_id}"
                            )
                            send_message(ADMIN_ID, order_summary)
                            send_message(chat_id, "سفارش شما با موفقیت ثبت شد. ✅\nبه زودی با شما تماس خواهیم گرفت.")
                            del user_data[chat_id]
                        else:
                            keyboard = {"keyboard": [[{"text": "🛍️ ثبت سفارش"}]], "resizekeyboard": True}
                            send_message(chat_id, "برای ثبت سفارش روی دکمه زیر کلیک کنید: 👇", keyboard=keyboard)
            time.sleep(2)
        except Exception as e:
            print(f"خطا در حلقه بات: {e}")
            time.sleep(3)

if __name__ == "__main__":
    # اجرای وب‌سرور در یک رشته جداگانه
    t = Thread(target=run_flask)
    t.start()

    # اجرای حلقه بات در رشته اصلی
    bot_loop()
