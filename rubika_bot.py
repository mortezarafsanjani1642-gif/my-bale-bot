import requests
import time
import os
import random
import string
import json

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

def send_message(chat_id, text, keyboard=None):
    payload = {"chat_id": chat_id, "text": text}
    if keyboard:
        payload["reply_markup"] = keyboard
    try:
        r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        if r.status_code != 200:
            print(f"❌ خطا در ارسال پیام: {r.text}")
    except Exception as e:
        print(f"❌ خطا در اتصال: {e}")

def send_photo(chat_id, photo_file_id, caption=None, keyboard=None):
    payload = {"chat_id": chat_id, "photo": photo_file_id}
    if caption:
        payload["caption"] = caption
    if keyboard:
        payload["reply_markup"] = keyboard
    try:
        r = requests.post(f"{API_URL}/sendPhoto", json=payload, timeout=30)
        if r.status_code != 200:
            print(f"❌ خطا در ارسال عکس: {r.text}")
    except Exception as e:
        print(f"❌ خطا در اتصال: {e}")

# ========== تابع اصلاح شده با POST ==========
def get_updates(start_id=None):
    payload = {}
    if start_id:
        payload["start_id"] = start_id
    payload["timeout"] = 10
    
    try:
        r = requests.post(f"{API_URL}/getUpdates", json=payload, timeout=15)
        if r.status_code != 200:
            print(f"❌ HTTP خطا: {r.status_code}")
            return {}
        
        content = r.text.strip()
        if not content:
            print("⚠️ پاسخ خالی از سرور")
            return {}
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ خطای JSON: {e}")
            print(f"📄 محتوای پاسخ: {content[:200]}...")
            return {}
            
    except requests.exceptions.Timeout:
        print("⏰ زمان‌بندی درخواست منقضی شد")
        return {}
    except Exception as e:
        print(f"❌ خطا در دریافت آپدیت: {e}")
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

def remove_keyboard():
    return {"remove_keyboard": True}

def refresh_products():
    global PRODUCTS
    settings = load_settings()
    PRODUCTS = settings.get("products", {})

# ==================================================
# ================ ساخت کیبوردها ===================
# ==================================================

def build_back_keyboard():
    return {"keyboard": [[{"text": "🔙 بازگشت"}]], "resize_keyboard": True}

def build_main_menu():
    return {"keyboard": [
        [{"text": "🛍️ ثبت سفارش جدید"}],
        [{"text": "💰 ارسال رسید پرداخت"}],
        [{"text": "✏️ تغییر سفارش"}],
        [{"text": "🔍 پیگیری سفارش"}]
    ], "resize_keyboard": True}

def build_product_keyboard():
    kb = [[{"text": p}] for p in PRODUCTS.keys()]
    kb.append([{"text": "🔙 بازگشت"}])
    return {"keyboard": kb, "resize_keyboard": True}

def build_quantity_keyboard():
    kb = [[{"text": q}] for q in QUANTITIES.keys()]
    kb.append([{"text": "🔙 بازگشت"}])
    return {"keyboard": kb, "resize_keyboard": True}

def build_yes_no_keyboard():
    return {"keyboard": [
        [{"text": "✅ بله، ارسال کن"}],
        [{"text": "❌ نه، خودم می‌گیرم"}],
        [{"text": "🔙 بازگشت"}]
    ], "resize_keyboard": True}

def build_confirmation_keyboard():
    return {"keyboard": [
        [{"text": "✅ ثبت سفارش"}],
        [{"text": "🔙 بازگشت"}]
    ], "resize_keyboard": True}

def build_edit_cancel_keyboard(tracking):
    return {"keyboard": [
        [{"text": f"✏️ ویرایش سفارش {tracking}"}],
        [{"text": f"❌ لغو سفارش {tracking}"}],
        [{"text": "🔙 بازگشت"}]
    ], "resize_keyboard": True}

def build_admin_panel():
    return {"keyboard": [
        [{"text": "📋 سفارش‌های باز (ثبت اولیه)"}],
        [{"text": "💰 سفارش‌های پرداخت نشده"}],
        [{"text": "✅ رسیدهای تایید شده"}],
        [{"text": "❌ رسیدهای رد شده"}],
        [{"text": "⏳ رسیدهای در انتظار تایید"}],
        [{"text": "📋 لیست همه سفارش‌ها"}],
        [{"text": "🛠 مدیریت محصولات"}],
        [{"text": "🔓 وضعیت سفارش‌گذاری"}],
        [{"text": "🚫 لغو سفارش"}],
        [{"text": "🗑️ حذف همیشگی سفارش"}],
        [{"text": "📊 داشبورد"}]
    ], "resize_keyboard": True}

def build_dashboard_menu():
    return {"keyboard": [
        [{"text": "📊 اطلاعات وضعیت سفارش‌ها"}],
        [{"text": "📦 محصولات تولید شده"}],
        [{"text": "🔙 بازگشت"}]
    ], "resize_keyboard": True}

def build_admin_confirm_keyboard(tracking):
    return {"keyboard": [
        [{"text": f"✅ تایید رسید {tracking}"}],
        [{"text": f"❌ رد رسید {tracking}"}],
        [{"text": "🔙 بازگشت"}]
    ], "resize_keyboard": True}

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
    if command == "🛠 مدیریت محصولات":
        keyboard = {"keyboard": [
            [{"text": "➕ افزودن محصول جدید"}],
            [{"text": "📋 لیست محصولات"}],
            [{"text": "❌ حذف محصول"}],
            [{"text": "🔙 بازگشت"}]
        ], "resize_keyboard": True}
        send_message(chat_id, "🛠 مدیریت محصولات:\nلطفاً یکی از گزینه‌ها را انتخاب کنید:", keyboard)
        user_data[chat_id] = {"state": "ADMIN_PRODUCTS_MENU"}
    
    elif command == "➕ افزودن محصول جدید":
        send_message(chat_id, "🔤 نام محصول را وارد کنید:", remove_keyboard())
        user_data[chat_id] = {"state": "ADMIN_ADD_PRODUCT_NAME"}
    
    elif command == "📋 لیست محصولات":
        if not PRODUCTS:
            send_message(chat_id, "📭 هیچ محصولی ثبت نشده است.", build_admin_panel())
            return
        msg = "📋 لیست محصولات و قیمت‌ها:\n\n"
        for name, price in PRODUCTS.items():
            msg += f"🛒 {name}: {price['min']:,} - {price['max']:,} تومان\n"
        send_message(chat_id, msg, build_admin_panel())
        user_data.pop(chat_id, None)
    
    elif command == "❌ حذف محصول":
        if not PRODUCTS:
            send_message(chat_id, "📭 هیچ محصولی برای حذف وجود ندارد.", build_admin_panel())
            return
        keyboard = {"keyboard": [[{"text": p}] for p in PRODUCTS.keys()] + [[{"text": "🔙 بازگشت"}]], "resize_keyboard": True}
        send_message(chat_id, "❌ محصول مورد نظر را برای حذف انتخاب کنید:", keyboard)
        user_data[chat_id] = {"state": "ADMIN_DELETE_PRODUCT"}

def handle_add_product_name(chat_id, text):
    if text == "🔙 بازگشت":
        send_message(chat_id, "به پنل مدیریت بازگشتید.", build_admin_panel())
        user_data.pop(chat_id, None)
        return
    user_data[chat_id]["new_product_name"] = text
    user_data[chat_id]["state"] = "ADMIN_ADD_PRODUCT_MIN"
    send_message(chat_id, f"✅ نام '{text}' ثبت شد.\n\nلطفاً حداقل قیمت (به تومان) را وارد کنید:\nمثال: 1500000", remove_keyboard())

def handle_add_product_min(chat_id, text):
    try:
        min_price = int(normalize_persian_numbers(text.strip()))
        if min_price <= 0:
            send_message(chat_id, "❌ قیمت باید بزرگتر از صفر باشد. دوباره وارد کنید:")
            return
        user_data[chat_id]["new_min"] = min_price
        user_data[chat_id]["state"] = "ADMIN_ADD_PRODUCT_MAX"
        send_message(chat_id, f"✅ حداقل قیمت {min_price:,} تومان ثبت شد.\n\nلطفاً حداکثر قیمت (به تومان) را وارد کنید:\nمثال: 1700000", remove_keyboard())
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

# ---------- مدیریت لغو و حذف سفارش توسط ادمین ----------
def handle_admin_cancel_order(chat_id, text):
    state = user_data.get(chat_id, {}).get("state")
    if state == "ADMIN_CANCEL_GET_TRACKING":
        if text == "🔙 بازگشت":
            send_message(chat_id, "به پنل مدیریت بازگشتید.", build_admin_panel())
            user_data.pop(chat_id, None)
            return
        tracking = normalize_persian_numbers(text.strip())
        if tracking in orders:
            orders[tracking]['status'] = 'cancelled'
            save_orders()
            try:
                user_chat_id = orders[tracking].get('chat_id')
                if user_chat_id:
                    send_message(user_chat_id,
                        f"🚫 سفارش شما با کد پیگیری {tracking} توسط مدیر لغو شد.\n"
                        f"در صورت نیاز با پشتیبانی تماس بگیرید."
                    )
            except:
                pass
            send_message(chat_id, f"✅ سفارش {tracking} با موفقیت لغو شد.", build_admin_panel())
            user_data.pop(chat_id, None)
        else:
            send_message(chat_id, "❌ کد پیگیری نامعتبر است. لطفاً دوباره وارد کنید:", build_back_keyboard())
    else:
        send_message(chat_id, "🔑 لطفاً کد پیگیری سفارش مورد نظر برای لغو را وارد کنید:", build_back_keyboard())
        user_data[chat_id] = {"state": "ADMIN_CANCEL_GET_TRACKING"}

def handle_admin_delete_order(chat_id, text):
    state = user_data.get(chat_id, {}).get("state")
    if state == "ADMIN_DELETE_GET_TRACKING":
        if text == "🔙 بازگشت":
            send_message(chat_id, "به پنل مدیریت بازگشتید.", build_admin_panel())
            user_data.pop(chat_id, None)
            return
        tracking = normalize_persian_numbers(text.strip())
        if tracking in orders:
            order = orders.pop(tracking)
            save_orders()
            try:
                user_chat_id = order.get('chat_id')
                if user_chat_id:
                    send_message(user_chat_id,
                        f"🗑️ سفارش شما با کد پیگیری {tracking} به طور کامل از سیستم حذف شد."
                    )
            except:
                pass
            send_message(chat_id, f"✅ سفارش {tracking} با موفقیت حذف شد.", build_admin_panel())
            user_data.pop(chat_id, None)
        else:
            send_message(chat_id, "❌ کد پیگیری نامعتبر است. لطفاً دوباره وارد کنید:", build_back_keyboard())
    else:
        send_message(chat_id, "🔑 لطفاً کد پیگیری سفارش مورد نظر برای حذف کامل را وارد کنید:", build_back_keyboard())
        user_data[chat_id] = {"state": "ADMIN_DELETE_GET_TRACKING"}

# ---------- داشبورد ----------
def handle_admin_dashboard(chat_id):
    send_message(chat_id, "📊 داشبورد مدیریت:\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:", build_dashboard_menu())
    user_data[chat_id] = {"state": "ADMIN_DASHBOARD_MENU"}

def handle_dashboard_status(chat_id):
    if not orders:
        send_message(chat_id, "📭 هیچ سفارشی در سیستم ثبت نشده است.", build_admin_panel())
        user_data.pop(chat_id, None)
        return
    
    stats = {"registered": 0, "pending_payment": 0, "payment_verified": 0, "payment_rejected": 0, "cancelled": 0}
    for order in orders.values():
        status = order.get('status', 'registered')
        if status in stats: stats[status] += 1
    total = sum(stats.values())
    msg = (
        f"📊 اطلاعات وضعیت سفارش‌ها:\n\n"
        f"📝 ثبت اولیه: {stats['registered']}\n"
        f"💰 در انتظار رسید: {stats['pending_payment']}\n"
        f"✅ تایید شده: {stats['payment_verified']}\n"
        f"❌ رد شده: {stats['payment_rejected']}\n"
        f"🚫 لغو شده: {stats['cancelled']}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📦 مجموع کل: {total}"
    )
    send_message(chat_id, msg, build_dashboard_menu())

def handle_dashboard_products(chat_id):
    if not orders:
        send_message(chat_id, "📭 هیچ سفارشی ثبت نشده.", build_admin_panel())
        user_data.pop(chat_id, None)
        return
    product_stats = {}
    for order in orders.values():
        if order.get('status') == 'payment_verified':
            for item in order.get('items', []):
                name = item.get('product', 'نامشخص')
                product_stats[name] = product_stats.get(name, 0) + 1
    if not product_stats:
        send_message(chat_id, "📭 هیچ محصول تایید شده‌ای یافت نشد.", build_dashboard_menu())
        return
    sorted_products = sorted(product_stats.items(), key=lambda x: x[1], reverse=True)
    msg = "📦 آمار محصولات تولید شده (تایید شده):\n\n"
    for idx, (name, count) in enumerate(sorted_products, 1):
        msg += f"{idx}. {name}: {count} سفارش\n"
    msg += f"\n📊 مجموع کل: {sum(product_stats.values())} سفارش"
    send_message(chat_id, msg, build_dashboard_menu())

# ---------- فرآیند ثبت سفارش کاربر ----------
def start_new_order(chat_id):
    if ORDER_STATUS == "closed":
        send_message(chat_id, "⛔ سفارش‌گذاری در حال حاضر متوقف شده است.\nلطفاً بعداً مجدداً تلاش کنید.", build_main_menu())
        return
    user_data[chat_id] = {"state": "PRODUCT_SELECTION", "items": [], "total_price": 0}
    welcome = f"🎉 خوش آمدید!\n📅 تاریخ تولید بعدی: {NEXT_PRODUCTION_DATE}\nلطفاً محصول خود را انتخاب کنید:"
    send_message(chat_id, welcome, build_product_keyboard())

def handle_product_selection(chat_id, text):
    if text in PRODUCTS:
        user_data[chat_id]["current_product"] = text
        user_data[chat_id]["current_prices"] = PRODUCTS[text]
        user_data[chat_id]["prev_state"] = "PRODUCT_SELECTION"
        user_data[chat_id]["state"] = "QUANTITY_SELECTION"
        send_message(chat_id, f"✅ {text} انتخاب شد.\nحالا مقدار را انتخاب کنید:", build_quantity_keyboard())
    else:
        send_message(chat_id, "لطفاً یکی از محصولات موجود را انتخاب کنید.", build_product_keyboard())

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
        
        keyboard = {"keyboard": [
            [{"text": "✅ بله، محصول دیگر"}],
            [{"text": "❌ نه، ادامه ثبت سفارش"}],
            [{"text": "🔙 بازگشت"}]
        ], "resize_keyboard": True}
        send_message(chat_id, f"✅ {text} اضافه شد.\nآیا محصول دیگری می‌خواهید؟", keyboard)
        user_data[chat_id]["state"] = "ASK_MORE_PRODUCTS"
    else:
        send_message(chat_id, "لطفاً یکی از گزینه‌ها را انتخاب کنید.", build_quantity_keyboard())

def handle_ask_more_products(chat_id, text):
    if text == "✅ بله، محصول دیگر":
        user_data[chat_id]["state"] = "PRODUCT_SELECTION"
        send_message(chat_id, "محصول بعدی را انتخاب کنید:", build_product_keyboard())
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
    else:
        handle_quantity_selection(chat_id, text)

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
        send_message(ADMIN_ID, f"📢 سفارش جدید!\nکد: {tracking}\nکاربر: {chat_id}\nمبلغ: {order_data['total_price']:,} تومان")
    elif text == "🔙 بازگشت":
        send_message(chat_id, "ثبت سفارش لغو شد.", build_main_menu())
        user_data.pop(chat_id, None)
    else:
        send_message(chat_id, "لطفاً یکی از گزینه‌ها را انتخاب کنید.", build_confirmation_keyboard())

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
            send_message(chat_id, "💬 توضیحات یا مبلغ واریزی را وارد کنید (یا هر پیامی که ادمین ببیند):", remove_keyboard())
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
            status_text = {"registered": "📝 ثبت شده", "pending_payment": "💰 در انتظار پرداخت", "payment_verified": "✅ تایید شده", "payment_rejected": "❌ رد شده", "cancelled": "🚫 لغو شده"}.get(order.get('status'), "نامشخص")
            items_text = "\n".join([f"- {i['product']} {i['quantity_text']}" for i in order.get('items', [])])
            msg = f"📋 سفارش {tracking}\nوضعیت: {status_text}\n\n{items_text}\n💰 مجموع: {order.get('total_price', 0):,} تومان"
            send_message(chat_id, msg, build_main_menu())
            user_data.pop(chat_id, None)
        else:
            send_message(chat_id, "❌ کد نامعتبر. دوباره وارد کنید:", build_back_keyboard())

def handle_edit_order(chat_id, text):
    if text == "✏️ تغییر سفارش":
        send_message(chat_id, "🔑 کد پیگیری سفارش خود را برای ویرایش یا لغو وارد کنید:", build_back_keyboard())
        user_data[chat_id] = {"state": "EDIT_GET_CODE"}
    elif user_data.get(chat_id, {}).get("state") == "EDIT_GET_CODE":
        if text == "🔙 بازگشت":
            send_message(chat_id, "به منوی اصلی بازگشتید.", build_main_menu())
            user_data.pop(chat_id, None)
            return
        tracking = normalize_persian_numbers(text.strip())
        if tracking in orders:
            if orders[tracking].get('status') in ['registered', 'pending_payment']:
                send_message(chat_id, f"سفارش {tracking} پیدا شد. چه اقدامی می‌خواهید انجام دهید؟", build_edit_cancel_keyboard(tracking))
                user_data[chat_id]["edit_tracking"] = tracking
                user_data[chat_id]["state"] = "EDIT_CHOOSE_ACTION"
            else:
                send_message(chat_id, f"❌ سفارش {tracking} در وضعیت '{orders[tracking].get('status')}' قابل ویرایش نیست.", build_main_menu())
                user_data.pop(chat_id, None)
        else:
            send_message(chat_id, "❌ کد نامعتبر.", build_back_keyboard())
    elif user_data.get(chat_id, {}).get("state") == "EDIT_CHOOSE_ACTION":
        tracking = user_data[chat_id]["edit_tracking"]
        if text == f"✏️ ویرایش سفارش {tracking}":
            send_message(chat_id, "برای ویرایش، لطفاً سفارش جدید ثبت کنید و سفارش قبلی را لغو نمایید.", build_main_menu())
            user_data.pop(chat_id, None)
        elif text == f"❌ لغو سفارش {tracking}":
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
        else:
            send_message(chat_id, "لطفاً از دکمه‌ها استفاده کنید.", build_edit_cancel_keyboard(tracking))

# ---------- پنل ادمین ----------
def handle_admin_commands(chat_id, text):
    if text == "📋 سفارش‌های باز (ثبت اولیه)":
        found = [f"{k}: {v['items'][0]['product']} - {v['total_price']:,} تومان" for k, v in orders.items() if v.get('status') == 'registered']
        send_message(chat_id, "📋 سفارش‌های باز:\n" + ("\n".join(found) if found else "هیچ سفارش بازی وجود ندارد."), build_admin_panel())
    
    elif text == "💰 سفارش‌های پرداخت نشده":
        found = [f"{k}: {v.get('receipt_desc', 'بدون توضیح')}" for k, v in orders.items() if v.get('status') == 'pending_payment']
        send_message(chat_id, "💰 در انتظار رسید:\n" + ("\n".join(found) if found else "هیچ سفارشی در انتظار رسید نیست."), build_admin_panel())
    
    elif text == "✅ رسیدهای تایید شده":
        found = [f"{k}: {v['total_price']:,} تومان" for k, v in orders.items() if v.get('status') == 'payment_verified']
        send_message(chat_id, "✅ تایید شده:\n" + ("\n".join(found) if found else "هیچ سفارش تایید شده‌ای وجود ندارد."), build_admin_panel())
    
    elif text == "❌ رسیدهای رد شده":
        found = [f"{k}" for k, v in orders.items() if v.get('status') == 'payment_rejected']
        send_message(chat_id, "❌ رد شده:\n" + ("\n".join(found) if found else "هیچ سفارش رد شده‌ای وجود ندارد."), build_admin_panel())
    
    elif text == "⏳ رسیدهای در انتظار تایید":
        found = [f"{k}: {v.get('receipt_desc', '')}" for k, v in orders.items() if v.get('status') == 'pending_payment']
        if found:
            for item in found:
                send_message(chat_id, f"⏳ {item}", build_admin_confirm_keyboard(item.split(":")[0]))
        else:
            send_message(chat_id, "هیچ رسید در انتظار تاییدی نیست.", build_admin_panel())
    
    elif text.startswith("✅ تایید رسید") or text.startswith("❌ رد رسید"):
        parts = text.split()
        if len(parts) == 3:
            tracking = parts[2]
            if tracking in orders:
                if "تایید" in text:
                    orders[tracking]['status'] = 'payment_verified'
                    save_orders()
                    send_message(chat_id, f"✅ رسید {tracking} تایید شد.", build_admin_panel())
                    try:
                        send_message(orders[tracking]['chat_id'], f"✅ سفارش {tracking} تایید شد. متشکریم!")
                    except: pass
                else:
                    orders[tracking]['status'] = 'payment_rejected'
                    save_orders()
                    send_message(chat_id, f"❌ رسید {tracking} رد شد.", build_admin_panel())
                    try:
                        send_message(orders[tracking]['chat_id'], f"❌ رسید سفارش {tracking} رد شد. لطفاً مجدداً ارسال کنید.")
                    except: pass
            else:
                send_message(chat_id, "❌ کد پیگیری نامعتبر!", build_admin_panel())
    
    elif text == "📋 لیست همه سفارش‌ها":
        if not orders:
            send_message(chat_id, "📭 هیچ سفارشی وجود ندارد.", build_admin_panel())
            return
        msg = "📋 همه سفارش‌ها:\n\n"
        for k, v in list(orders.items())[:10]:
            msg += f"{k}: {v.get('status')} - {v['total_price']:,} تومان\n"
        send_message(chat_id, msg, build_admin_panel())
    
    elif text == "🛠 مدیریت محصولات":
        handle_admin_products(chat_id, text)
    elif text == "🔓 وضعیت سفارش‌گذاری":
        handle_admin_order_status(chat_id)
    elif text == "🚫 لغو سفارش":
        handle_admin_cancel_order(chat_id, text)
    elif text == "🗑️ حذف همیشگی سفارش":
        handle_admin_delete_order(chat_id, text)
    elif text == "📊 داشبورد":
        handle_admin_dashboard(chat_id)

# ---------- پردازش پیام ورودی ----------
def process_update(chat_id, sender_id, text):
    if text == "/start":
        send_message(chat_id, "سلام! به ربات فروشگاهی خوش آمدید.\nلطفاً از منوی زیر استفاده کنید:", build_main_menu())
        return

    if sender_id == ADMIN_ID:
        state = user_data.get(chat_id, {}).get("state", "")
        if state == "ADMIN_ADD_PRODUCT_NAME":
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
        elif state == "ADMIN_CANCEL_GET_TRACKING":
            handle_admin_cancel_order(chat_id, text)
            return
        elif state == "ADMIN_DELETE_GET_TRACKING":
            handle_admin_delete_order(chat_id, text)
            return
        elif state == "ADMIN_DASHBOARD_MENU":
            if text == "📊 اطلاعات وضعیت سفارش‌ها":
                handle_dashboard_status(chat_id)
            elif text == "📦 محصولات تولید شده":
                handle_dashboard_products(chat_id)
            elif text == "🔙 بازگشت":
                send_message(chat_id, "به پنل مدیریت بازگشتید.", build_admin_panel())
                user_data.pop(chat_id, None)
            return
        elif state == "ADMIN_PRODUCTS_MENU":
            handle_admin_products(chat_id, text)
            return

        if text in ["📋 سفارش‌های باز (ثبت اولیه)", "💰 سفارش‌های پرداخت نشده", 
                    "✅ رسیدهای تایید شده", "❌ رسیدهای رد شده", "⏳ رسیدهای در انتظار تایید",
                    "📋 لیست همه سفارش‌ها", "🛠 مدیریت محصولات", "🔓 وضعیت سفارش‌گذاری",
                    "🚫 لغو سفارش", "🗑️ حذف همیشگی سفارش", "📊 داشبورد"]:
            handle_admin_commands(chat_id, text)
            return
        if text.startswith("✅ تایید رسید") or text.startswith("❌ رد رسید"):
            handle_admin_commands(chat_id, text)
            return

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
    print("🚀 ربات روبیکا شروع به کار کرد...")
    print(f"👤 ADMIN_ID: {ADMIN_ID}")
    print("⏳ در حال دریافت پیام‌ها...")
    
    start_id = None
    while True:
        try:
            updates = get_updates(start_id)
            if updates.get("status") == "OK":
                data = updates.get("data", {})
                update_count = len(data.get("updates", []))
                if update_count > 0:
                    print(f"📥 {update_count} آپدیت جدید دریافت شد.")
                
                if "next_offset_id" in data:
                    start_id = data["next_offset_id"]
                
                updates_list = data.get("updates", [])
                for upd in updates_list:
                    if upd.get("type") == "NewMessage":
                        chat_id = upd.get("chat_id")
                        msg_data = upd.get("new_message", {})
                        sender_id = msg_data.get("sender_id")
                        text = msg_data.get("text", "")
                        
                        if not chat_id or not sender_id:
                            continue
                        
                        print(f"📩 پیام از {sender_id}: {text}")
                        process_update(chat_id, sender_id, text)
                        
            time.sleep(1)
        except Exception as e:
            print(f"❌ خطا در حلقه اصلی: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()