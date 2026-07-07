import requests
import time
import json

TOKEN = "BIJFAB0MVHQAPLZSKUQLWKYWBTLDWCEQCCBHOXLCLXUUARAVJTITTEJHIHWYMCOX"
API_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

def send_message(chat_id, text, chat_keypad=None, chat_keypad_type="New"):
    payload = {"chat_id": chat_id, "text": text}
    if chat_keypad:
        payload["chat_keypad"] = chat_keypad
        payload["chat_keypad_type"] = chat_keypad_type
    try:
        r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        if r.status_code != 200:
            print(f"❌ خطا در ارسال: {r.text}")
        else:
            print("✅ پیام ارسال شد.")
    except Exception as e:
        print(f"❌ خطا: {e}")

def get_updates(offset_id=None):
    payload = {}
    if offset_id:
        payload["offset_id"] = offset_id  # ✅ پارامتر صحیح
    payload["limit"] = 10  # تعداد آپدیت در هر درخواست
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
    print("🚀 ربات با offset_id شروع شد...")
    offset_id = None
    processed = set()

    while True:
        try:
            response = get_updates(offset_id)
            if response.get("status") == "OK":
                data = response.get("data", {})
                updates = data.get("updates", [])
                
                # به‌روزرسانی offset_id برای درخواست بعدی
                if "next_offset_id" in data:
                    offset_id = data["next_offset_id"]
                    print(f"🔄 offset_id جدید: {offset_id}")

                if updates:
                    print(f"📥 {len(updates)} آپدیت دریافت شد.")
                    
                    for upd in updates:
                        if upd.get("type") == "NewMessage":
                            chat_id = upd.get("chat_id")
                            msg = upd.get("new_message", {})
                            msg_id = msg.get("message_id")
                            text = msg.get("text", "")
                            sender = msg.get("sender_id")
                            
                            if not chat_id or not sender:
                                continue
                            
                            if msg_id and msg_id in processed:
                                continue
                            if msg_id:
                                processed.add(msg_id)
                            
                            print(f"📩 پیام از {sender}: {text}")
                            
                            if text == "/start":
                                send_message(chat_id, "سلام! به ربات خوش آمدید.\nلطفاً از منو استفاده کنید:", main_menu())
                            elif text in ["🛍️ ثبت سفارش جدید", "💰 ارسال رسید پرداخت", "✏️ تغییر سفارش", "🔍 پیگیری سفارش"]:
                                send_message(chat_id, f"شما {text} را انتخاب کردید.")
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