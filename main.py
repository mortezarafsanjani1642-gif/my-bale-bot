import requests
import time
import os
import random
import string
import json
from flask import Flask
from threading import Thread

# ========== تنظیمات ==========
PRODUCTS = {
    "سوسیس آلمانی": 1000,
    "سوسیس بلغاری": 1000,
    "ناگت مرغ": 1000,
    "ناگت بوقلمون": 1000
}

NEXT_PRODUCTION_DATE = "۱۵ تیر ۱۴۰۴"

QUANTITIES = {
    "نیم کیلو": 0.5,
    "یک کیلو": 1.0,
    "یک کیلو و نیم": 1.5,
    "دو کیلو": 2.0,
    "دو کیلو و نیم": 2.5,
    "سه کیلو": 3.0
}

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
API_URL = f"https://tapi.bale.ai/bot{TOKEN}"

# ========== ذخیره‌سازی ==========
user_data = {}  # وضعیت موقت کاربران
orders = {}     # دیکشنری سفارش‌ها: {tracking_code: order_data}

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

def calculate_price(product_price, quantity_text):
    weight = QUANTITIES.get(quantity_text, 0)
    return int(product_price * weight)

def remove_keyboard():
    return {"remove_keyboard": True}

def build_main_menu():
    """منوی اصلی با سه دکمه"""
    keyboard = [
        [{"text": "🛍️ ثبت سفارش جدید"}],
        [{"text": "✏️ تغییر سفارش"}],
        [{"text": "🔍 پیگیری سفارش"}]
    ]
    return {"keyboard": keyboard, "resize_keyboard": True}

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

def build_edit_cancel_keyboard(tracking):
    """کیبورد ویرایش و لغو سفارش"""
    keyboard = [
        [{"text": f"✏️ ویرایش سفارش {tracking}"}],
        [{"text": f"❌ لغو سفارش {tracking}"}],
        [{"text": "🔙 بازگشت"}]
    ]
    return {"keyboard": keyboard, "resize_keyboard": True}

def build_admin_panel():
    """پنل مدیریتی برای ادمین"""
    keyboard = [
        [{"text": "📋 لیست همه سفارش‌ها"}],
        [{"text": "🔄 تغییر وضعیت سفارش"}],
        [{"text": "🚚 تحویل سفارش"}]
    ]
    return {"keyboard": keyboard, "resize_keyboard": True}

def get_order_status_text(status):
    """تبدیل وضعیت به متن فارسی"""
    status_map = {
        "registered": "📝 ثبت شده و در انتظار تولید",
        "in_production": "🏭 در حال تولید",
        "delivered": "✅ تحویل داده شده"
    }
    return status_map.get(status, "نامشخص")

# ========== توابع اصلی ==========
def show_order_summary(chat_id, tracking):
    """نمایش خلاصه یک سفارش با وضعیت"""
    order = orders.get(tracking)
    if not order:
        send_message(chat_id, "❌ سفارشی با این کد پیدا نشد.")
        return False
    
    msg = (
        f"📋 اطلاعات سفارش:\n\n"
        f"🆔 کد پیگیری: {tracking}\n"
        f"📊 وضعیت: {get_order_status_text(order['status'])}\n"
        f"🛒 محصول: {order['product']}\n"
        f"⚖️ مقدار: {order['quantity_text']}\n"
        f"💰 قیمت: {order['final_price']:,} تومان\n"
        f"👤 نام: {order['name']}\n"
        f"📞 تلفن: {order['phone']}\n"
    )
    if order.get("delivery"):
        msg += (
            f"🚚 ارسال: بله\n"
            f"📍 آدرس: {order.get('address', 'نامشخص')}\n"
            f"📮 کدپستی: {order.get('postal_code', 'نامشخص')}\n"
        )
    else:
        msg += "🚚 ارسال: نه (تحویل حضوری)\n"
    
    send_message(chat_id, msg)
    return True

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

                        # ===== پنل ادمین (فقط برای ادمین) =====
                        if str(chat_id) == ADMIN_ID and text in ["📋 لیست همه سفارش‌ها", "🔄 تغییر وضعیت سفارش", "🚚 تحویل سفارش"]:
                            handle_admin_command(chat_id, text)
                            continue

                        # ===== منوی اصلی =====
                        if text == "/start":
                            send_message(chat_id, 
                                "🎉 به ربات سفارش‌گیری اکسیر پروتئین خوش آمدید!\n"
                                "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                                build_main_menu()
                            )
                            continue

                        if text == "🛍️ ثبت سفارش جدید":
                            start_new_order(chat_id)
                            continue

                        if text == "✏️ تغییر سفارش":
                            send_message(chat_id, "🔑 لطفاً کد پیگیری سفارش خود را وارد کنید:", remove_keyboard())
                            user_data[chat_id] = {"state": "EDIT_GET_TRACKING"}
                            continue

                        if text == "🔍 پیگیری سفارش":
                            send_message(chat_id, "🔑 لطفاً کد پیگیری سفارش خود را وارد کنید:", remove_keyboard())
                            user_data[chat_id] = {"state": "TRACK_GET_TRACKING"}
                            continue

                        # ===== مدیریت بازگشت =====
                        if text == "🔙 بازگشت":
                            handle_back(chat_id)
                            continue

                        # ===== پردازش بر اساس وضعیت =====
                        state = user_data.get(chat_id, {}).get("state")
                        
                        # ---- ثبت سفارش جدید ----
                        if state == "PRODUCT_SELECTION":
                            handle_product_selection(chat_id, text)
                        elif state == "QUANTITY_SELECTION":
                            handle_quantity_selection(chat_id, text)
                        elif state == "NAME":
                            handle_name(chat_id, text)
                        elif state == "PHONE":
                            handle_phone(chat_id, text)
                        elif state == "DELIVERY_OPTION":
                            handle_delivery_option(chat_id, text)
                        elif state == "ADDRESS":
                            handle_address(chat_id, text)
                        elif state == "POSTAL_CODE":
                            handle_postal_code(chat_id, text)
                        elif state == "CONFIRMATION":
                            handle_confirmation(chat_id, text)
                        
                        # ---- تغییر سفارش ----
                        elif state == "EDIT_GET_TRACKING":
                            tracking = text.strip()
                            if tracking in orders:
                                user_data[chat_id]["edit_tracking"] = tracking
                                user_data[chat_id]["state"] = "EDIT_SHOW_OPTIONS"
                                send_message(chat_id, 
                                    f"✅ سفارش با کد {tracking} پیدا شد.\n"
                                    f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                                    build_edit_cancel_keyboard(tracking)
                                )
                            else:
                                send_message(chat_id, "❌ کد پیگیری نامعتبر است. لطفاً دوباره وارد کنید یا /start را بزنید.")
                        
                        elif state == "EDIT_SHOW_OPTIONS":
                            if text.startswith("✏️ ویرایش سفارش"):
                                tracking = text.split()[-1]
                                if tracking in orders:
                                    # شروع مجدد فرایند ثبت با اطلاعات قبلی
                                    order = orders[tracking]
                                    user_data[chat_id] = {
                                        "state": "PRODUCT_SELECTION",
                                        "edit_mode": True,
                                        "edit_tracking": tracking,
                                        "product": order["product"],
                                        "price_per_kg": PRODUCTS[order["product"]]
                                    }
                                    send_message(chat_id, 
                                        f"🔄 در حال ویرایش سفارش {tracking}\n"
                                        f"محصول فعلی: {order['product']}\n"
                                        f"لطفاً محصول جدید را انتخاب کنید یا همان را تأیید کنید:",
                                        build_product_keyboard()
                                    )
                                else:
                                    send_message(chat_id, "❌ خطا در ویرایش. لطفاً مجدداً تلاش کنید.")
                            
                            elif text.startswith("❌ لغو سفارش"):
                                tracking = text.split()[-1]
                                if tracking in orders:
                                    user_data[chat_id]["cancel_tracking"] = tracking
                                    user_data[chat_id]["state"] = "CANCEL_CONFIRM"
                                    keyboard = {"keyboard": [[{"text": "✅ بله، لغو کن"}, {"text": "❌ نه، منصرف شدم"}]], "resize_keyboard": True}
                                    send_message(chat_id, f"⚠️ آیا مطمئن هستید که می‌خواهید سفارش {tracking} را لغو کنید؟", keyboard)
                                else:
                                    send_message(chat_id, "❌ کد پیگیری نامعتبر است.")
                            
                            elif text == "🔙 بازگشت":
                                send_message(chat_id, "به منوی اصلی بازگشتید.", build_main_menu())
                                user_data.pop(chat_id, None)
                            else:
                                send_message(chat_id, "لطفاً یکی از گزینه‌ها را انتخاب کنید.", build_edit_cancel_keyboard(user_data[chat_id].get("edit_tracking", "")))
                        
                        elif state == "CANCEL_CONFIRM":
                            if text == "✅ بله، لغو کن":
                                tracking = user_data[chat_id].get("cancel_tracking")
                                if tracking and tracking in orders:
                                    order = orders.pop(tracking)
                                    send_message(chat_id, f"✅ سفارش {tracking} با موفقیت لغو شد.")
                                    send_message(ADMIN_ID, f"⚠️ کاربر {order['name']} سفارش {tracking} را لغو کرد.")
                                    send_message(chat_id, "به منوی اصلی بازگشتید.", build_main_menu())
                                    user_data.pop(chat_id, None)
                                else:
                                    send_message(chat_id, "❌ خطا در لغو سفارش.")
                            elif text == "❌ نه، منصرف شدم":
                                send_message(chat_id, "✅ لغو سفارش کنسل شد. به منوی اصلی بازگشتید.", build_main_menu())
                                user_data.pop(chat_id, None)
                            else:
                                send_message(chat_id, "لطفاً یکی از گزینه‌ها را انتخاب کنید.")
                        
                        # ---- پیگیری سفارش ----
                        elif state == "TRACK_GET_TRACKING":
                            tracking = text.strip()
                            if tracking in orders:
                                show_order_summary(chat_id, tracking)
                                send_message(chat_id, "به منوی اصلی بازگشتید.", build_main_menu())
                                user_data.pop(chat_id, None)
                            else:
                                send_message(chat_id, "❌ کد پیگیری نامعتبر است. لطفاً دوباره وارد کنید یا /start را بزنید.")
                        
                        # ===== حالت پیش‌فرض =====
                        else:
                            if text not in ["/start", "🛍️ ثبت سفارش جدید", "✏️ تغییر سفارش", "🔍 پیگیری سفارش", "🔙 بازگشت"]:
                                send_message(chat_id, "لطفاً از دکمه‌های منو استفاده کنید.", build_main_menu())

            time.sleep(0.5)
        except Exception as e:
            print(f"خطا در حلقه بات: {e}")
            time.sleep(3)

# ========== توابع مدیریت مراحل ==========
def start_new_order(chat_id):
    user_data[chat_id] = {"state": "PRODUCT_SELECTION"}
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
        send_message(chat_id, welcome, build_main_menu())
        return
    send_message(chat_id, welcome, build_product_keyboard())

def handle_product_selection(chat_id, text):
    if text in PRODUCTS:
        user_data[chat_id]["product"] = text
        user_data[chat_id]["price_per_kg"] = PRODUCTS[text]
        user_data[chat_id]["prev_state"] = "PRODUCT_SELECTION"
        user_data[chat_id]["state"] = "QUANTITY_SELECTION"
        send_message(chat_id, f"✅ محصول {text} انتخاب شد.\n\nحالا مقدار مورد نیاز را انتخاب کنید:", build_quantity_keyboard())
    else:
        send_message(chat_id, "لطفاً یکی از محصولات موجود را انتخاب کنید.", build_product_keyboard())

def handle_quantity_selection(chat_id, text):
    if text in QUANTITIES:
        user_data[chat_id]["quantity_text"] = text
        user_data[chat_id]["quantity_kg"] = QUANTITIES[text]
        price = calculate_price(user_data[chat_id]["price_per_kg"], text)
        user_data[chat_id]["final_price"] = price
        user_data[chat_id]["prev_state"] = "QUANTITY_SELECTION"
        user_data[chat_id]["state"] = "NAME"
        send_message(
            chat_id,
            f"✅ مقدار {text} با قیمت {price:,} تومان ثبت شد.\n\n"
            f"لطفاً نام و نام خانوادگی خود را وارد کنید:",
            remove_keyboard()
        )
    else:
        send_message(chat_id, "لطفاً یکی از مقادیر موجود را انتخاب کنید.", build_quantity_keyboard())

def handle_name(chat_id, text):
    if len(text) > 2:
        user_data[chat_id]["name"] = text
        user_data[chat_id]["prev_state"] = "NAME"
        user_data[chat_id]["state"] = "PHONE"
        send_message(chat_id, f"✅ نام شما ثبت شد.\n\nحالا شماره تماس خود را وارد کنید:", remove_keyboard())
    else:
        send_message(chat_id, "نام باید حداقل ۳ حرف باشد. لطفاً دوباره وارد کنید:")

def handle_phone(chat_id, text):
    user_data[chat_id]["phone"] = text
    user_data[chat_id]["prev_state"] = "PHONE"
    user_data[chat_id]["state"] = "DELIVERY_OPTION"
    send_message(chat_id, f"✅ شماره تماس ثبت شد.\n\nآیا مایلید سفارش برای شما ارسال شود؟", build_yes_no_keyboard())

def handle_delivery_option(chat_id, text):
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

def handle_address(chat_id, text):
    if len(text) > 5:
        user_data[chat_id]["address"] = text
        user_data[chat_id]["prev_state"] = "ADDRESS"
        user_data[chat_id]["state"] = "POSTAL_CODE"
        send_message(chat_id, "✅ آدرس ثبت شد.\n\nحالا کد پستی ۱۰ رقمی خود را وارد کنید:", remove_keyboard())
    else:
        send_message(chat_id, "آدرس باید حداقل ۵ حرف باشد. لطفاً دوباره وارد کنید:")

def handle_postal_code(chat_id, text):
    if len(text) >= 5:
        user_data[chat_id]["postal_code"] = text
        user_data[chat_id]["prev_state"] = "POSTAL_CODE"
        user_data[chat_id]["state"] = "CONFIRMATION"
        show_confirmation(chat_id)
    else:
        send_message(chat_id, "کد پستی باید حداقل ۵ رقم باشد. لطفاً دوباره وارد کنید:")

def handle_confirmation(chat_id, text):
    if text == "✅ ثبت سفارش":
        finalize_order(chat_id)
    elif text == "🔙 بازگشت":
        prev = user_data[chat_id].get("prev_state", "PRODUCT_SELECTION")
        user_data[chat_id]["state"] = prev
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

def handle_back(chat_id):
    state = user_data.get(chat_id, {}).get("state")
    if state in ["PRODUCT_SELECTION", "QUANTITY_SELECTION", "NAME", "PHONE", "DELIVERY_OPTION", "ADDRESS", "POSTAL_CODE", "CONFIRMATION"]:
        prev = user_data[chat_id].get("prev_state")
        if prev:
            user_data[chat_id]["state"] = prev
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
            send_message(chat_id, "به منوی اصلی بازگشتید.", build_main_menu())
            user_data.pop(chat_id, None)
    else:
        send_message(chat_id, "به منوی اصلی بازگشتید.", build_main_menu())
        user_data.pop(chat_id, None)

# ========== نمایش و ثبت نهایی ==========
def show_confirmation(chat_id):
    data = user_data[chat_id]
    tracking = generate_tracking_code()
    data["tracking"] = tracking

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

def finalize_order(chat_id):
    data = user_data[chat_id]
    tracking = data.get("tracking", generate_tracking_code())
    data["tracking"] = tracking
    data["status"] = "registered"  # وضعیت اولیه

    # ذخیره سفارش
    orders[tracking] = data.copy()

    # ارسال به ادمین
    order_msg = (
        f"📦 سفارش جدید ثبت شد!\n\n"
        f"🆔 کد پیگیری: {tracking}\n"
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
    
    # پیام به کاربر
    send_message(chat_id,
        f"✅ سفارش شما با موفقیت ثبت شد!\n"
        f"🆔 کد پیگیری: {tracking}\n"
        f"📞 در صورت نیاز با شما تماس خواهیم گرفت.\n\n"
        f"🙏 سپاس از انتخاب شما"
    )

    # پاک کردن اطلاعات موقت
    user_data.pop(chat_id, None)
    
    # نمایش منوی اصلی با دکمه‌ها
    send_message(chat_id, "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", build_main_menu())

# ========== توابع مدیریت ادمین ==========
def handle_admin_command(chat_id, command):
    if command == "📋 لیست همه سفارش‌ها":
        if not orders:
            send_message(chat_id, "📭 هیچ سفارشی ثبت نشده است.", build_admin_panel())
            return
        msg = "📋 لیست سفارش‌ها:\n\n"
        for tracking, order in orders.items():
            msg += (
                f"🆔 {tracking} | {order['name']} | "
                f"{order['product']} | {get_order_status_text(order['status'])}\n"
            )
        send_message(chat_id, msg, build_admin_panel())
    
    elif command == "🔄 تغییر وضعیت سفارش":
        send_message(chat_id, 
            "🔑 لطفاً کد پیگیری سفارش را وارد کنید.\n"
            "سپس وضعیت جدید را انتخاب کنید.",
            remove_keyboard()
        )
        user_data[chat_id] = {"state": "ADMIN_CHANGE_STATUS_GET_TRACKING"}
    
    elif command == "🚚 تحویل سفارش":
        send_message(chat_id, 
            "🔑 لطفاً کد پیگیری سفارش را وارد کنید تا وضعیت آن به 'تحویل داده شده' تغییر کند.",
            remove_keyboard()
        )
        user_data[chat_id] = {"state": "ADMIN_DELIVER_GET_TRACKING"}

def handle_admin_status_change(chat_id, text):
    state = user_data.get(chat_id, {}).get("state")
    if state == "ADMIN_CHANGE_STATUS_GET_TRACKING":
        tracking = text.strip()
        if tracking in orders:
            user_data[chat_id]["admin_tracking"] = tracking
            user_data[chat_id]["state"] = "ADMIN_CHANGE_STATUS_SELECT"
            keyboard = {"keyboard": [
                [{"text": "🏭 در حال تولید"}],
                [{"text": "✅ تحویل داده شده"}],
                [{"text": "🔙 بازگشت"}]
            ], "resize_keyboard": True}
            send_message(chat_id, f"وضعیت فعلی: {get_order_status_text(orders[tracking]['status'])}\nوضعیت جدید را انتخاب کنید:", keyboard)
        else:
            send_message(chat_id, "❌ کد پیگیری نامعتبر است.")
            user_data.pop(chat_id, None)
    
    elif state == "ADMIN_CHANGE_STATUS_SELECT":
        tracking = user_data[chat_id].get("admin_tracking")
        if tracking and tracking in orders:
            if text == "🏭 در حال تولید":
                orders[tracking]["status"] = "in_production"
                send_message(chat_id, f"✅ وضعیت سفارش {tracking} به 'در حال تولید' تغییر کرد.", build_admin_panel())
                send_message(int(ADMIN_ID), f"🔔 وضعیت سفارش {tracking} به 'در حال تولید' تغییر یافت.")  # اطلاع به ادمین
                user_data.pop(chat_id, None)
            elif text == "✅ تحویل داده شده":
                orders[tracking]["status"] = "delivered"
                send_message(chat_id, f"✅ وضعیت سفارش {tracking} به 'تحویل داده شده' تغییر کرد.", build_admin_panel())
                send_message(int(ADMIN_ID), f"🔔 وضعیت سفارش {tracking} به 'تحویل داده شده' تغییر یافت.")
                user_data.pop(chat_id, None)
            elif text == "🔙 بازگشت":
                send_message(chat_id, "به پنل مدیریت بازگشتید.", build_admin_panel())
                user_data.pop(chat_id, None)
            else:
                send_message(chat_id, "لطفاً یکی از گزینه‌ها را انتخاب کنید.")
        else:
            send_message(chat_id, "❌ خطا در تغییر وضعیت.")

def handle_admin_deliver(chat_id, text):
    tracking = text.strip()
    if tracking in orders:
        orders[tracking]["status"] = "delivered"
        send_message(chat_id, f"✅ سفارش {tracking} به 'تحویل داده شده' تغییر کرد.", build_admin_panel())
        send_message(int(ADMIN_ID), f"🔔 سفارش {tracking} تحویل داده شد.")
        user_data.pop(chat_id, None)
    else:
        send_message(chat_id, "❌ کد پیگیری نامعتبر است.")
        user_data.pop(chat_id, None)

# ========== اجرا ==========
if __name__ == "__main__":
    bot_loop()