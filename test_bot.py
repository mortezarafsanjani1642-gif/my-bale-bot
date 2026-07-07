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
    except Exception as e:
        print(f"❌ خطا: {e}")

def get_updates(start_id=None):
    payload = {}
    if start_id:
        payload["start_id"] = start_id
    payload["timeout"] = 10
    try:
        r = requests.post(f"{API_URL}/getUpdates", json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"❌ HTTP Error: {r.status_code}")
            return {}
    except Exception as e:
        print(f"❌ خطا در getUpdates: {e}")
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

def process_message(chat_id, text):
    if text == "/start":
        send_message(chat_id, "سلام! به ربات خوش آمدید.\nلطفاً از منو استفاده کنید:", main_menu())
    else:
        send_message(chat_id, f"شما گفتید: {text}", main_menu())

def main():
    print("🚀 ربات با start_id و update_time شروع شد...")
    start_id = None
    processed = set()

    while True:
        try:
            response = get_updates(start_id)
            if response.get("status") == "OK":
                data = response.get("data", {})
                updates = data.get("updates", [])

                if updates:
                    # محاسبه start_id جدید از آخرین update_time
                    last_update_time = max([u.get("update_time", 0) for u in updates])
                    start_id = last_update_time + 1  # ✅ کلید اصلی: استفاده از update_time

                    print(f"📥 {len(updates)} آپدیت جدید. start_id جدید: {start_id}")

                    for upd in updates:
                        if upd.get("type") == "NewMessage":
                            chat_id = upd.get("chat_id")
                            msg = upd.get("new_message", {})
                            sender = msg.get("sender_id")
                            text = msg.get("text", "")
                            msg_id = msg.get("message_id")

                            if not chat_id or not sender:
                                continue

                            if msg_id and msg_id in processed:
                                continue
                            if msg_id:
                                processed.add(msg_id)

                            print(f"📩 پیام از {sender}: {text}")
                            process_message(chat_id, text)
                else:
                    # هیچ آپدیت جدیدی نیست
                    pass

            time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 توقف.")
            break
        except Exception as e:
            print(f"❌ خطا: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()