from rubpy import BotClient
from rubpy.bot import filters
from rubpy.bot.models import Update, Keypad, KeypadRow, Button, ButtonTypeEnum

TOKEN = "BIJFAB0MVHQAPLZSKUQLWKYWBTLDWCEQCCBHOXLCLXUUARAVJTITTEJHIHWYMCOX"

# ====== راه‌اندازی ربات ======
bot = BotClient(token=TOKEN)

# ====== دستور /start ======
@bot.on_update(filters.commands("start"))
async def handle_start(bot: BotClient, update: Update):
    # ساخت کیبورد با ۴ دکمه
    keypad = Keypad(
        rows=[
            KeypadRow(
                buttons=[
                    Button(
                        id="1",
                        type=ButtonTypeEnum.TEXT,
                        button_text="🛍️ ثبت سفارش جدید"
                    )
                ]
            ),
            KeypadRow(
                buttons=[
                    Button(
                        id="2",
                        type=ButtonTypeEnum.TEXT,
                        button_text="💰 ارسال رسید پرداخت"
                    )
                ]
            ),
            KeypadRow(
                buttons=[
                    Button(
                        id="3",
                        type=ButtonTypeEnum.TEXT,
                        button_text="✏️ تغییر سفارش"
                    )
                ]
            ),
            KeypadRow(
                buttons=[
                    Button(
                        id="4",
                        type=ButtonTypeEnum.TEXT,
                        button_text="🔍 پیگیری سفارش"
                    )
                ]
            )
        ],
        resize_keyboard=True,
        on_time_keyboard=False
    )
    
    await update.reply(
        "سلام! به ربات خوش آمدید.\nلطفاً از منو استفاده کنید:",
        inline_keypad=keypad
    )

# ====== دریافت پیام‌های معمولی ======
@bot.on_update(filters.text)
async def handle_text(bot: BotClient, update: Update):
    text = update.new_message.text
    await update.reply(f"شما گفتید: {text}")

# ====== اجرا ======
if __name__ == "__main__":
    bot.run()