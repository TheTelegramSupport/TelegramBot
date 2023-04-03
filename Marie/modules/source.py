from platform import python_version as y

from pyrogram import __version__ as z
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram import __version__ as o
from telethon import __version__ as s

from Marie import BOT_NAME, BOT_USERNAME, OWNER_USERNAME, OWNER_ID, START_IMG, pbot


@pbot.on_message(filters.command(["repo", "source"]))
async def repo(_, message: Message):
    await message.reply_photo(
        photo=START_IMG,
        caption=f"""**ʜᴇʏ {message.from_user.mention},

I Am [{BOT_NAME}](https://t.me/{BOT_USERNAME})**

**» My Developer :** [Telegram Support](https://t.me/{OWNER_USERNAME})
**» Python Version :** `{y()}`
**» Library Version :** `{o}` 
**» Telethon Version :** `{s}` 
**» Pyrogram Version :** `{z}`
""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Developer", user_id=OWNER_ID),
                    InlineKeyboardButton(
                        "Source",
                        url="https://t.me/TheTelegramSupport",
                    ),
                ]
            ]
        ),
    )


__mod_name__ = "Repo"
