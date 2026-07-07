import requests
import time
import json

TOKEN = "BIJFAB0MVHQAPLZSKUQLWKYWBTLDWCEQCCBHOXLCLXUUARAVJTITTEJHIHWYMCOX"
API_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

def send_message(chat_id, text, inline_keypad=None):
    payload = {"chat_id": chat_id, "text": text}
    if inline_keypad:
        payload["inline_keypad"] = inline_keypad
    try:
        r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        print(f"📤 پاسخ: {r.status_code} - {r.text}")
        if r.status_code != 200:
            print(f"❌ خطا در ارسال: {r.text}")
    except Exception as e:
        print(f"❌ خطا: {e}")

def get_updates(start_id=None):
    payload = {}
    if start_id:
        payload["start_id"] = start_id
    payload["timeout"] = 5
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
            {
                "buttons": [
                    {"id": "new_order", "type": "Simple", "button_text": "🛍️ ثبت سفارش جدید"}
                ]
            },
            {
                "buttons": [
                    {"id": "receipt", "type": "Simple", "button_text": "💰 ارسال رسید پرداخت"}
                ]
            },
            {
                "buttons": [
                    {"id": "edit", "type": "Simple", "button_text": "✏️ تغییر سفارش"}
                ]
            },
            {
                "buttons": [
                    {"id": "track", "type": "Simple", "button_text": "🔍 پیگیری سفارش"}
                ]
            }
        ]
    }

def process_update(chat_id, text):
    if text == "/start":
        send_message(chat_id, "سلام! به ربات خوش آمدید.\nلطفاً از منو استفاده کنید:", main_menu())
    else:
        # پاسخ به دکمه‌ها
        if text == "new_order":
            send_message(chat_id, "شما ثبت سفارش جدید را انتخاب کردید.")
        elif text == "receipt":
            send_message(chat_id, "شما ارسال رسید پرداخت را انتخاب کردید.")
        elif text == "edit":
            send_message(chat_id, "شما تغییر سفارش را انتخاب کردید.")
        elif text == "track":
            send_message(chat_id, "شما پیگیری سفارش را انتخاب کردید.")
        else:
            send_message(chat_id, f"شما گفتید: {text}")

def main():
    print("🚀 ربات با inline_keypad شروع شد...")
    start_id = None
    processed = set()

    while True:
        try:
            response = get_updates(start_id)
            if response.get("status") == "OK":
                data = response.get("data", {})
                updates = data.get("updates", [])

                if updates:
                    # به‌روزرسانی start_id با آخرین update_time
                    last_time = max([u.get("update_time", 0) for u in updates])
                    start_id = last_time + 1
                    print(f"🔄 start_id: {start_id}")

                    for upd in updates:
                        # دریافت پیام‌های متنی
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
                            process_update(chat_id, text)
                        
                        # دریافت کلیک روی دکمه‌های inline
                        elif upd.get("type") == "InlineMessage":
                            chat_id = upd.get("chat_id")
                            inline_msg = upd.get("inline_message", {})
                            msg_id = inline_msg.get("message_id")
                            data = inline_msg.get("data", {})
                            button_id = data.get("id") if data else None
                            
                            if msg_id and msg_id in processed:
                                continue
                            if msg_id:
                                processed.add(msg_id)
                            
                            if button_id:
                                print(f"🔘 کلیک روی دکمه: {button_id}")
                                process_update(chat_id, button_id)

            time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 توقف.")
            break
        except Exception as e:
            print(f"❌ خطا: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()