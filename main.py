import requests
import time
import os
import random
import string
from flask import Flask
from threading import Thread

# ========== تنظیمات ==========
PRODUCTS = {
    "سوسیس آلمانی": {"min": 1500000, "max": 1700000},
    "سوسیس بلغاری": {"min": 1500000, "max": 1700000},
    "ناگت مرغ": {"min": 1500000, "max": 1700000},
    "ناگت بوقلمون": {"min": 1500000, "max": 1700000}
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

user_data = {}
orders = {}

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running! 🚀"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ========== توابع کمکی ==========
def normalize_persian_numbers(text):
    persian_map = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }
    return ''.join(persian_map.get(char, char) for char in text)

def send_message(chat_id, text, keyboard=None):
    payload = {"chat_id": chat_id, "text": text}
    if keyboard:
        payload["reply_markup"] = keyboard
    try:
        r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        print(f"Send status: {r.status_code}")
    except Exception as e:
        print(f"Send error: {e}")

def send_photo(chat_id, photo_file_id, caption=None, keyboard=None):
    """ارسال تصویر با استفاده از file_id"""
    payload = {"chat_id": chat_id, "photo": photo_file_id}
    if caption:
        payload["caption"] = caption
    if keyboard:
        payload["reply_markup"] = keyboard
    try:
        r = requests.post(f"{API_URL}/sendPhoto", json=payload, timeout=30)
        print(f"Send photo status: {r.status_code}")
    except Exception as e:
        print(f"Send photo error: {e}")

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

def calculate_price_range(product_prices, quantity_text):
    weight = QUANTITIES.get(quantity_text, 0)
    min_price = int(product_prices['min'] * weight)
    max_price = int(product_prices['max'] * weight)
    return min_price, max_price

def remove_keyboard():
    return {"remove_keyboard": True}

def get_order_status_text(status):
    status_map = {
        "registered": "📝 ثبت اولیه سفارش و در انتظار تولید",
        "pending_payment": "🏭 تولید محصول و در انتظار ارسال رسید پرداخت",
        "payment_verified": "✅ رسید پرداخت ارسال و تایید شده",
        "payment_rejected": "❌ رد رسید پرداخت"
    }
    return status_map.get(status, "نامشخص")

# ========== کیبوردها ==========
def build_main_menu():
    keyboard = [
        [{"text": "🛍️ ثبت سفارش جدید"}],
        [{"text": "💰 ارسال رسید پرداخت"}],
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
    keyboard = [
        [{"text": f"✏️ ویرایش سفارش {tracking}"}],
        [{"text": f"❌ لغو سفارش {tracking}"}],
        [{"text": "🔙 بازگشت"}]
    ]
    return {"keyboard": keyboard, "resize_keyboard": True}

def build_admin_panel():
    keyboard = [
        [{"text": "📋 سفارش‌های باز (ثبت اولیه)"}],
        [{"text": "💰 سفارش‌های پرداخت نشده"}],
        [{"text": "📋 لیست همه سفارش‌ها"}]
    ]
    return {"keyboard": keyboard, "resize_keyboard": True}

def build_admin_confirm_keyboard(tracking):
    """کیبورد تایید/رد برای ادمین"""
    keyboard = [
        [{"text": f"✅ تایید رسید {tracking}"}],
        [{"text": f"❌ رد رسید {tracking}"}],
        [{"text": "🔙 بازگشت"}]
    ]
    return {"keyboard": keyboard, "resize_keyboard": True}

# ========== مدیریت ثبت سفارش ==========
def start_new_order(chat_id):
    user_data[chat_id] = {
        "state": "PRODUCT_SELECTION",
        "items": [],
        "total_price": 0
    }
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
        user_data[chat_id]["current_product"] = text
        user_data[chat_id]["current_prices"] = PRODUCTS[text]
        user_data[chat_id]["prev_state"] = "PRODUCT_SELECTION"
        user_data[chat_id]["state"] = "QUANTITY_SELECTION"
        send_message(chat_id, f"✅ {text} انتخاب شد.\n\nحالا مقدار مورد نیاز را انتخاب کنید:", build_quantity_keyboard())
    else:
        send_message(chat_id, "لطفاً یکی از محصولات موجود را انتخاب کنید.", build_product_keyboard())

def handle_quantity_selection(chat_id, text):
    if text in QUANTITIES:
        min_price, max_price = calculate_price_range(
            user_data[chat_id]["current_prices"], 
            text
        )
        price_range_text = f"{min_price:,} - {max_price:,} تومان"
        avg_price = (min_price + max_price) // 2
        item = {
            "product": user_data[chat_id]["current_product"],
            "quantity_text": text,
            "quantity_kg": QUANTITIES[text],
            "price_range": price_range_text,
            "avg_price": avg_price
        }
        user_data[chat_id]["items"].append(item)
        user_data[chat_id]["total_price"] += avg_price
        
        keyboard = {"keyboard": [
            [{"text": "✅ بله، محصول دیگر"}],
            [{"text": "❌ نه، ادامه ثبت سفارش"}],
            [{"text": "🔙 بازگشت"}]
        ], "resize_keyboard": True}
        send_message(
            chat_id,
            f"✅ {text} با حدود قیمت {price_range_text} به سبد خرید اضافه شد.\n\n"
            f"📦 سبد خرید شما: {len(user_data[chat_id]['items'])} محصول\n"
            f"💰 قیمت تقریبی کل: {user_data[chat_id]['total_price']:,} تومان\n\n"
            f"آیا محصول دیگری می‌خواهید اضافه کنید؟",
            keyboard
        )
        user_data[chat_id]["state"] = "ASK_MORE_ITEMS"
    else:
        send_message(chat_id, "لطفاً یکی از مقادیر موجود را انتخاب کنید.", build_quantity_keyboard())

def handle_ask_more_items(chat_id, text):
    if text == "✅ بله، محصول دیگر":
        user_data[chat_id]["state"] = "PRODUCT_SELECTION"
        user_data[chat_id]["prev_state"] = "ASK_MORE_ITEMS"
        send_message(chat_id, "محصول جدید را انتخاب کنید:", build_product_keyboard())
    elif text == "❌ نه، ادامه ثبت سفارش":
        user_data[chat_id]["state"] = "NAME"
        user_data[chat_id]["prev_state"] = "ASK_MORE_ITEMS"
        send_message(chat_id, "لطفاً نام و نام خانوادگی خود را وارد کنید:", remove_keyboard())
    elif text == "🔙 بازگشت":
        if user_data[chat_id]["items"]:
            removed = user_data[chat_id]["items"].pop()
            user_data[chat_id]["total_price"] -= removed["avg_price"]
            send_message(chat_id, f"✅ {removed['product']} با {removed['quantity_text']} از سبد خرید حذف شد.")
        if user_data[chat_id]["items"]:
            user_data[chat_id]["state"] = "ASK_MORE_ITEMS"
            keyboard = {"keyboard": [
                [{"text": "✅ بله، محصول دیگر"}],
                [{"text": "❌ نه، ادامه ثبت سفارش"}],
                [{"text": "🔙 بازگشت"}]
            ], "resize_keyboard": True}
            send_message(chat_id, f"سبد خرید شما {len(user_data[chat_id]['items'])} محصول دارد. آیا محصول دیگری می‌خواهید؟", keyboard)
        else:
            user_data[chat_id]["state"] = "PRODUCT_SELECTION"
            send_message(chat_id, "سبد خرید خالی شد. لطفاً یک محصول انتخاب کنید:", build_product_keyboard())
    else:
        send_message(chat_id, "لطفاً یکی از گزینه‌ها را انتخاب کنید.")

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
    if state in ["PRODUCT_SELECTION", "QUANTITY_SELECTION", "ASK_MORE_ITEMS", "NAME", "PHONE", "DELIVERY_OPTION", "ADDRESS", "POSTAL_CODE", "CONFIRMATION"]:
        prev = user_data[chat_id].get("prev_state")
        if prev:
            user_data[chat_id]["state"] = prev
            if prev == "PRODUCT_SELECTION":
                send_message(chat_id, "محصول جدید انتخاب کنید:", build_product_keyboard())
            elif prev == "QUANTITY_SELECTION":
                send_message(chat_id, "مقدار جدید انتخاب کنید:", build_quantity_keyboard())
            elif prev == "ASK_MORE_ITEMS":
                keyboard = {"keyboard": [
                    [{"text": "✅ بله، محصول دیگر"}],
                    [{"text": "❌ نه، ادامه ثبت سفارش"}],
                    [{"text": "🔙 بازگشت"}]
                ], "resize_keyboard": True}
                send_message(chat_id, "آیا محصول دیگری می‌خواهید اضافه کنید؟", keyboard)
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

def show_confirmation(chat_id):
    data = user_data[chat_id]
    tracking = generate_tracking_code()
    data["tracking"] = tracking

    msg = (
        f"📋 خلاصه سفارش شما:\n\n"
        f"🆔 کد پیگیری: {tracking}\n"
        f"🛒 محصولات:\n"
    )
    for item in data['items']:
        msg += f"  - {item['product']} | {item['quantity_text']} | حدود قیمت: {item['price_range']}\n"
    msg += f"\n💰 قیمت تقریبی کل: {data['total_price']:,} تومان\n"
    msg += f"👤 نام: {data['name']}\n"
    msg += f"📞 تلفن: {data['phone']}\n"
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
    data["chat_id"] = chat_id  # ذخیره chat_id برای اطلاع‌رسانی بعدی

    orders[tracking] = data.copy()

    order_msg = (
        f"📦 سفارش جدید ثبت شد!\n\n"
        f"🆔 کد پیگیری: {tracking}\n"
        f"🛒 محصولات:\n"
    )
    for item in data['items']:
        order_msg += f"  - {item['product']} | {item['quantity_text']} | حدود قیمت: {item['price_range']}\n"
    order_msg += f"\n💰 قیمت تقریبی کل: {data['total_price']:,} تومان\n"
    order_msg += f"👤 نام: {data['name']}\n"
    order_msg += f"📞 تلفن: {data['phone']}\n"
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
        f"🆔 کد پیگیری: {tracking}\n"
        f"📞 در صورت نیاز با شما تماس خواهیم گرفت.\n\n"
        f"🙏 سپاس از انتخاب شما"
    )

    user_data.pop(chat_id, None)
    send_message(chat_id, "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", build_main_menu())

# ========== مدیریت ارسال رسید پرداخت ==========
def handle_receipt_upload(chat_id, text):
    if text == "💰 ارسال رسید پرداخت":
        send_message(chat_id, "🔑 لطفاً کد پیگیری سفارش خود را وارد کنید:", remove_keyboard())
        user_data[chat_id] = {"state": "RECEIPT_GET_TRACKING"}
    else:
        send_message(chat_id, "لطفاً از دکمه‌های منو استفاده کنید.", build_main_menu())

def handle_receipt_tracking(chat_id, text):
    tracking = normalize_persian_numbers(text.strip())
    if tracking in orders:
        order = orders[tracking]
        if order['status'] == "pending_payment":
            user_data[chat_id] = {
                "state": "RECEIPT_UPLOAD",
                "tracking": tracking
            }
            send_message(chat_id, 
                f"✅ سفارش {tracking} پیدا شد.\n"
                f"لطفاً تصویر رسید پرداخت را آپلود کنید.\n"
                f"(از دکمه پیوست یا گالری گوشی استفاده کنید)",
                remove_keyboard()
            )
        else:
            status_text = get_order_status_text(order['status'])
            send_message(chat_id, 
                f"❌ سفارش {tracking} در وضعیت '{status_text}' است.\n"
                f"فقط سفارش‌های در انتظار رسید پرداخت (pending_payment) قابل ارسال هستند.",
                build_main_menu()
            )
            user_data.pop(chat_id, None)
    else:
        send_message(chat_id, "❌ کد پیگیری نامعتبر است. لطفاً دوباره وارد کنید یا /start را بزنید.")

# ========== مدیریت ادمین ==========
def handle_admin_command(chat_id, command):
    if command == "📋 سفارش‌های باز (ثبت اولیه)":
        # سفارش‌های با وضعیت registered
        open_orders = [t for t, o in orders.items() if o['status'] == 'registered']
        if not open_orders:
            send_message(chat_id, "📭 هیچ سفارش جدیدی برای تعیین قیمت وجود ندارد.", build_admin_panel())
            return
        
        msg = "📋 سفارش‌های جدید (ثبت اولیه) - برای تعیین قیمت:\n\n"
        for tracking in open_orders:
            order = orders[tracking]
            total = order.get('total_price', 0)
            msg += f"🆔 {tracking} | {order['name']} | قیمت تقریبی: {total:,} تومان\n"
        
        msg += "\n🔑 برای تعیین قیمت نهایی، کد پیگیری سفارش را وارد کنید."
        send_message(chat_id, msg, remove_keyboard())
        user_data[chat_id] = {"state": "ADMIN_SET_PRICE_GET_TRACKING"}
    
    elif command == "💰 سفارش‌های پرداخت نشده":
        # سفارش‌های با وضعیت pending_payment
        pending_orders = [t for t, o in orders.items() if o['status'] == 'pending_payment']
        if not pending_orders:
            send_message(chat_id, "📭 هیچ سفارشی در انتظار رسید پرداخت وجود ندارد.", build_admin_panel())
            return
        
        msg = "💰 سفارش‌های در انتظار رسید پرداخت:\n\n"
        for tracking in pending_orders:
            order = orders[tracking]
            final_price = order.get('final_price', 'نامشخص')
            msg += f"🆔 {tracking} | {order['name']} | قیمت نهایی: {final_price:,} تومان\n"
        send_message(chat_id, msg, build_admin_panel())
    
    elif command == "📋 لیست همه سفارش‌ها":
        if not orders:
            send_message(chat_id, "📭 هیچ سفارشی ثبت نشده است.", build_admin_panel())
            return
        msg = "📋 لیست همه سفارش‌ها:\n\n"
        for tracking, order in orders.items():
            status_emoji = {
                "registered": "📝",
                "pending_payment": "💰",
                "payment_verified": "✅",
                "payment_rejected": "❌"
            }.get(order['status'], "❓")
            msg += f"{status_emoji} {tracking} | {order['name']} | {get_order_status_text(order['status'])}\n"
        send_message(chat_id, msg, build_admin_panel())

def handle_admin_set_price(chat_id, text):
    """تعیین قیمت نهایی برای سفارش‌های registered"""
    state = user_data.get(chat_id, {}).get("state")
    if state == "ADMIN_SET_PRICE_GET_TRACKING":
        tracking = normalize_persian_numbers(text.strip())
        if tracking in orders and orders[tracking]['status'] == 'registered':
            user_data[chat_id]["admin_tracking"] = tracking
            user_data[chat_id]["state"] = "ADMIN_SET_PRICE_ENTER"
            send_message(chat_id, 
                f"🆔 سفارش: {tracking}\n"
                f"👤 نام: {orders[tracking]['name']}\n"
                f"💰 قیمت تقریبی فعلی: {orders[tracking].get('total_price', 0):,} تومان\n\n"
                f"🔢 لطفاً مبلغ نهایی (به تومان) را وارد کنید:",
                remove_keyboard()
            )
        else:
            send_message(chat_id, "❌ کد پیگیری نامعتبر یا سفارش در مرحله ثبت اولیه نیست.")
            user_data.pop(chat_id, None)
    
    elif state == "ADMIN_SET_PRICE_ENTER":
        try:
            final_price = int(normalize_persian_numbers(text.strip()))
            if final_price <= 0:
                send_message(chat_id, "❌ مبلغ باید بزرگتر از صفر باشد. دوباره وارد کنید:")
                return
            tracking = user_data[chat_id].get("admin_tracking")
            if tracking and tracking in orders:
                orders[tracking]['final_price'] = final_price
                orders[tracking]['status'] = 'pending_payment'
                send_message(chat_id, 
                    f"✅ قیمت نهایی سفارش {tracking} به {final_price:,} تومان تغییر کرد.\n"
                    f"وضعیت به '{get_order_status_text('pending_payment')}' تغییر یافت.",
                    build_admin_panel()
                )
                # اطلاع به کاربر
                send_message(orders[tracking]['chat_id'],
                    f"💰 قیمت نهایی سفارش شما (کد {tracking}) تعیین شد: {final_price:,} تومان\n"
                    f"لطفاً مبلغ را واریز کرده و رسید را از طریق دکمه 'ارسال رسید پرداخت' ارسال کنید."
                )
                user_data.pop(chat_id, None)
            else:
                send_message(chat_id, "❌ خطا در تنظیم قیمت.")
                user_data.pop(chat_id, None)
        except ValueError:
            send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید (مثلاً 1500000):")

def handle_admin_receipt_action(chat_id, text):
    """پردازش تایید/رد رسید توسط ادمین"""
    if text.startswith("✅ تایید رسید"):
        tracking = text.split()[-1]
        if tracking in orders:
            orders[tracking]['status'] = 'payment_verified'
            send_message(chat_id, f"✅ رسید سفارش {tracking} تایید شد.", build_admin_panel())
            send_message(orders[tracking]['chat_id'],
                f"✅ رسید پرداخت شما برای سفارش {tracking} تایید شد.\n"
                f"سفارش شما در مرحله تولید قرار گرفت."
            )
            user_data.pop(chat_id, None)
        else:
            send_message(chat_id, "❌ خطا در تایید رسید.")
    
    elif text.startswith("❌ رد رسید"):
        tracking = text.split()[-1]
        if tracking in orders:
            orders[tracking]['status'] = 'payment_rejected'
            send_message(chat_id, f"❌ رسید سفارش {tracking} رد شد.", build_admin_panel())
            send_message(orders[tracking]['chat_id'],
                f"❌ رسید پرداخت شما برای سفارش {tracking} رد شد.\n"
                f"لطفاً با پشتیبانی تماس بگیرید."
            )
            user_data.pop(chat_id, None)
        else:
            send_message(chat_id, "❌ خطا در رد رسید.")
    
    elif text == "🔙 بازگشت":
        send_message(chat_id, "به پنل مدیریت بازگشتید.", build_admin_panel())
        user_data.pop(chat_id, None)
    else:
        send_message(chat_id, "لطفاً یکی از گزینه‌ها را انتخاب کنید.")

# ========== نمایش خلاصه سفارش برای کاربر ==========
def show_order_summary(chat_id, tracking):
    order = orders.get(tracking)
    if not order:
        send_message(chat_id, "❌ سفارشی با این کد پیدا نشد.")
        return False
    
    msg = (
        f"📋 اطلاعات سفارش:\n\n"
        f"🆔 کد پیگیری: {tracking}\n"
        f"📊 وضعیت: {get_order_status_text(order['status'])}\n"
        f"🛒 محصولات:\n"
    )
    for item in order['items']:
        msg += f"  - {item['product']} | {item['quantity_text']} | حدود قیمت: {item['price_range']}\n"
    
    if order.get('final_price'):
        msg += f"\n💰 قیمت نهایی: {order['final_price']:,} تومان\n"
    else:
        total = order.get('total_price', 0)
        msg += f"\n💰 قیمت تقریبی: {total:,} تومان\n"
    
    msg += f"👤 نام: {order['name']}\n"
    msg += f"📞 تلفن: {order['phone']}\n"
    
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

# ========== حلقه اصلی ==========
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
                        chat_id_str = str(chat_id)
                        
                        # ===== ورود به پنل ادمین با ADMZ =====
                        if text == "ADMZ" and chat_id_str == ADMIN_ID:
                            send_message(chat_id, 
                                "👋 به پنل مدیریت خوش آمدید!\n"
                                "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                                build_admin_panel()
                            )
                            continue
                        
                        # ===== مدیریت دستورات ادمین =====
                        if chat_id_str == ADMIN_ID:
                            if text in ["📋 سفارش‌های باز (ثبت اولیه)", "💰 سفارش‌های پرداخت نشده", "📋 لیست همه سفارش‌ها"]:
                                handle_admin_command(chat_id, text)
                                continue
                            
                            if user_data.get(chat_id, {}).get("state") in ["ADMIN_SET_PRICE_GET_TRACKING", "ADMIN_SET_PRICE_ENTER"]:
                                handle_admin_set_price(chat_id, text)
                                continue
                            
                            if text.startswith("✅ تایید رسید") or text.startswith("❌ رد رسید") or text == "🔙 بازگشت":
                                handle_admin_receipt_action(chat_id, text)
                                continue
                        
                        # ===== دریافت تصویر رسید از کاربر =====
                        if "photo" in message and user_data.get(chat_id, {}).get("state") == "RECEIPT_UPLOAD":
                            photo = message["photo"][-1]
                            file_id = photo["file_id"]
                            data = user_data[chat_id]
                            tracking = data.get("tracking")
                            if tracking and tracking in orders:
                                caption = (
                                    f"📎 رسید پرداخت جدید\n\n"
                                    f"🆔 کد پیگیری: {tracking}\n"
                                    f"👤 کاربر: {orders[tracking]['name']}\n"
                                    f"📞 تلفن: {orders[tracking]['phone']}\n"
                                    f"💰 مبلغ: {orders[tracking].get('final_price', 'نامشخص')} تومان"
                                )
                                keyboard = build_admin_confirm_keyboard(tracking)
                                send_photo(ADMIN_ID, file_id, caption, keyboard)
                                send_message(chat_id, "✅ رسید شما با موفقیت ارسال شد.\nمنتظر تأیید ادمین باشید.", build_main_menu())
                                user_data.pop(chat_id, None)
                            else:
                                send_message(chat_id, "❌ خطا در ارسال رسید. لطفاً مجدداً تلاش کنید.", build_main_menu())
                                user_data.pop(chat_id, None)
                            continue
                        
                        # ===== منوی اصلی کاربر =====
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
                        
                        if text == "💰 ارسال رسید پرداخت":
                            user_data[chat_id] = {"state": "RECEIPT_GET_TRACKING"}
                            send_message(chat_id, "🔑 لطفاً کد پیگیری سفارش خود را وارد کنید:", remove_keyboard())
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
                        
                        if state == "PRODUCT_SELECTION":
                            handle_product_selection(chat_id, text)
                        elif state == "QUANTITY_SELECTION":
                            handle_quantity_selection(chat_id, text)
                        elif state == "ASK_MORE_ITEMS":
                            handle_ask_more_items(chat_id, text)
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
                        elif state == "RECEIPT_GET_TRACKING":
                            handle_receipt_tracking(chat_id, text)
                        elif state == "EDIT_GET_TRACKING":
                            tracking = normalize_persian_numbers(text.strip())
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
                                    order = orders[tracking]
                                    user_data[chat_id] = {
                                        "state": "PRODUCT_SELECTION",
                                        "edit_mode": True,
                                        "edit_tracking": tracking,
                                        "items": order['items'].copy(),
                                        "total_price": order.get('total_price', 0)
                                    }
                                    send_message(chat_id, 
                                        f"🔄 در حال ویرایش سفارش {tracking}\n"
                                        f"سبد خرید فعلی: {len(order['items'])} محصول\n"
                                        f"برای اضافه کردن محصول جدید، یکی از گزینه‌ها را انتخاب کنید:",
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
                        elif state == "TRACK_GET_TRACKING":
                            tracking = normalize_persian_numbers(text.strip())
                            if tracking in orders:
                                show_order_summary(chat_id, tracking)
                                send_message(chat_id, "به منوی اصلی بازگشتید.", build_main_menu())
                                user_data.pop(chat_id, None)
                            else:
                                send_message(chat_id, "❌ کد پیگیری نامعتبر است. لطفاً دوباره وارد کنید یا /start را بزنید.")
                        else:
                            if text not in ["/start", "🛍️ ثبت سفارش جدید", "💰 ارسال رسید پرداخت", "✏️ تغییر سفارش", "🔍 پیگیری سفارش", "🔙 بازگشت"]:
                                send_message(chat_id, "لطفاً از دکمه‌های منو استفاده کنید.", build_main_menu())
            
            time.sleep(0.5)
        except Exception as e:
            print(f"خطا در حلقه بات: {e}")
            time.sleep(3)

# ========== اجرا ==========
if __name__ == "__main__":
    bot_loop()