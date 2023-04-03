import random, requests, time
from Marie import telethn as asst
from Marie import pbot
from telethon import Button, events
from Marie.events import register
from pyrogram import filters
from pyrogram.types import *
from Marie import SUPPORT_CHAT

@pbot.on_message(filters.command("wish"))
async def wish(_, m):
            if len(m.command) <  2:
                  await m.reply("**Add Wish!**")
                  return 
            api = requests.get("https://nekos.best/api/v2/happy").json()
            url = api["results"][0]['url']
            text = m.text.split(None, 1)[1]
            wish_count = random.randint(1,100)
            wish = f"✨ **Gey, Dear! {m.from_user.first_name}!** "
            wish += f"✨ **Your Wish**: **{text}** "
            wish += f"✨ **Possible To: {wish_count}%**"
            await m.reply_animation(url,caption=(wish),
              reply_markup=InlineKeyboardMarkup(
                    [ [InlineKeyboardButton("Support", url=f"https://t.me/{SUPPORT_CHAT}")]]))
            
         
BUTTON = [[Button.url("Support", f"https://t.me/{SUPPORT_CHAT}")]]
CUTIE = "https://64.media.tumblr.com/d701f53eb5681e87a957a547980371d2/tumblr_nbjmdrQyje1qa94xto1_500.gif"



@asst.on(events.NewMessage(pattern="/cute ?(.*)"))
async def cute(e):
         if not e.is_reply:
              user_id = e.sender.id
              user_name = e.sender.first_name
              mention = f"[{user_name}](tg://user?id={str(user_id)})"
              mm = random.randint(1,100)
              CUTE = f"**🍑** {mention} {mm}**% Lol**"
              await e.reply(CUTE, buttons=BUTTON, file=CUTIE)
         if e.is_reply:
               replied = (await e.get_reply_message())
               id = replied.sender.id
               name = replied.sender.first_name
               mention = f"[{name}](tg://user?id={str(id)})"
               mm = random.randint(1,100)
               CUTE = f"**🍑** {mention} {mm}**% Cute Lol**"
               await e.reply(CUTE, buttons=BUTTON, file=CUTIE)

__help__ = """

» What Us This (Wish):
You Having Any Kind Of
(Wishes) You Can Using This Bot To How Possible To Your Wish!
Example:» /wish : I want To be Class Topper 
» `/wish` : I Want A New Phone 
» `/cute` : How Much I Am Cute

"""

__mod_name__ = "How-All"
