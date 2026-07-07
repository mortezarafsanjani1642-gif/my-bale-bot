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

def get_updates():
    try:
        r = requests.post(f"{API_URL}/getUpdates", json={"timeout": 5}, timeout=10)
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
    print("🚀 ربات شروع شد...")
    last_update_time = 0
    
    while True:
        try:
            response = get_updates()
            if response.get("status") == "OK":
                data = response.get("data", {})
                updates = data.get("updates", [])
                
                # فقط آپدیت‌های جدیدتر از last_update_time رو پردازش کن
                new_updates = [u for u in updates if u.get("update_time", 0) > last_update_time]
                
                if new_updates:
                    # به‌روزرسانی last_update_time
                    last_update_time = max([u.get("update_time", 0) for u in new_updates])
                    
                    for upd in new_updates:
                        if upd.get("type") == "NewMessage":
                            chat_id = upd.get("chat_id")
                            msg = upd.get("new_message", {})
                            text = msg.get("text", "")
                            sender = msg.get("sender_id")
                            
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