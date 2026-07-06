import requests
import time
import os
import random
import string
from flask import Flask
from threading import Thread

# ========== تنظیمات قابل تغییر توسط شما ==========
PRODUCTS = {
    "سوسیس آلمانی": 1000,
    "سوسیس بلغاری": 1000,
    "ناگت مرغ": 1000,
    "ناگت بوقلمون": 1000
}

NEXT_PRODUCTION_DATE = "۱۵ تیر ۱۴۰۴"

# لیست وزن‌ها با مقادیر عددی (به کیلوگرم)
QUANTITIES = {
    "نیم کیلو": 0.5,
    "یک کیلو": 1.0,
    "یک کیلو و نیم": 1.5,
    "دو کیلو": 2.0,
    "دو کیلو و نیم": 2.5,
    "سه کیلو": 3.0
}

# ========== تنظیمات بات ==========
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
API_URL = f"https://tapi.bale.ai/bot{TOKEN}"

user_data = {}
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running! 🚀"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ========== توابع کمکی ==========
def send_message(chat_id, text, keyboard=None):
    payload = {"chat_id": chat_id, "text": text}
    if keyboard:
        payload["reply_markup"] = keyboard
    try:
        r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        print(f"Send status: {r.status_code}")
    except Exception as e:
        print(f"Send error: {e}")

def get_updates(offset=None):
    params = {"offset": offset, "timeout": 20}
    try:
        response = requests.get(f"{API_URL}/getUpdates", params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception as e:
        print(f"خطا در اتصال: {e}")
        return {}

def generate_tracking_code():
    return ''.join(random.choices(string.digits, k=6))

def build_product_keyboard():
    keyboard = [[{"text": p}] for p in PRODUCTS.keys()]
    keyboard.append([{"text": "🔙 بازگشت"}])
    return {"keyboard": keyboard, "resize_keyboard": True}

def build_quantity_keyboard():
    keyboard = [[{"text": q}] for q in QUANTITIES.keys()]
    keyboard.append([{"text": "🔙 بازگشت"}])
    return {"keyboard": keyboard, "resize_keyboard": True}

def build_yes_no_keyboard():
    keyboard = [
        [{"text": "✅ بله، ارسال کن"}],
        [{"text": "❌ نه، خودم می‌گیرم"}],
        [{"text": "🔙 بازگشت"}]
    ]
    return {"keyboard": keyboard, "resize_keyboard": True}

def build_confirmation_keyboard():
    keyboard = [
        [{"text": "✅ ثبت سفارش"}],
        [{"text": "🔙 بازگشت"}]
    ]
    return {"keyboard": keyboard, "resize_keyboard": True}

def get_main_menu_keyboard():
    keyboard = [[{"text": "🛍️ ثبت سفارش جدید"}]]
    return {"keyboard": keyboard, "resize_keyboard": True}

def remove_keyboard():
    """کیبورد را حذف می‌کند (برای ورود متن)"""
    return {"remove_keyboard": True}

# ========== محاسبه قیمت ==========
def calculate_price(product_price, quantity_text):
    """قیمت نهایی را بر اساس وزن محاسبه می‌کند"""
    weight = QUANTITIES.get(quantity_text, 0)
    return int(product_price * weight)

# ========== پردازش پیام‌ها ==========
def bot_loop():
    print("بات روشن شد... در حال گوش دادن به پیام‌ها 🚀")
    last_update_id = 0

    while True:
        try:
            updates = get_updates(last_update_id + 1)
            if "result" in updates and updates["result"]:
                for update in updates["result"]:
                    last_update_id = update["update_id"]
                    if "message" in update:
                        message = update["message"]
                        chat_id = message["from"]["id"]
                        text = message.get("text", "")

                        # ===== شروع =====
                        if text == "/start" or text == "🛍️ ثبت سفارش جدید":
                            if NEXT_PRODUCTION_DATE:
                                welcome = (
                                    f"🎉 خیلی خوشحالیم که اکسیر پروتئین رو انتخاب کردید!\n\n"
                                    f"📅 تاریخ تولید بعدی: {NEXT_PRODUCTION_DATE}\n"
                                    f"لطفاً سفارش خود را برای همین تاریخ ثبت کنید.\n\n"
                                    f"برای شروع، یکی از محصولات زیر را انتخاب کنید:"
                                )
                            else:
                                welcome = (
                                    f"🎉 خیلی خوشحالیم که اکسیر پروتئین رو انتخاب کردید!\n\n"
                                    f"⛔ متأسفانه این هفته تولید نداریم.\n"
                                    f"لطفاً هفته آینده مجدداً تشریف بیاورید."
                                )
                                send_message(chat_id, welcome, get_main_menu_keyboard())
                                continue

                            user_data[chat_id] = {"state": "PRODUCT_SELECTION"}
                            send_message(chat_id, welcome, build_product_keyboard())
                            continue

                        # ===== مدیریت بازگشت =====
                        if text == "🔙 بازگشت":
                            prev = user_data.get(chat_id, {}).get("prev_state")
                            if prev:
                                user_data[chat_id]["state"] = prev
                                state = prev
                            else:
                                send_message(chat_id, "شما در ابتدای مسیر هستید.", get_main_menu_keyboard())
                                continue
                        else:
                            state = user_data.get(chat_id, {}).get("state")

                        # ===== مرحله انتخاب محصول =====
                        if state == "PRODUCT_SELECTION":
                            if text in PRODUCTS:
                                user_data[chat_id]["product"] = text
                                user_data[chat_id]["price_per_kg"] = PRODUCTS[text]
                                user_data[chat_id]["prev_state"] = "PRODUCT_SELECTION"
                                user_data[chat_id]["state"] = "QUANTITY_SELECTION"
                                send_message(chat_id, f"✅ محصول {text} انتخاب شد.\n\nحالا مقدار مورد نیاز را انتخاب کنید:", build_quantity_keyboard())
                            else:
                                send_message(chat_id, "لطفاً یکی از محصولات موجود را انتخاب کنید.", build_product_keyboard())

                        # ===== مرحله انتخاب وزن =====
                        elif state == "QUANTITY_SELECTION":
                            if text in QUANTITIES:
                                user_data[chat_id]["quantity_text"] = text
                                user_data[chat_id]["quantity_kg"] = QUANTITIES[text]
                                # محاسبه قیمت نهایی
                                price = calculate_price(
                                    user_data[chat_id]["price_per_kg"],
                                    text
                                )
                                user_data[chat_id]["final_price"] = price

                                user_data[chat_id]["prev_state"] = "QUANTITY_SELECTION"
                                user_data[chat_id]["state"] = "NAME"

                                # حذف کیبورد وزن و نمایش پیام ورود نام
                                send_message(
                                    chat_id,
                                    f"✅ مقدار {text} با قیمت {price:,} تومان ثبت شد.\n\n"
                                    f"لطفاً نام و نام خانوادگی خود را وارد کنید:",
                                    remove_keyboard()
                                )
                            else:
                                send_message(chat_id, "لطفاً یکی از مقادیر موجود را انتخاب کنید.", build_quantity_keyboard())

                        # ===== مرحله دریافت نام =====
                        elif state == "NAME":
                            if len(text) > 2:
                                user_data[chat_id]["name"] = text
                                user_data[chat_id]["prev_state"] = "NAME"
                                user_data[chat_id]["state"] = "PHONE"
                                send_message(chat_id, f"✅ نام شما ثبت شد.\n\nحالا شماره تماس خود را وارد کنید:", remove_keyboard())
                            else:
                                send_message(chat_id, "نام باید حداقل ۳ حرف باشد. لطفاً دوباره وارد کنید:")

                        # ===== مرحله دریافت شماره =====
                        elif state == "PHONE":
                            user_data[chat_id]["phone"] = text
                            user_data[chat_id]["prev_state"] = "PHONE"
                            user_data[chat_id]["state"] = "DELIVERY_OPTION"
                            send_message(chat_id, f"✅ شماره تماس ثبت شد.\n\nآیا مایلید سفارش برای شما ارسال شود؟", build_yes_no_keyboard())

                        # ===== مرحله انتخاب ارسال =====
                        elif state == "DELIVERY_OPTION":
                            if text == "✅ بله، ارسال کن":
                                user_data[chat_id]["delivery"] = True
                                user_data[chat_id]["prev_state"] = "DELIVERY_OPTION"
                                user_data[chat_id]["state"] = "ADDRESS"
                                send_message(chat_id, "لطفاً آدرس کامل خود را وارد کنید:", remove_keyboard())
                            elif text == "❌ نه، خودم می‌گیرم":
                                user_data[chat_id]["delivery"] = False
                                user_data[chat_id]["prev_state"] = "DELIVERY_OPTION"
                                user_data[chat_id]["state"] = "CONFIRMATION"
                                show_confirmation(chat_id)
                            else:
                                send_message(chat_id, "لطفاً یکی از گزینه‌ها را انتخاب کنید.", build_yes_no_keyboard())

                        # ===== مرحله دریافت آدرس =====
                        elif state == "ADDRESS":
                            if len(text) > 5:
                                user_data[chat_id]["address"] = text
                                user_data[chat_id]["prev_state"] = "ADDRESS"
                                user_data[chat_id]["state"] = "POSTAL_CODE"
                                send_message(chat_id, "✅ آدرس ثبت شد.\n\nحالا کد پستی ۱۰ رقمی خود را وارد کنید:", remove_keyboard())
                            else:
                                send_message(chat_id, "آدرس باید حداقل ۵ حرف باشد. لطفاً دوباره وارد کنید:")

                        # ===== مرحله دریافت کد پستی =====
                        elif state == "POSTAL_CODE":
                            if len(text) >= 5:
                                user_data[chat_id]["postal_code"] = text
                                user_data[chat_id]["prev_state"] = "POSTAL_CODE"
                                user_data[chat_id]["state"] = "CONFIRMATION"
                                show_confirmation(chat_id)
                            else:
                                send_message(chat_id, "کد پستی باید حداقل ۵ رقم باشد. لطفاً دوباره وارد کنید:")

                        # ===== مرحله تأیید نهایی =====
                        elif state == "CONFIRMATION":
                            if text == "✅ ثبت سفارش":
                                finalize_order(chat_id)
                            elif text == "🔙 بازگشت":
                                prev = user_data[chat_id].get("prev_state", "PRODUCT_SELECTION")
                                user_data[chat_id]["state"] = prev
                                # بازگرداندن کیبورد مناسب
                                if prev == "PRODUCT_SELECTION":
                                    send_message(chat_id, "محصول جدید انتخاب کنید:", build_product_keyboard())
                                elif prev == "QUANTITY_SELECTION":
                                    send_message(chat_id, "مقدار جدید انتخاب کنید:", build_quantity_keyboard())
                                elif prev == "NAME":
                                    send_message(chat_id, "نام خود را دوباره وارد کنید:", remove_keyboard())
                                elif prev == "PHONE":
                                    send_message(chat_id, "شماره تماس خود را دوباره وارد کنید:", remove_keyboard())
                                elif prev == "DELIVERY_OPTION":
                                    send_message(chat_id, "آیا مایلید سفارش ارسال شود؟", build_yes_no_keyboard())
                                elif prev == "ADDRESS":
                                    send_message(chat_id, "آدرس را دوباره وارد کنید:", remove_keyboard())
                                elif prev == "POSTAL_CODE":
                                    send_message(chat_id, "کد پستی را دوباره وارد کنید:", remove_keyboard())
                            else:
                                send_message(chat_id, "لطفاً دکمه ثبت سفارش را بزنید.", build_confirmation_keyboard())

                        # ===== حالت پیش‌فرض =====
                        else:
                            send_message(chat_id, "برای ثبت سفارش جدید، روی دکمه زیر کلیک کنید:", get_main_menu_keyboard())

            time.sleep(0.5)
        except Exception as e:
            print(f"خطا در حلقه بات: {e}")
            time.sleep(3)

# ========== نمایش خلاصه سفارش ==========
def show_confirmation(chat_id):
    data = user_data[chat_id]
    tracking = generate_tracking_code()
    user_data[chat_id]["tracking"] = tracking

    msg = (
        f"📋 خلاصه سفارش شما:\n\n"
        f"🆔 کد پیگیری: {tracking}\n"
        f"🛒 محصول: {data['product']}\n"
        f"⚖️ مقدار: {data['quantity_text']}\n"
        f"💰 قیمت نهایی: {data['final_price']:,} تومان\n"
        f"👤 نام: {data['name']}\n"
        f"📞 تلفن: {data['phone']}\n"
    )
    if data.get("delivery"):
        msg += (
            f"🚚 ارسال: بله\n"
            f"📍 آدرس: {data.get('address', 'نامشخص')}\n"
            f"📮 کدپستی: {data.get('postal_code', 'نامشخص')}\n"
        )
    else:
        msg += "🚚 ارسال: نه (تحویل حضوری)\n"

    msg += "\n✅ لطفاً برای ثبت نهایی سفارش، دکمه زیر را بزنید."
    send_message(chat_id, msg, build_confirmation_keyboard())

# ========== ثبت نهایی سفارش ==========
def finalize_order(chat_id):
    data = user_data[chat_id]

    order_msg = (
        f"📦 سفارش جدید ثبت شد!\n\n"
        f"🆔 کد پیگیری: {data['tracking']}\n"
        f"🛒 محصول: {data['product']}\n"
        f"⚖️ مقدار: {data['quantity_text']}\n"
        f"💰 قیمت نهایی: {data['final_price']:,} تومان\n"
        f"👤 نام: {data['name']}\n"
        f"📞 تلفن: {data['phone']}\n"
    )
    if data.get("delivery"):
        order_msg += (
            f"🚚 ارسال: بله\n"
            f"📍 آدرس: {data.get('address', 'نامشخص')}\n"
            f"📮 کدپستی: {data.get('postal_code', 'نامشخص')}\n"
        )
    else:
        order_msg += "🚚 ارسال: نه (تحویل حضوری)\n"

    order_msg += f"\n👤 سفارش‌دهنده: @{chat_id}"

    send_message(ADMIN_ID, order_msg)
    send_message(chat_id,
        f"✅ سفارش شما با موفقیت ثبت شد!\n"
        f"🆔 کد پیگیری: {data['tracking']}\n"
        f"📞 در صورت نیاز با شما تماس خواهیم گرفت.\n\n"
        f"🙏 سپاس از انتخاب شما"
    )

    del user_data[chat_id]
    send_message(chat_id, "برای ثبت سفارش جدید، روی دکمه زیر کلیک کنید:", get_main_menu_keyboard())

# ========== اجرا ==========
if __name__ == "__main__":
    bot_loop()