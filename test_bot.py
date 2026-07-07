import requests
import time
import json

# ===================== تنظیمات =====================
TOKEN = "BIJFAB0MVHQAPLZSKUQLWKYWBTLDWCEQCCBHOXLCLXUUARAVJTITTEJHIHWYMCOX"  # توکن خودت
API_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

# ================ توابع ارتباطی ================

def send_message(chat_id, text, keyboard=None):
    """ارسال پیام با کیبورد دلخواه"""
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
    """دریافت آپدیت‌ها با start_id"""
    payload = {}
    if start_id:
        payload["start_id"] = start_id
    payload["timeout"] = 10
    try:
        r = requests.post(f"{API_URL}/getUpdates", json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()
        return {}
    except Exception as e:
        print(f"❌ خطا در getUpdates: {e}")
        return {}

# ================ ساخت کیبورد منو ================

def main_menu_keyboard():
    """چهار دکمه اصلی"""
    return {
        "keyboard": [
            [{"text": "🛍️ ثبت سفارش جدید"}],
            [{"text": "💰 ارسال رسید پرداخت"}],
            [{"text": "✏️ تغییر سفارش"}],
            [{"text": "🔍 پیگیری سفارش"}]
        ],
        "resize_keyboard": True
    }

# ================ پردازش پیام ================

def process_message(chat_id, text):
    """پردازش پیام دریافتی"""
    if text == "/start":
        send_message(
            chat_id,
            "سلام! به ربات فروشگاهی خوش آمدید.\nلطفاً از منوی زیر استفاده کنید:",
            main_menu_keyboard()
        )
    else:
        # فعلاً فقط یک پاسخ ساده برای تست
        send_message(chat_id, f"شما پیام دادید: {text}", main_menu_keyboard())

# =================== حلقه اصلی ====================

def main():
    print("🚀 ربات تست راه‌اندازی شد...")
    start_id = None
    processed_messages = set()  # برای جلوگیری از تکرار

    while True:
        try:
            updates = get_updates(start_id)
            if updates.get("status") == "OK":
                data = updates.get("data", {})
                updates_list = data.get("updates", [])

                if updates_list:
                    print(f"📥 {len(updates_list)} آپدیت جدید دریافت شد.")

                    # به‌روزرسانی start_id با آخرین update_time + 1
                    last_time = max([u.get("update_time", 0) for u in updates_list])
                    start_id = last_time + 1

                    for upd in updates_list:
                        if upd.get("type") == "NewMessage":
                            chat_id = upd.get("chat_id")
                            msg_data = upd.get("new_message", {})
                            sender_id = msg_data.get("sender_id")
                            text = msg_data.get("text", "")
                            message_id = msg_data.get("message_id")

                            if not chat_id or not sender_id:
                                continue

                            # جلوگیری از پردازش تکراری
                            if message_id and message_id in processed_messages:
                                continue
                            if message_id:
                                processed_messages.add(message_id)

                            print(f"📩 پیام از {sender_id}: {text}")
                            process_message(chat_id, text)

            time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 ربات متوقف شد.")
            break
        except Exception as e:
            print(f"❌ خطا: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()