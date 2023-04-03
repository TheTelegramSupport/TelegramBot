from telethon import events, Button, custom, version
from telethon.tl.types import ChannelParticipantsAdmins
import asyncio
import os,re
import requests
import datetime
import time
from datetime import datetime
import random
from PIL import Image
from io import BytesIO
from Marie import telethn as bot
from Marie import telethn as tgbot
from Marie.events import register
from Marie import dispatcher, BOT_NAME


edit_time = 5
""" =======================Marie====================== """
file1 = "https://telegra.ph/file/dfb9b919a3090f2b44081.jpg"
file2 = "https://telegra.ph/file/dfb9b919a3090f2b44081.jpg"
file3 = "https://telegra.ph/file/dfb9b919a3090f2b44081.jpg"
file4 = "https://telegra.ph/file/dfb9b919a3090f2b44081.jpg"
file5 = "https://telegra.ph/file/dfb9b919a3090f2b44081.jpg"
""" =======================Marie====================== """


@register(pattern="/myinfo")
async def proboyx(event):
    chat = await event.get_chat()
    current_time = datetime.utcnow()
    firstname = event.sender.first_name
    button = [[custom.Button.inline("information",data="informations")]]
    on = await bot.send_file(event.chat_id, file=file2,caption= f"Hello, Dear User {firstname}, \n Click The Below Button \n To Get Your Info", buttons=button)

    await asyncio.sleep(edit_time)
    ok = await bot.edit_message(event.chat_id, on, file=file3, buttons=button) 

    await asyncio.sleep(edit_time)
    ok2 = await bot.edit_message(event.chat_id, ok, file=file5, buttons=button)

    await asyncio.sleep(edit_time)
    ok3 = await bot.edit_message(event.chat_id, ok2, file=file1, buttons=button)

    await asyncio.sleep(edit_time)
    ok7 = await bot.edit_message(event.chat_id, ok6, file=file4, buttons=button)
    
    await asyncio.sleep(edit_time)
    ok4 = await bot.edit_message(event.chat_id, ok3, file=file2, buttons=button)
    
    await asyncio.sleep(edit_time)
    ok5 = await bot.edit_message(event.chat_id, ok4, file=file1, buttons=button)
    
    await asyncio.sleep(edit_time)
    ok6 = await bot.edit_message(event.chat_id, ok5, file=file3, buttons=button)
    
    await asyncio.sleep(edit_time)
    ok7 = await bot.edit_message(event.chat_id, ok6, file=file5, buttons=button)

    await asyncio.sleep(edit_time)
    ok7 = await bot.edit_message(event.chat_id, ok6, file=file4, buttons=button)

@tgbot.on(events.callbackquery.CallbackQuery(data=re.compile(b"information")))
async def callback_query_handler(event):
  try:
    boy = event.sender_id
    PRO = await bot.get_entity(boy)
    LILIE = f"Powered By {BOT_NAME} \n\n"
    LILIE += f"First Name: {PRO.first_name} \n"
    LILIE += f"Last Name: {PRO.last_name}\n"
    LILIE += f"You Bot : {PRO.bot} \n"
    LILIE += f"RESTRICTED : {PRO.restricted} \n"
    LILIE += f"User ID : {boy}\n"
    LILIE += f"Username : {PRO.username}\n"
    await event.answer(LILIE, alert=True)
  except Exception as e:
    await event.reply(f"{e}")


__command_list__ = [
    "myinfo"
]


__help__ = """
 » `/myinfo` Generate Your Own Information.
"""

__mod_name__ = "My-Info"
