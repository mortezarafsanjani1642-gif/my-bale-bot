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
        print(f"📤 پاسخ: {r.status_code} - {r.text}")
        if r.status_code != 200:
            print(f"❌ خطا در ارسال: {r.text}")
    except Exception as e:
        print(f"❌ خطا: {e}")

def get_updates():
    try:
        r = requests.post(f"{API_URL}/getUpdates", json={"timeout": 5}, timeout=10)
        if r.status_code == 200:
            return r.json()
        return {}
    except Exception as e:
        print(f"❌ خطا: {e}")
        return {}

def main():
    print("🚀 تست کیبورد ساده شروع شد...")
    last_message_id = None

    while True:
        try:
            response = get_updates()
            if response.get("status") == "OK":
                data = response.get("data", {})
                updates = data.get("updates", [])

                if updates:
                    last_new = None
                    for upd in reversed(updates):
                        if upd.get("type") == "NewMessage":
                            last_new = upd
                            break
                    
                    if last_new:
                        chat_id = last_new.get("chat_id")
                        msg = last_new.get("new_message", {})
                        msg_id = msg.get("message_id")
                        text = msg.get("text", "")
                        
                        if msg_id != last_message_id:
                            last_message_id = msg_id
                            print(f"📩 پیام جدید: {text}")
                            
                            if text == "/start":
                                # ✅ ساده‌ترین کیبورد ممکن: فقط یک دکمه
                                keyboard = {
                                    "keyboard": [
                                        [{"text": "🛍️ ثبت سفارش"}]
                                    ]
                                }
                                send_message(chat_id, "سلام! روی دکمه کلیک کن:", keyboard)
                            else:
                                send_message(chat_id, f"شما گفتید: {text}")

            time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 توقف.")
            break
        except Exception as e:
            print(f"❌ خطا: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()