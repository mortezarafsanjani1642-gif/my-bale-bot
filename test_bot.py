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
    try:
        r = requests.post(f"{API_URL}/getUpdates", json={"timeout": 5}, timeout=10)
        if r.status_code == 200:
            return r.json()
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

def main():
    print("🚀 ربات با مدیریت update_time شروع شد...")
    last_update_time = 0  # فقط آپدیت‌های جدیدتر از این زمان را پردازش کن
    processed_messages = set()  # برای جلوگیری از تکرار

    while True:
        try:
            response = get_updates()
            if response.get("status") == "OK":
                data = response.get("data", {})
                updates = data.get("updates", [])

                if updates:
                    # پیدا کردن جدیدترین update_time
                    max_time = max([u.get("update_time", 0) for u in updates])
                    
                    # فقط آپدیت‌هایی که جدیدتر از last_update_time هستند
                    new_updates = [u for u in updates if u.get("update_time", 0) > last_update_time]
                    
                    if new_updates:
                        print(f"📥 {len(new_updates)} آپدیت جدید دریافت شد.")
                        last_update_time = max_time
                        
                        for upd in new_updates:
                            if upd.get("type") == "NewMessage":
                                chat_id = upd.get("chat_id")
                                msg = upd.get("new_message", {})
                                msg_id = msg.get("message_id")
                                text = msg.get("text", "")
                                sender = msg.get("sender_id")
                                
                                if not chat_id or not sender:
                                    continue
                                
                                # جلوگیری از پردازش تکراری
                                if msg_id and msg_id in processed_messages:
                                    continue
                                if msg_id:
                                    processed_messages.add(msg_id)
                                
                                print(f"📩 پیام از {sender}: {text}")
                                
                                if text == "/start":
                                    send_message(chat_id, "سلام! به ربات خوش آمدید.\nلطفاً از منو استفاده کنید:", main_menu())
                                else:
                                    send_message(chat_id, f"شما گفتید: {text}", main_menu())

            time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 توقف.")
            break
        except Exception as e:
            print(f"❌ خطا: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()