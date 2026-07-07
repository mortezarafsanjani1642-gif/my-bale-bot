import requests
import time
import json
import os
import random
import string

# ==================================================
# ================ تنظیمات اولیه ==================
# ==================================================

TOKEN = "BIJFAB0MVHQAPLZSKUQLWKYWBTLDWCEQCCBHOXLCLXUUARAVJTITTEJHIHWYMCOX"
ADMIN_ID = "u0BFJ3K03f5d8786134f2ab3c1ebfc40"
API_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

SETTINGS_FILE = "settings.json"
ORDERS_FILE = "orders.json"
NEXT_PRODUCTION_DATE = "۱۵ تیر ۱۴۰۴"

QUANTITIES = {
    "نیم کیلو": 0.5,
    "یک کیلو": 1.0,
    "یک کیلو و نیم": 1.5,
    "دو کیلو": 2.0,
    "دو کیلو و نیم": 2.5,
    "سه کیلو": 3.0
}

# ==================================================
# ================ مدیریت فایل‌ها ==================
# ==================================================

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            default = {
                "products": {
                    "سوسیس آلمانی": {"min": 1500000, "max": 1700000},
                    "سوسیس بلغاری": {"min": 1500000, "max": 1700000},
                    "ناگت مرغ": {"min": 1500000, "max": 1700000},
                    "ناگت بوقلمون": {"min": 1500000, "max": 1700000}
                },
                "order_status": "open"
            }
            save_settings(default)
            return default
    except Exception as e:
        print(f"خطا در بارگذاری تنظیمات: {e}")
        return {"products": {}, "order_status": "open"}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        print("✅ تنظیمات ذخیره شد.")
    except Exception as e:
        print(f"❌ خطا در ذخیره تنظیمات: {e}")

def load_orders():
    global orders
    try:
        if os.path.exists(ORDERS_FILE):
            with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
                orders = json.load(f)
            print(f"✅ {len(orders)} سفارش بارگذاری شد.")
        else:
            orders = {}
    except Exception as e:
        print(f"❌ خطا در بارگذاری سفارش‌ها: {e}")
        orders = {}

def save_orders():
    try:
        with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
        print("✅ سفارش‌ها ذخیره شدند.")
    except Exception as e:
        print(f"❌ خطا در ذخیره سفارش‌ها: {e}")

# ==================================================
# ============== توابع ارتباط با API ===============
# ==================================================

def send_message(chat_id, text, chat_keypad=None, chat_keypad_type="New"):
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
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

# ==================================================
# ================ توابع کمکی ======================
# ==================================================

def normalize_persian_numbers(text):
    persian_map = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }
    return ''.join(persian_map.get(char, char) for char in text)

def generate_tracking_code():
    return ''.join(random.choices(string.digits, k=6))

def calculate_price_range(product_prices, quantity_text):
    weight = QUANTITIES.get(quantity_text, 0)
    min_price = int(product_prices['min'] * weight)
    max_price = int(product_prices['max'] * weight)
    return min_price, max_price

def refresh_products():
    global PRODUCTS
    settings = load_settings()
    PRODUCTS = settings.get("products", {})

# ==================================================
# ================ ساخت کیبوردها ===================
# ==================================================

def build_main_menu():
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

def build_back_keyboard():
    return {
        "rows": [
            {"buttons": [{"id": "back", "type": "Simple", "button_text": "🔙 بازگشت"}]}
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def build_product_keyboard(products):
    rows = []
    for p in products:
        rows.append({"buttons": [{"id": p, "type": "Simple", "button_text": p}]})
    rows.append({"buttons": [{"id": "back", "type": "Simple", "button_text": "🔙 بازگشت"}]})
    return {
        "rows": rows,
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def build_quantity_keyboard():
    rows = []
    for q in QUANTITIES.keys():
        rows.append({"buttons": [{"id": q, "type": "Simple", "button_text": q}]})
    rows.append({"buttons": [{"id": "back", "type": "Simple", "button_text": "🔙 بازگشت"}]})
    return {
        "rows": rows,
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def build_confirmation_keyboard():
    return {
        "rows": [
            {"buttons": [{"id": "confirm", "type": "Simple", "button_text": "✅ ثبت سفارش"}]},
            {"buttons": [{"id": "back", "type": "Simple", "button_text": "🔙 بازگشت"}]}
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def build_admin_panel():
    return {
        "rows": [
            {"buttons": [{"id": "admin_open", "type": "Simple", "button_text": "📋 سفارش‌های باز"}]},
            {"buttons": [{"id": "admin_pending", "type": "Simple", "button_text": "💰 در انتظار رسید"}]},
            {"buttons": [{"id": "admin_verified", "type": "Simple", "button_text": "✅ رسیدهای تایید شده"}]},
            {"buttons": [{"id": "admin_rejected", "type": "Simple", "button_text": "❌ رسیدهای رد شده"}]},
            {"buttons": [{"id": "admin_all", "type": "Simple", "button_text": "📋 لیست همه سفارش‌ها"}]},
            {"buttons": [{"id": "admin_products", "type": "Simple", "button_text": "🛠 مدیریت محصولات"}]},
            {"buttons": [{"id": "admin_status", "type": "Simple", "button_text": "🔓 وضعیت سفارش‌گذاری"}]}
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

# ==================================================
# ============== منطق اصلی ربات ====================
# ==================================================

settings = load_settings()
PRODUCTS = settings.get("products", {})
ORDER_STATUS = settings.get("order_status", "open")
user_data = {}
orders = {}
load_orders()

# ---------- بخش مدیریت محصولات ----------
def handle_admin_products(chat_id, command):
    if command == "🛠 مدیریت محصولات" or command == "admin_products":
        keyboard = {
            "rows": [
                {"buttons": [{"id": "add_product", "type": "Simple", "button_text": "➕ افزودن محصول جدید"}]},
                {"buttons": [{"id": "list_products", "type": "Simple", "button_text": "📋 لیست محصولات"}]},
                {"buttons": [{"id": "delete_product", "type": "Simple", "button_text": "❌ حذف محصول"}]},
                {"buttons": [{"id": "back", "type": "Simple", "button_text": "🔙 بازگشت"}]}
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        send_message(chat_id, "🛠 مدیریت محصولات:\nلطفاً یکی از گزینه‌ها را انتخاب کنید:", keyboard)
        user_data[chat_id] = {"state": "ADMIN_PRODUCTS_MENU"}
    
    elif command == "➕ افزودن محصول جدید" or command == "add_product":
        send_message(chat_id, "🔤 نام محصول را وارد کنید:", build_back_keyboard())
        user_data[chat_id] = {"state": "ADMIN_ADD_PRODUCT_NAME"}
    
    elif command == "📋 لیست محصولات" or command == "list_products":
        if not PRODUCTS:
            send_message(chat_id, "📭 هیچ محصولی ثبت نشده است.", build_admin_panel())
            return
        msg = "📋 لیست محصولات و قیمت‌ها:\n\n"
        for name, price in PRODUCTS.items():
            msg += f"🛒 {name}: {price['min']:,} - {price['max']:,} تومان\n"
        send_message(chat_id, msg, build_admin_panel())
        user_data.pop(chat_id, None)
    
    elif command == "❌ حذف محصول" or command == "delete_product":
        if not PRODUCTS:
            send_message(chat_id, "📭 هیچ محصولی برای حذف وجود ندارد.", build_admin_panel())
            return
        rows = []
        for p in PRODUCTS.keys():
            rows.append({"buttons": [{"id": f"del_{p}", "type": "Simple", "button_text": p}]})
        rows.append({"buttons": [{"id": "back", "type": "Simple", "button_text": "🔙 بازگشت"}]})
        keyboard = {"rows": rows, "resize_keyboard": True, "one_time_keyboard": False}
        send_message(chat_id, "❌ محصول مورد نظر را برای حذف انتخاب کنید:", keyboard)
        user_data[chat_id] = {"state": "ADMIN_DELETE_PRODUCT"}

def handle_add_product_name(chat_id, text):
    if text == "🔙 بازگشت":
        send_message(chat_id, "به پنل مدیریت بازگشتید.", build_admin_panel())
        user_data.pop(chat_id, None)
        return
    user_data[chat_id]["new_product_name"] = text
    user_data[chat_id]["state"] = "ADMIN_ADD_PRODUCT_MIN"
    send_message(chat_id, f"✅ نام '{text}' ثبت شد.\n\nلطفاً حداقل قیمت (به تومان) را وارد کنید:\nمثال: 1500000", build_back_keyboard())

def handle_add_product_min(chat_id, text):
    try:
        min_price = int(normalize_persian_numbers(text.strip()))
        if min_price <= 0:
            send_message(chat_id, "❌ قیمت باید بزرگتر از صفر باشد. دوباره وارد کنید:")
            return
        user_data[chat_id]["new_min"] = min_price
        user_data[chat_id]["state"] = "ADMIN_ADD_PRODUCT_MAX"
        send_message(chat_id, f"✅ حداقل قیمت {min_price:,} تومان ثبت شد.\n\nلطفاً حداکثر قیمت (به تومان) را وارد کنید:\nمثال: 1700000", build_back_keyboard())
    except ValueError:
        send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید:")

def handle_add_product_max(chat_id, text):
    try:
        max_price = int(normalize_persian_numbers(text.strip()))
        name = user_data[chat_id].get("new_product_name")
        min_price = user_data[chat_id].get("new_min")
        if max_price <= min_price:
            send_message(chat_id, "❌ حداکثر قیمت باید از حداقل قیمت بیشتر باشد. دوباره وارد کنید:")
            return
        settings = load_settings()
        settings["products"][name] = {"min": min_price, "max": max_price}
        save_settings(settings)
        refresh_products()
        send_message(chat_id, f"✅ محصول '{name}' با قیمت {min_price:,} - {max_price:,} تومان اضافه شد.", build_admin_panel())
        user_data.pop(chat_id, None)
    except ValueError:
        send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید:")

def handle_delete_product(chat_id, text):
    if text == "🔙 بازگشت":
        send_message(chat_id, "به پنل مدیریت بازگشتید.", build_admin_panel())
        user_data.pop(chat_id, None)
        return
    if text in PRODUCTS:
        settings = load_settings()
        del settings["products"][text]
        save_settings(settings)
        refresh_products()
        send_message(chat_id, f"✅ محصول '{text}' با موفقیت حذف شد.", build_admin_panel())
        user_data.pop(chat_id, None)
    else:
        send_message(chat_id, "❌ محصول انتخاب شده معتبر نیست. لطفاً از لیست انتخاب کنید.")

# ---------- مدیریت وضعیت سفارش ----------
def handle_admin_order_status(chat_id):
    global ORDER_STATUS
    settings = load_settings()
    current = settings.get("order_status", "open")
    new_status = "closed" if current == "open" else "open"
    settings["order_status"] = new_status
    save_settings(settings)
    ORDER_STATUS = new_status
    status_text = "باز ✅" if new_status == "open" else "بسته ❌"
    send_message(chat_id, f"🔓 وضعیت سفارش‌گذاری به '{status_text}' تغییر کرد.", build_admin_panel())

# ---------- فرآیند ثبت سفارش کاربر ----------
def start_new_order(chat_id):
    if ORDER_STATUS == "closed":
        send_message(chat_id, "⛔ سفارش‌گذاری در حال حاضر متوقف شده است.\nلطفاً بعداً مجدداً تلاش کنید.", build_main_menu())
        return
    user_data[chat_id] = {"state": "PRODUCT_SELECTION", "items": [], "total_price": 0}
    welcome = f"🎉 خوش آمدید!\n📅 تاریخ تولید بعدی: {NEXT_PRODUCTION_DATE}\nلطفاً محصول خود را انتخاب کنید:"
    send_message(chat_id, welcome, build_product_keyboard(PRODUCTS.keys()))

def handle_product_selection(chat_id, text):
    if text in PRODUCTS:
        user_data[chat_id]["current_product"] = text
        user_data[chat_id]["current_prices"] = PRODUCTS[text]
        user_data[chat_id]["prev_state"] = "PRODUCT_SELECTION"
        user_data[chat_id]["state"] = "QUANTITY_SELECTION"
        send_message(chat_id, f"✅ {text} انتخاب شد.\nحالا مقدار را انتخاب کنید:", build_quantity_keyboard())
    else:
        send_message(chat_id, "لطفاً یکی از محصولات موجود را انتخاب کنید.", build_product_keyboard(PRODUCTS.keys()))

def handle_quantity_selection(chat_id, text):
    if text in QUANTITIES:
        min_price, max_price = calculate_price_range(user_data[chat_id]["current_prices"], text)
        avg_price = (min_price + max_price) // 2
        item = {
            "product": user_data[chat_id]["current_product"],
            "quantity_text": text,
            "quantity_kg": QUANTITIES[text],
            "price_range": f"{min_price:,} - {max_price:,} تومان",
            "avg_price": avg_price
        }
        user_data[chat_id]["items"].append(item)
        user_data[chat_id]["total_price"] += avg_price
        
        keyboard = {
            "rows": [
                {"buttons": [{"id": "yes", "type": "Simple", "button_text": "✅ بله، محصول دیگر"}]},
                {"buttons": [{"id": "no", "type": "Simple", "button_text": "❌ نه، ادامه ثبت سفارش"}]},
                {"buttons": [{"id": "back", "type": "Simple", "button_text": "🔙 بازگشت"}]}
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        send_message(chat_id, f"✅ {text} اضافه شد.\nآیا محصول دیگری می‌خواهید؟", keyboard)
        user_data[chat_id]["state"] = "ASK_MORE_PRODUCTS"
    else:
        send_message(chat_id, "لطفاً یکی از گزینه‌ها را انتخاب کنید.", build_quantity_keyboard())

def handle_ask_more_products(chat_id, text):
    if text == "✅ بله، محصول دیگر":
        user_data[chat_id]["state"] = "PRODUCT_SELECTION"
        send_message(chat_id, "محصول بعدی را انتخاب کنید:", build_product_keyboard(PRODUCTS.keys()))
    elif text == "❌ نه، ادامه ثبت سفارش":
        items = user_data[chat_id]["items"]
        total = user_data[chat_id]["total_price"]
        summary = "📋 خلاصه سفارش:\n\n"
        for i, item in enumerate(items, 1):
            summary += f"{i}. {item['product']} - {item['quantity_text']} - {item['price_range']}\n"
        summary += f"\n💰 مجموع: {total:,} تومان"
        send_message(chat_id, summary, build_confirmation_keyboard())
        user_data[chat_id]["state"] = "CONFIRM_ORDER"
    elif text == "🔙 بازگشت":
        send_message(chat_id, "به منوی اصلی بازگشتید.", build_main_menu())
        user_data.pop(chat_id, None)

def handle_confirm_order(chat_id, text):
    if text == "✅ ثبت سفارش":
        tracking = generate_tracking_code()
        while tracking in orders:
            tracking = generate_tracking_code()
        
        order_data = {
            "chat_id": chat_id,
            "items": user_data[chat_id]["items"],
            "total_price": user_data[chat_id]["total_price"],
            "status": "registered",
            "date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        orders[tracking] = order_data
        save_orders()
        send_message(chat_id, f"✅ سفارش شما با کد پیگیری {tracking} ثبت شد.\n\nجهت تکمیل سفارش، رسید پرداخت را ارسال کنید.", build_main_menu())
        user_data.pop(chat_id, None)
        send_message(ADMIN_ID, f"📢 سفارش جدید!\nکد: {tracking}\nکاربر: {chat_id}\nمبلغ: {order_data['total_price']:,} تومان", build_admin_panel())
    elif text == "🔙 بازگشت":
        send_message(chat_id, "ثبت سفارش لغو شد.", build_main_menu())
        user_data.pop(chat_id, None)

# ---------- ارسال رسید پرداخت ----------
def handle_receipt(chat_id, text):
    if text == "💰 ارسال رسید پرداخت":
        send_message(chat_id, "🔑 لطفاً کد پیگیری سفارش خود را وارد کنید:", build_back_keyboard())
        user_data[chat_id] = {"state": "RECEIPT_GET_TRACKING"}
    elif user_data.get(chat_id, {}).get("state") == "RECEIPT_GET_TRACKING":
        if text == "🔙 بازگشت":
            send_message(chat_id, "به منوی اصلی بازگشتید.", build_main_menu())
            user_data.pop(chat_id, None)
            return
        tracking = normalize_persian_numbers(text.strip())
        if tracking in orders:
            user_data[chat_id]["receipt_tracking"] = tracking
            user_data[chat_id]["state"] = "RECEIPT_GET_DESC"
            send_message(chat_id, "💬 توضیحات یا مبلغ واریزی را وارد کنید (یا هر پیامی که ادمین ببیند):", build_back_keyboard())
        else:
            send_message(chat_id, "❌ کد پیگیری نامعتبر است. دوباره وارد کنید:", build_back_keyboard())
    elif user_data.get(chat_id, {}).get("state") == "RECEIPT_GET_DESC":
        tracking = user_data[chat_id]["receipt_tracking"]
        desc = text
        if tracking in orders:
            orders[tracking]['status'] = 'pending_payment'
            orders[tracking]['receipt_desc'] = desc
            save_orders()
            send_message(chat_id, f"✅ رسید شما برای سفارش {tracking} ارسال شد.\nمنتظر تایید ادمین باشید.", build_main_menu())
            send_message(ADMIN_ID, f"💰 رسید جدید برای سفارش {tracking}:\n{desc}\n\nبرای تایید/رد از پنل مدیریت استفاده کنید.", build_admin_panel())
            user_data.pop(chat_id, None)
        else:
            send_message(chat_id, "❌ خطا! دوباره تلاش کنید.", build_main_menu())
            user_data.pop(chat_id, None)

# ---------- پیگیری و ویرایش سفارش ----------
def handle_track_order(chat_id, text):
    if text == "🔍 پیگیری سفارش":
        send_message(chat_id, "🔑 کد پیگیری خود را وارد کنید:", build_back_keyboard())
        user_data[chat_id] = {"state": "TRACK_GET_CODE"}
    elif user_data.get(chat_id, {}).get("state") == "TRACK_GET_CODE":
        if text == "🔙 بازگشت":
            send_message(chat_id, "به منوی اصلی بازگشتید.", build_main_menu())
            user_data.pop(chat_id, None)
            return
        tracking = normalize_persian_numbers(text.strip())
        if tracking in orders:
            order = orders[tracking]
            status_text = {
                "registered": "📝 ثبت شده", 
                "pending_payment": "💰 در انتظار پرداخت", 
                "payment_verified": "✅ تایید شده", 
                "payment_rejected": "❌ رد شده", 
                "cancelled": "🚫 لغو شده"
            }.get(order.get('status'), "نامشخص")
            items_text = "\n".join([f"- {i['product']} {i['quantity_text']}" for i in order.get('items', [])])
            msg = f"📋 سفارش {tracking}\nوضعیت: {status_text}\n\n{items_text}\n💰 مجموع: {order.get('total_price', 0):,} تومان"
            send_message(chat_id, msg, build_main_menu())
            user_data.pop(chat_id, None)
        else:
            send_message(chat_id, "❌ کد نامعتبر. دوباره وارد کنید:", build_back_keyboard())

def handle_edit_order(chat_id, text):
    if text == "✏️ تغییر سفارش":
        send_message(chat_id, "🔑 کد پیگیری سفارش خود را برای لغو وارد کنید:", build_back_keyboard())
        user_data[chat_id] = {"state": "EDIT_GET_CODE"}
    elif user_data.get(chat_id, {}).get("state") == "EDIT_GET_CODE":
        if text == "🔙 بازگشت":
            send_message(chat_id, "به منوی اصلی بازگشتید.", build_main_menu())
            user_data.pop(chat_id, None)
            return
        tracking = normalize_persian_numbers(text.strip())
        if tracking in orders:
            if orders[tracking].get('status') in ['registered', 'pending_payment']:
                keyboard = {
                    "rows": [
                        {"buttons": [{"id": f"cancel_{tracking}", "type": "Simple", "button_text": f"❌ لغو سفارش {tracking}"}]},
                        {"buttons": [{"id": "back", "type": "Simple", "button_text": "🔙 بازگشت"}]}
                    ],
                    "resize_keyboard": True,
                    "one_time_keyboard": False
                }
                send_message(chat_id, f"سفارش {tracking} پیدا شد. آیا می‌خواهید آن را لغو کنید؟", keyboard)
                user_data[chat_id]["edit_tracking"] = tracking
                user_data[chat_id]["state"] = "EDIT_CHOOSE_ACTION"
            else:
                send_message(chat_id, f"❌ سفارش {tracking} در وضعیت '{orders[tracking].get('status')}' قابل لغو نیست.", build_main_menu())
                user_data.pop(chat_id, None)
        else:
            send_message(chat_id, "❌ کد نامعتبر.", build_back_keyboard())
    elif user_data.get(chat_id, {}).get("state") == "EDIT_CHOOSE_ACTION":
        tracking = user_data[chat_id]["edit_tracking"]
        if text == f"❌ لغو سفارش {tracking}":
            if tracking in orders:
                orders[tracking]['status'] = 'cancelled'
                save_orders()
                send_message(chat_id, f"✅ سفارش {tracking} لغو شد.", build_main_menu())
                user_data.pop(chat_id, None)
            else:
                send_message(chat_id, "❌ خطا!", build_main_menu())
                user_data.pop(chat_id, None)
        elif text == "🔙 بازگشت":
            send_message(chat_id, "به منوی اصلی بازگشتید.", build_main_menu())
            user_data.pop(chat_id, None)

# ---------- پنل ادمین ----------
def handle_admin_commands(chat_id, text):
    if text == "📋 سفارش‌های باز" or text == "admin_open":
        found = [f"{k}: {v['items'][0]['product']} - {v['total_price']:,} تومان" for k, v in orders.items() if v.get('status') == 'registered']
        send_message(chat_id, "📋 سفارش‌های باز:\n" + ("\n".join(found) if found else "هیچ سفارش بازی وجود ندارد."), build_admin_panel())
    
    elif text == "💰 در انتظار رسید" or text == "admin_pending":
        found = [f"{k}: {v.get('receipt_desc', 'بدون توضیح')}" for k, v in orders.items() if v.get('status') == 'pending_payment']
        send_message(chat_id, "💰 در انتظار رسید:\n" + ("\n".join(found) if found else "هیچ سفارشی در انتظار رسید نیست."), build_admin_panel())
    
    elif text == "✅ رسیدهای تایید شده" or text == "admin_verified":
        found = [f"{k}: {v['total_price']:,} تومان" for k, v in orders.items() if v.get('status') == 'payment_verified']
        send_message(chat_id, "✅ تایید شده:\n" + ("\n".join(found) if found else "هیچ سفارش تایید شده‌ای وجود ندارد."), build_admin_panel())
    
    elif text == "❌ رسیدهای رد شده" or text == "admin_rejected":
        found = [f"{k}" for k, v in orders.items() if v.get('status') == 'payment_rejected']
        send_message(chat_id, "❌ رد شده:\n" + ("\n".join(found) if found else "هیچ سفارش رد شده‌ای وجود ندارد."), build_admin_panel())
    
    elif text == "📋 لیست همه سفارش‌ها" or text == "admin_all":
        if not orders:
            send_message(chat_id, "📭 هیچ سفارشی وجود ندارد.", build_admin_panel())
            return
        msg = "📋 همه سفارش‌ها:\n\n"
        for k, v in list(orders.items())[:10]:
            msg += f"{k}: {v.get('status')} - {v['total_price']:,} تومان\n"
        send_message(chat_id, msg, build_admin_panel())
    
    elif text == "🛠 مدیریت محصولات" or text == "admin_products":
        handle_admin_products(chat_id, text)
    elif text == "🔓 وضعیت سفارش‌گذاری" or text == "admin_status":
        handle_admin_order_status(chat_id)

# ---------- پردازش پیام ورودی ----------
def process_update(chat_id, sender_id, text):
    print(f"🔍 پردازش: chat_id={chat_id}, sender={sender_id}, text='{text}'")
    
    if text == "/start":
        send_message(chat_id, "سلام! به ربات فروشگاهی خوش آمدید.\nلطفاً از منوی زیر استفاده کنید:", build_main_menu())
        return

    # پنل ادمین
    if sender_id == ADMIN_ID:
        state = user_data.get(chat_id, {}).get("state", "")
        if state == "ADMIN_PRODUCTS_MENU":
            handle_admin_products(chat_id, text)
            return
        elif state == "ADMIN_ADD_PRODUCT_NAME":
            handle_add_product_name(chat_id, text)
            return
        elif state == "ADMIN_ADD_PRODUCT_MIN":
            handle_add_product_min(chat_id, text)
            return
        elif state == "ADMIN_ADD_PRODUCT_MAX":
            handle_add_product_max(chat_id, text)
            return
        elif state == "ADMIN_DELETE_PRODUCT":
            handle_delete_product(chat_id, text)
            return

        # فرمان‌های پنل ادمین
        if text in ["📋 سفارش‌های باز", "💰 در انتظار رسید", "✅ رسیدهای تایید شده", 
                    "❌ رسیدهای رد شده", "📋 لیست همه سفارش‌ها", "🛠 مدیریت محصولات", 
                    "🔓 وضعیت سفارش‌گذاری"]:
            handle_admin_commands(chat_id, text)
            return

    # منوی کاربر معمولی
    state = user_data.get(chat_id, {}).get("state", "")
    
    if state == "PRODUCT_SELECTION":
        if text == "🛍️ ثبت سفارش جدید":
            start_new_order(chat_id)
        elif text == "🔙 بازگشت":
            send_message(chat_id, "به منوی اصلی بازگشتید.", build_main_menu())
            user_data.pop(chat_id, None)
        else:
            handle_product_selection(chat_id, text)
        return
    
    elif state == "QUANTITY_SELECTION":
        if text == "🔙 بازگشت":
            send_message(chat_id, "به منوی اصلی بازگشتید.", build_main_menu())
            user_data.pop(chat_id, None)
        else:
            handle_quantity_selection(chat_id, text)
        return
    
    elif state == "ASK_MORE_PRODUCTS":
        handle_ask_more_products(chat_id, text)
        return
    
    elif state == "CONFIRM_ORDER":
        handle_confirm_order(chat_id, text)
        return
    
    elif state == "RECEIPT_GET_TRACKING" or state == "RECEIPT_GET_DESC":
        handle_receipt(chat_id, text)
        return
    
    elif state == "TRACK_GET_CODE":
        handle_track_order(chat_id, text)
        return
    
    elif state == "EDIT_GET_CODE" or state == "EDIT_CHOOSE_ACTION":
        handle_edit_order(chat_id, text)
        return
    
    # منوی اصلی
    if text == "🛍️ ثبت سفارش جدید":
        start_new_order(chat_id)
    elif text == "💰 ارسال رسید پرداخت":
        handle_receipt(chat_id, text)
    elif text == "✏️ تغییر سفارش":
        handle_edit_order(chat_id, text)
    elif text == "🔍 پیگیری سفارش":
        handle_track_order(chat_id, text)
    else:
        send_message(chat_id, "❗ دستور نامعتبر. لطفاً از منو استفاده کنید.", build_main_menu())

# ==================================================
# =================== حلقه اصلی ====================
# ==================================================

def main():
    print("🚀 ربات فروشگاهی روبیکا شروع به کار کرد...")
    print(f"👤 ADMIN_ID: {ADMIN_ID}")
    print("⏳ در حال دریافت پیام‌ها...")
    
    start_id = 0
    processed_messages = set()

    while True:
        try:
            response = get_updates(start_id if start_id > 0 else None)
            if response.get("status") == "OK":
                data = response.get("data", {})
                updates = data.get("updates", [])

                if updates:
                    # پیدا کردن آخرین update_time
                    last_update_time = max([u.get("update_time", 0) for u in updates])
                    start_id = last_update_time + 1
                    print(f"🔄 start_id جدید (بر اساس update_time): {start_id}")

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
                            
                            # جلوگیری از پردازش تکراری
                            if msg_id and msg_id in processed_messages:
                                continue
                            if msg_id:
                                processed_messages.add(msg_id)
                            
                            print(f"📩 پیام از {sender}: {text}")
                            process_update(chat_id, sender, text)

            time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 ربات متوقف شد.")
            break
        except Exception as e:
            print(f"❌ خطا در حلقه اصلی: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()