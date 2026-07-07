import requests
import time
import json

TOKEN = "BIJFAB0MVHQAPLZSKUQLWKYWBTLDWCEQCCBHOXLCLXUUARAVJTITTEJHIHWYMCOX"
API_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

def send_message(chat_id, text, keyboard=None):
    payload = {"chat_id": chat_id, "text": text}
    if keyboard:
        payload["reply_markup"] = keyboard
    try:
        r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        if r.status_code != 200:
            print(f"❌ خطا در ارسال: {r.text}")
        else:
            print("✅ پیام ارسال شد.")
    except Exception as e:
        print(f"❌ خطا: {e}")

def get_updates():
    # بدون هیچ پارامتری، همه آپدیت‌ها را بگیر
    try:
        r = requests.post(f"{API_URL}/getUpdates", json={"timeout": 10}, timeout=15)
        if r.status_code == 200:
            return r.json()
        return {}
    except Exception as e:
        print(f"❌ خطا: {e}")
        return {}

def main_menu():
    return {
        "keyboard": [
            [{"text": "🛍️ ثبت سفارش جدید"}],
            [{"text": "💰 ارسال رسید پرداخت"}],
            [{"text": "✏️ تغییر سفارش"}],
            [{"text": "🔍 پیگیری سفارش"}]
        ],
        "resize_keyboard": True
    }

def main():
    print("🚀 ربات با روش آخرین پیام شروع شد...")
    last_message_id = None  # فقط آخرین پیام را پردازش کن

    while True:
        try:
            response = get_updates()
            if response.get("status") == "OK":
                data = response.get("data", {})
                updates = data.get("updates", [])

                if updates:
                    # فقط آخرین آپدیت را بگیر
                    last_update = updates[-1]
                    
                    if last_update.get("type") == "NewMessage":
                        chat_id = last_update.get("chat_id")
                        msg = last_update.get("new_message", {})
                        msg_id = msg.get("message_id")
                        text = msg.get("text", "")
                        sender = msg.get("sender_id")

                        # اگر این پیام قبلاً پردازش نشده
                        if msg_id != last_message_id:
                            last_message_id = msg_id
                            print(f"📩 پیام جدید از {sender}: {text}")
                            
                            if text == "/start":
                                send_message(chat_id, "سلام! به ربات خوش آمدید.\nلطفاً از منو استفاده کنید:", main_menu())
                            else:
                                send_message(chat_id, f"شما گفتید: {text}", main_menu())
                        else:
                            print("⏳ پیام تکراری، نادیده گرفته شد.")

            time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 توقف.")
            break
        except Exception as e:
            print(f"❌ خطا: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()