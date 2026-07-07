import asyncio
from rubpy import Client, filters
from rubpy.types import Update

TOKEN = "BIJFAB0MVHQAPLZSKUQLWKYWBTLDWCEQCCBHOXLCLXUUARAVJTITTEJHIHWYMCOX"

client = Client(token=TOKEN)

@client.on_message(filters.text)
async def handle_message(update: Update):
    chat_id = update.chat_id
    text = update.text
    
    if text == "/start":
        # کیبورد با چهار دکمه
        keyboard = {
            "keyboard": [
                [{"text": "🛍️ ثبت سفارش جدید"}],
                [{"text": "💰 ارسال رسید پرداخت"}],
                [{"text": "✏️ تغییر سفارش"}],
                [{"text": "🔍 پیگیری سفارش"}]
            ],
            "resize_keyboard": True
        }
        await client.send_message(
            chat_id=chat_id,
            text="سلام! به ربات خوش آمدید.\nلطفاً از منو استفاده کنید:",
            reply_markup=keyboard
        )
    else:
        await client.send_message(
            chat_id=chat_id,
            text=f"شما گفتید: {text}"
        )

if __name__ == "__main__":
    client.run()