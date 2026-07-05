import requests
import time
# --- تنظیمات بات ---
TOKEN = "626939785:8_aTchF4OohBT0FKJxTnsexwpR8gyzbGmms"
ADMIN_ID = "1264284928"
API_URL = f"https://api.bale.ai/bot{TOKEN}"

# برای ذخیره وضعیت هر کاربر (که در چه مرحله‌ای از سفارش است)
user_data = {}

def send_message(chat_id, text, keyboard=None):
    payload = {"chat_id": chat_id, "text": text}
    if keyboard:
        payload["reply_markup"] = keyboard
    requests.post(f"{API_URL}/sendMessage", data=payload)

def get_updates(offset=None):
    params = {"offset": offset}
    try:
        response = requests.get(f"{API_URL}/getUpdates", params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"خطای سرور: {response.status_code}")
            return {}
    except Exception as e:
        print(f"خطا در اتصال: {e}")
        return {}

print("بات روشن شد... در حال گوش دادن به پیام‌ها 🚀")

last_update_id = None

while True:
    try:
        updates = get_updates(last_update_id + 1 if last_update_id else None)
        if "result" in updates:
            for update in updates["result"]:
                last_update_id = update["update_id"]

                if "message" in update:
                    message = update["message"]
                    chat_id = message["from"]["id"]
                    text = message.get("text", "")

                    # اگر کاربر برای اولین بار پیام داده یا دکمه شروع را زده است
                    if text == "/start" or text == "🛍️ ثبت سفارش":
                        user_data[chat_id] = {"state": "WAITING_NAME"}
                        send_message(chat_id, "سلام! خوش آمدید. 😊\nلطفاً نام و نام خانوادگی خود را ارسال کنید:")
                        continue

                    # بررسی وضعیت کاربر در مراحل مختلف
                    state = user_data.get(chat_id, {}).get("state")

                    if state == "WAITING_NAME":
                        user_data[chat_id]["name"] = text
                        user_data[chat_id]["state"] = "WAITING_PHONE"
                        send_message(chat_id, "ممنون! حالا لطفاً شماره تلفن خود را بفرستید:")

                    elif state == "WAITING_PHONE":
                        user_data[chat_id]["phone"] = text
                        user_data[chat_id]["state"] = "WAITING_ADDRESS"
                        send_message(chat_id, "سپاس. در مرحله آخر، لطفاً آدرس دقیق* خود را ارسال کنید:")

                    elif state == "WAITING_ADDRESS":
                        user_data[chat_id]["address"] = text
                        user_data[chat_id]["state"] = "FINISHED"

                        # جمع‌آوری اطلاعات برای ادمین
                        order_summary = (

                            f"📦 *سفارش جدید دریافت شد!\n\n"
                            f"👤 نام: {user_data[chat_id]['name']}\n"
                            f"📞 تلفن: {user_data[chat_id]['phone']}\n"
                            f"📍 آدرس: {user_data[chat_id]['address']}\n"
                            f"🆔 آیدی کاربر: {chat_id}"
                        )

                        # ارسال سفارش به ادمین
                        send_message(ADMIN_ID, order_summary)

                        # پیام تایید به کاربر
                        send_message(chat_id, "سفارش شما با موفقیت ثبت شد. ✅\nبه زودی با شما تماس خواهیم گرفت.")

                        # پاک کردن وضعیت کاربر برای سفارش بعدی
                        del user_data[chat_id]

                    else:
                        # اگر کاربر خارج از جریان سفارش باشد
                        keyboard = {
                            "keyboard": [[{"text": "🛍️ ثبت سفارش"}]],
                            "resize_keyboard": True
                        }
                        send_message(chat_id, "برای ثبت سفارش روی دکمه زیر کلیک کنید: 👇", keyboard=keyboard)

        time.sleep(2) # برای اینکه فشار زیادی به سرور وارد نشود
    except Exception as e:
        print(f"خطا: {e}")
        time.sleep(3)