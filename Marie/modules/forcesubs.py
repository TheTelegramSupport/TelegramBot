import logging
import time

from pyrogram import filters
from pyrogram.errors.exceptions.bad_request_400 import (
    ChatAdminRequired,
    PeerIdInvalid,
    UsernameNotOccupied,
    UserNotParticipant,
)
from pyrogram.types import ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup

from Marie import DRAGONS as SUDO_USERS
from Marie import pbot
from Marie.modules.sql import forceSubscribe_sql as sql

logging.basicConfig(level=logging.INFO)

static_data_filter = filters.create(
    lambda _, __, query: query.data == "onUnMuteRequest"
)


@pbot.on_callback_query(static_data_filter)
def _onUnMuteRequest(client, cb):
    user_id = cb.from_user.id
    chat_id = cb.message.chat.id
    chat_db = sql.fs_settings(chat_id)
    if chat_db:
        channel = chat_db.channel
        chat_member = client.get_chat_member(chat_id, user_id)
        if chat_member.restricted_by:
            if chat_member.restricted_by.id == (client.get_me()).id:
                try:
                    client.get_chat_member(channel, user_id)
                    client.unban_chat_member(chat_id, user_id)
                    cb.message.delete()
                    # if cb.message.reply_to_message.from_user.id == user_id:
                    # cb.message.delete()
                except UserNotParticipant:
                    client.answer_callback_query(
                        cb.id,
                        text=f"Join Our @{channel} Channel And Press 'Unmute Me' Button.",
                        show_alert=True,
                    )
            else:
                client.answer_callback_query(
                    cb.id,
                    text="❗ You Have Been Muted By Admins Due To Some Other Reason.",
                    show_alert=True,
                )
        else:
            if (not client.get_chat_member(chat_id, (client.get_me()).id).status == "administrator"
            ):
                client.send_message(
                    chat_id,
                    f" **{cb.from_user.mention} Is Trying To Unmute Himself But I Can't Unmute Him Because I'm Not An admin In This Chat Add Me As Admin Again.**\n__#Leaving This Chat...__",
                )

            else:
                client.answer_callback_query(
                    cb.id,
                    text="Warning! Don't Press The Button When You Can Talk.",
                    show_alert=True,
                )


@pbot.on_message(filters.text & ~filters.private, group=1)
def _check_member(client, message):
    chat_id = message.chat.id
    chat_db = sql.fs_settings(chat_id)
    if chat_db:
        user_id = message.from_user.id
        if (not client.get_chat_member(chat_id, user_id).status in ("administrator", "creator")
            and not user_id in SUDO_USERS
        ):
            channel = chat_db.channel
            try:
                client.get_chat_member(channel, user_id)
            except UserNotParticipant:
                try:
                    sent_message = message.reply_text(
                        "Welcome, Dear {} 🙏 \n **You Haven't Joined Our @{} Channel Yet **👷 \n \nPlease Join [Our Channel](https://t.me/{}) And Hit The **Unmute Me** Button. \n \n ".format(
                            message.from_user.mention, channel, channel
                        ),
                        disable_web_page_preview=True,
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(
                                        "Join Channel",
                                        url="https://t.me/{}".format(channel),
                                    )
                                ],
                                [
                                    InlineKeyboardButton(
                                        "Unmute Me", callback_data="onUnMuteRequest"
                                    )
                                ],
                            ]
                        ),
                    )
                    client.restrict_chat_member(
                        chat_id, user_id, ChatPermissions(can_send_messages=False)
                    )
                except ChatAdminRequired:
                    sent_message.edit(
                        " **Bot Is Not Admin Here..**\n__Give Me Ban Permissions And Retry.. \n#Ending Fsub...__"
                    )

            except ChatAdminRequired:
                client.send_message(
                    chat_id,
                    text=f" **I'm Not An Admin Of @{channel} Channel.**\n__Give Me Admin Of That Channel And Retry.\n#Ending Fsub...__",
                )


@pbot.on_message(filters.command(["forcesubscribe", "fsub"]) & ~filters.private)
def config(client, message):
    user = client.get_chat_member(message.chat.id, message.from_user.id)
    if user.status == "creator" or user.user.id in SUDO_USERS:
        chat_id = message.chat.id
        if len(message.command) > 1:
            input_str = message.command[1]
            input_str = input_str.replace("@", "")
            if input_str.lower() in ("off", "no", "disable"):
                sql.disapprove(chat_id)
                message.reply_text(" **Force Subscribe Is Disabled Successfully.**")
            elif input_str.lower() in ("clear"):
                sent_message = message.reply_text(
                    "**Unmuting All Members Who Are Muted By Me...**"
                )
                try:
                    for chat_member in client.get_chat_members(
                        message.chat.id, filter="restricted"
                    ):
                        if chat_member.restricted_by.id == (client.get_me()).id:
                            client.unban_chat_member(chat_id, chat_member.user.id)
                            time.sleep(1)
                    sent_message.edit(" **Unmuted All Members Who Are Muted By Me.**")
                except ChatAdminRequired:
                    sent_message.edit(
                        "**I'm Not An admin In This Chat.**\n__I Can't Unmute Members Because I Am Not An Admin In This Chat Make Me Admin With Ban User Permission.__"
                    )
            else:
                try:
                    client.get_chat_member(input_str, "me")
                    sql.add_channel(chat_id, input_str)
                    message.reply_text(
                        f" **Force Subscribe Is Enabled**\n__Force Subscribe Is Enabled, All The Group Members Have Yo Subscribe This [Channel](https://ᴛ.ᴍᴇ/{input_str}) In Order To Send Message In This Group.__",
                        disable_web_page_preview=True,
                    )
                except UserNotParticipant:
                    message.reply_text(
                        f" **Not An Admin In The Channel**\n__I Am Not An Admin In The [Channel](https://t.me/{input_str}).Add Me As An Admin In Order To Enable ForceSubscribe.__",
                        disable_web_page_preview=True,
                    )
                except (UsernameNotOccupied, PeerIdInvalid):
                    message.reply_text(f"**Invalid Channel Username.**")
                except Exception as err:
                    message.reply_text(f"**Error:** ```{err}``` .")
        else:
            if sql.fs_settings(chat_id):
                message.reply_text(
                    f" **Force Subscribe Is Enabled In This Chat.**\n__For This [Channel](https://t.me/{sql.fs_settings(chat_id).channel})__",
                    disable_web_page_preview=True,
                )
            else:
                message.reply_text("**Force Subscribe Is Disabled In This Chat.**")
    else:
        message.reply_text(
            "❗ **Group Creator Required**\n__You Have To Be The Group Creator To Do That.__"
        )


__help__ = """
» `/fsub` {channel username} - To Turn On And Setup The Channel.
  💡Do This First...
» `/fsub` - To Get The Current Settings.
» `/fsub disable` - To Turn Of ForceSubscribe..
💡If you Disable Fsub, You Need To Set Again For Working.. /fsub {channel username} 
» `/fsub clear` - To Unmute All Members Who Muted By Me.

"""
__mod_name__ = "F-Sub"
