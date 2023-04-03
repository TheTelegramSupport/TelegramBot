import random

from pyrogram import __version__ as pyrover
from telegram import __version__ as telever
from telethon import Button
from telethon import __version__ as tlhver

from Marie import OWNER_USERNAME, SUPPORT_CHAT, dispatcher
from Marie import telethn as tbot
from Marie.events import register

PHOTO = [
    "https://telegra.ph/file/dfb9b919a3090f2b44081.jpg",
    "https://telegra.ph/file/dfb9b919a3090f2b44081.jpg",
]


@register(pattern=("/alive"))
async def awake(event):
    TEXT = f"**Hello Sir/Mam​ [{event.sender.first_name}](tg://user?id={event.sender.id}),\n\nI'm {dispatcher.bot.first_name}**\n━━━━━━━━━━━━━━━━━━━\n\n"
    TEXT += f"» **My Developer​ : [Telegram Support](https://t.me/{OWNER_USERNAME})\n\n"
    TEXT += f"» **Library Version :** `{telever}` \n\n"
    TEXT += f"» **Telethon Version :** `{tlhver}` \n\n"
    TEXT += f"» **Pyrogram Version:** `{pyrover}` \n━━━━━━━━━━━━━━━━━\n\n"
    BUTTON = [
        [
            Button.url("Help​", f"https://t.me/{dispatcher.bot.username}?start=help"),
            Button.url("Support​", f"https://t.me/{SUPPORT_CHAT}"),
        ]
    ]
    ran = random.choice(PHOTO)
    await tbot.send_file(event.chat_id, ran, caption=TEXT, buttons=BUTTON)


__mod_name__ = "Alive"
