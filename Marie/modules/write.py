from pyrogram import filters
from Marie import pbot, BOT_NAME, BOT_USERNAME 

@pbot.on_message(filters.command("write"))
async def write(_, message):
    if len(message.command) < 2 :
            return await message.reply_text("`Please Given Me Text To Write`")
    m = await message.reply_text("`Writting...`")
    name = message.text.split(None, 1)[1] if len(message.command) < 3 else message.text.split(None, 1)[1].replace(" ", "%20")
    hand = "https://apis.xditya.me/write?text=" + name
    await m.edit("`Uploading...`")
    await m.delete()
    await message.reply_photo(hand, caption = f"**Made By [{BOT_NAME}](https://t.me/{BOT_USERNAME})**")


__help__ = """
» `/write` <text> : Writes The Given Text.
"""

__mod_name__ = "Write"
