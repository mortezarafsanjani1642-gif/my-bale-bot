import requests
import time
import json

TOKEN = "BIJFAB0MVHQAPLZSKUQLWKYWBTLDWCEQCCBHOXLCLXUUARAVJTITTEJHIHWYMCOX"
API_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

def send_message(chat_id, text):
    payload = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        print(f"📤 پاسخ: {r.status_code} - {r.text}")
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
    print("🚀 ربات تست ساده شروع شد...")
    last_update_time = 0

    while True:
        try:
            response = get_updates()
            if response.get("status") == "OK":
                data = response.get("data", {})
                updates = data.get("updates", [])

                if updates:
                    # فقط جدیدترین آپدیت را بگیر
                    last_update = updates[-1]
                    update_time = last_update.get("update_time", 0)

                    if update_time > last_update_time:
                        last_update_time = update_time

                        if last_update.get("type") == "NewMessage":
                            chat_id = last_update.get("chat_id")
                            msg = last_update.get("new_message", {})
                            text = msg.get("text", "")
                            sender = msg.get("sender_id")

                            print(f"📩 پیام جدید از {sender}: {text}")
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