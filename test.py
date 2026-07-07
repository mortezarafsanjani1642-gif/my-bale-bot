import requests
import time
import json

TOKEN = "BIJFAB0MVHQAPLZSKUQLWKYWBTLDWCEQCCBHOXLCLXUUARAVJTITTEJHIHWYMCOX"
API_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

def send_message(chat_id, text, chat_keypad=None):
    payload = {"chat_id": chat_id, "text": text}
    if chat_keypad:
        payload["chat_keypad"] = chat_keypad
        payload["chat_keypad_type"] = "New"  # طبق مستندات
    try:
        r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        if r.status_code != 200:
            print(f"❌ خطا: {r.text}")
        else:
            print("✅ پیام ارسال شد.")
    except Exception as e:
        print(f"❌ خطا: {e}")

def get_updates(offset_id=None):
    payload = {}
    if offset_id:
        payload["offset_id"] = offset_id
    payload["limit"] = 10
    try:
        r = requests.post(f"{API_URL}/getUpdates", json=payload, timeout=10)
        if r.status_code == 200:
            return r.json()
        return {}
    except Exception as e:
        print(f"❌ خطا: {e}")
        return {}

def main_menu():
    return {
        "rows": [
            {"buttons": [{"id": "1", "type": "Simple", "button_text": "🛍️ ثبت سفارش جدید"}]},
            {"buttons": [{"id": "2", "type": "Simple", "button_text": "💰 ارسال رسید پرداخت"}]},
            {"buttons": [{"id": "3", "type": "Simple", "button_text": "✏️ تغییر سفارش"}]},
            {"buttons": [{"id": "4", "type": "Simple", "button_text": "🔍 پیگیری سفارش"}]}
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def main():
    print("🚀 ربات نهایی روبیکا شروع شد...")
    offset_id = None
    processed = set()

    while True:
        try:
            response = get_updates(offset_id)
            if response.get("status") == "OK":
                data = response.get("data", {})
                updates = data.get("updates", [])
                
                if "next_offset_id" in data:
                    offset_id = data["next_offset_id"]
                    print(f"🔄 offset_id: {offset_id}")

                for upd in updates:
                    if upd.get("type") == "NewMessage":
                        chat_id = upd.get("chat_id")
                        msg = upd.get("new_message", {})
                        msg_id = msg.get("message_id")
                        text = msg.get("text", "")
                        
                        if msg_id and msg_id in processed:
                            continue
                        if msg_id:
                            processed.add(msg_id)
                        
                        print(f"📩 پیام: {text}")
                        
                        if text == "/start":
                            send_message(chat_id, "سلام! به ربات خوش آمدید.\nلطفاً از منو استفاده کنید:", main_menu())
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