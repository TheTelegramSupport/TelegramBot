from datetime import datetime

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from Marie import OWNER_ID, START_IMG, SUPPORT_CHAT, pbot
from Marie.utils.errors import capture_err


def content(msg: Message) -> [None, str]:
    text_to_return = msg.text

    if msg.text is None:
        return None
    if " " in text_to_return:
        try:
            return msg.text.split(None, 1)[1]
        except IndexError:
            return None
    else:
        return None


@pbot.on_message(filters.command("bug"))
@capture_err
async def bug(_, msg: Message):
    if msg.chat.username:
        chat_username = f"@{msg.chat.username} [`{msg.chat.id}`]"
    else:
        chat_username = f"Private Group [`{msg.chat.id}`]"
    bugs = content(msg)
    datetimes_fmt = "%d-%m-%Y"
    datetimes = datetime.utcnow().strftime(datetimes_fmt)

    bug_report = f"""
**#Bug**

User ID : `{msg.from_user.id}`
Chat: @{chat_username}
Reported By: {msg.from_user.mention}

Bug: `{bugs}`

Event Stamp: `{datetimes}`"""

    if msg.chat.type == ChatType.PRIVATE:
        return await msg.reply_text("<b>» This Command Is Only For Groups.</b>")

    elif msg.from_user.id == OWNER_ID:
        return await msg.reply_text(
                "<b>» Are You Crazy, You're The Owner Of The Bot.</b>",
            )
    else:
        if bugs:
            await msg.reply_text(
                f"<b>Bug Report :</b> `{bugs}`\n\n"
                "<b>» Bug Successfully Reported At Support Chat!!</b>",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("• Close •", callback_data="close")]]
                ),
            )
            await pbot.send_photo(
                SUPPORT_CHAT,
                photo=START_IMG,
                caption=bug_report,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("• View Bug •", url=msg.link),
                            InlineKeyboardButton("• Close •", callback_data="close_")
                        ],
                    ]
                ),
            )
        else:
            await msg.reply_text(
                f"<b>» No Bug To Report!</b>",
            )


@pbot.on_callback_query(filters.regex("close"))
async def close_reply(_, CallbackQuery):
    await CallbackQuery.message.delete()


@pbot.on_callback_query(filters.regex("close_"))
async def close_send_photo(_, CallbackQuery):
    if CallbackQuery.from_user.id != OWNER_ID:
        return await CallbackQuery.answer(
            "You Don't Have Permissions To Close This !.", show_alert=True
        )
    else:
        await CallbackQuery.message.delete()


__help__ = """
 » `/bug` <text> :  For Reporting Any Bug In Bot 
 """
__mod_name__ = "Bug"
