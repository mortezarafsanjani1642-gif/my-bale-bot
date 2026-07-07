from rubka.asynco import Robot
from rubka.context import Message
import asyncio

BOT_TOKEN = "BIJFAB0MVHQAPLZSKUQLWKYWBTLDWCEQCCBHOXLCLXUUARAVJTITTEJHIHWYMCOX"

bot = Robot(token=BOT_TOKEN)

@bot.on_message(commands=["start"])
async def start(bot: Robot, message: Message):
    info_text = f"""===== اطلاعات شما =====
Chat ID: {message.chat_id}
User GUID : {message.author_guid}
Object GUID: {message.object_guid}
========================"""
    print(info_text)
    await message.reply(info_text)

asyncio.run(bot.run())