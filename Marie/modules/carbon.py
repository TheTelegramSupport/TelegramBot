from platform import python_version as y
from telegram import __version__ as o
from pyrogram import __version__ as z
from telethon import __version__ as s
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import filters
from Marie import pbot
from Marie.utils.errors import capture_err
from Marie.utils.functions import make_carbon


@pbot.on_message(filters.command("carbon"))
@capture_err
async def carbon_func(_, message):
    if not message.reply_to_message:
        return await message.reply_text("`Reply To A Text Message To Make Carbon.`")
    if not message.reply_to_message.text:
        return await message.reply_text("`Reply To A Tedt Message To Make Carbon.`")
    m = await message.reply_text("`Preparing Carbon`")
    carbon = await make_carbon(message.reply_to_message.text)
    await m.edit("`Uploading`")
    await pbot.send_photo(message.chat.id, carbon)
    await m.delete()
    carbon.close()


__mod_name__ = "Carbon"

__help__ = """
» `/carbon` *:* Makes Carbon If Replied To A Text 

 """
