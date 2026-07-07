from rubpy import BotClient
from rubpy.bot import filters
from rubpy.bot.models import Update

TOKEN = "BIJFAB0MVHQAPLZSKUQLWKYWBTLDWCEQCCBHOXLCLXUUARAVJTITTEJHIHWYMCOX"

bot = BotClient(token=TOKEN)

@bot.on_update(filters.commands("start"))
async def handle_start(bot: BotClient, update: Update):
    # ✅ کیبورد به صورت دیکشنری ساده (بدون ButtonTypeEnum)
    keyboard = {
        "keyboard": [
            [{"text": "🛍️ ثبت سفارش جدید"}],
            [{"text": "💰 ارسال رسید پرداخت"}],
            [{"text": "✏️ تغییر سفارش"}],
            [{"text": "🔍 پیگیری سفارش"}]
        ],
        "resize_keyboard": True
    }
    
    await update.reply(
        "سلام! به ربات خوش آمدید.\nلطفاً از منو استفاده کنید:",
        reply_markup=keyboard
    )

@bot.on_update(filters.text)
async def handle_text(bot: BotClient, update: Update):
    text = update.new_message.text
    await update.reply(f"شما گفتید: {text}")

if __name__ == "__main__":
    bot.run()