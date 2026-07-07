from rubika_bot_api import Bot

TOKEN = "BIJFAB0MVHQAPLZSKUQLWKYWBTLDWCEQCCBHOXLCLXUUARAVJTITTEJHIHWYMCOX"
ADMIN_ID = "u0BFJ3K03f5d8786134f2ab3c1ebfc40"

bot = Bot(TOKEN)

user_state = {}

MAIN_KEYBOARD = {
    "keyboard": [
        [{"text": "🛍 ثبت سفارش جدید"}],
        [{"text": "🔍 پیگیری وضعیت سفارش"}],
        [{"text": "📷 بارگذاری تصویر رسید"}]
    ],
    "resize_keyboard": True
}


@bot.on_message()
def handle_message(message):

    chat_id = message.sender_id
    text = getattr(message, "text", "")

    if text == "/start":
        bot.send_message(
            chat_id,
            "به ربات خوش آمدید",
            reply_markup=MAIN_KEYBOARD
        )
        return

    if text == "🛍 ثبت سفارش جدید":

        keyboard = {
            "keyboard": [
                [{"text": "1"}],
                [{"text": "2"}],
                [{"text": "3"}]
            ],
            "resize_keyboard": True
        }

        bot.send_message(
            chat_id,
            "یکی از گزینه‌ها را انتخاب کنید:",
            reply_markup=keyboard
        )
        return

    if text in ["1", "2", "3"]:
        bot.send_message(
            chat_id,
            f"گزینه {text} ثبت شد."
        )
        return

    if text == "🔍 پیگیری وضعیت سفارش":

        user_state[chat_id] = "WAIT_TRACKING"

        bot.send_message(
            chat_id,
            "کد پیگیری را وارد کنید:"
        )
        return

    if user_state.get(chat_id) == "WAIT_TRACKING":

        tracking_code = text

        bot.send_message(
            chat_id,
            f"کد پیگیری دریافت شد:\n{tracking_code}"
        )

        user_state.pop(chat_id, None)
        return

    if text == "📷 بارگذاری تصویر رسید":

        user_state[chat_id] = "WAIT_IMAGE"

        bot.send_message(
            chat_id,
            "لطفاً تصویر رسید را ارسال کنید."
        )
        return

    if user_state.get(chat_id) == "WAIT_IMAGE" and getattr(message, "file", None):

        bot.send_message(
            ADMIN_ID,
            f"رسید جدید از کاربر {chat_id}"
        )

        # اینجا می‌توانی فایل را برای ادمین فوروارد یا ذخیره کنی

        bot.send_message(
            chat_id,
            "تصویر با موفقیت دریافت شد."
        )

        user_state.pop(chat_id, None)


bot.run()