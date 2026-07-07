import requests
import time
import json

TOKEN = "BIJFAB0MVHQAPLZSKUQLWKYWBTLDWCEQCCBHOXLCLXUUARAVJTITTEJHIHWYMCOX"
API_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

def send_message(chat_id, text):
    """ارسال پیام ساده بدون کیبورد"""
    payload = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        print(f"📤 پاسخ sendMessage: {r.status_code} - {r.text}")
        if r.status_code != 200:
            print(f"❌ خطا در ارسال: {r.text}")
    except Exception as e:
        print(f"❌ خطا: {e}")

def get_updates():
    try:
        r = requests.post(f"{API_URL}/getUpdates", json={"timeout": 10}, timeout=15)
        if r.status_code == 200:
            return r.json()
        return {}
    except Exception as e:
        print(f"❌ خطا: {e}")
        return {}

def main():
    print("🚀 ربات تست ساده شروع شد...")
    last_message_id = None

    while True:
        try:
            response = get_updates()
            if response.get("status") == "OK":
                data = response.get("data", {})
                updates = data.get("updates", [])

                if updates:
                    last_update = updates[-1]
                    if last_update.get("type") == "NewMessage":
                        chat_id = last_update.get("chat_id")
                        msg = last_update.get("new_message", {})
                        msg_id = msg.get("message_id")
                        text = msg.get("text", "")

                        if msg_id != last_message_id:
                            last_message_id = msg_id
                            print(f"📩 پیام جدید: {text}")
                            
                            # فقط یک پیام ساده بفرست (بدون کیبورد)
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