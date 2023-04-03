import html
import random

from time import sleep
from telegram import (
    ParseMode,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.error import BadRequest
from telegram.ext import CallbackContext, Filters, CommandHandler, run_async, CallbackQueryHandler
from telegram.utils.helpers import mention_html
from typing import Optional, List
from telegram import TelegramError

import Marie.modules.sql.users_sql as sql
from Marie.modules.disable import DisableAbleCommandHandler
from Marie.modules.helper_funcs.filters import CustomFilters
from Marie import (
    DEV_USERS,
    LOGGER,
    OWNER_ID,
    DRAGONS,
    DEMONS,
    TIGERS,
    WOLVES,
    dispatcher,
)
from Marie.modules.helper_funcs.chat_status import (
    user_admin_no_reply,
    bot_admin,
    can_restrict,
    connection_status,
    is_user_admin,
    is_user_ban_protected,
    is_user_in_chat,
    user_admin,
    user_can_ban,
    can_delete,
    dev_plus,
)
from Marie.modules.helper_funcs.extraction import extract_user_and_text
from Marie.modules.helper_funcs.string_handling import extract_time
from Marie.modules.log_channel import gloggable, loggable



@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def ban(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot = context.bot
    args = context.args
    reason = ""
    if message.reply_to_message and message.reply_to_message.sender_chat:
        r = bot.ban_chat_sender_chat(chat_id=chat.id, sender_chat_id=message.reply_to_message.sender_chat.id)
        if r:
            message.reply_text("Channel {} Was Banned Successfully From {} ..".format(
                html.escape(message.reply_to_message.sender_chat.title),
                html.escape(chat.title)
            ),
                parse_mode="html"
            )
        else:
            message.reply_text("Failed To Ban Channel")
        return

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("User not found.")
        return log_message
    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise
        message.reply_text("Can't Seem To Find This Person.")
        return log_message
    if user_id == bot.id:
        message.reply_text("Oh yeah, Ban Myself, Noom!")
        return log_message

    if is_user_ban_protected(chat, user_id, member) and user not in DEV_USERS:
        if user_id == OWNER_ID:
            message.reply_text("Trying To Put Me Against A King Huh?")
        elif user_id in DEV_USERS:
            message.reply_text("I Can't Act Against Our Prince.")
        elif user_id in DRAGONS:
            message.reply_text(
                "Fighting This Emperor Here Will Put User Lives At Risk."
            )
        elif user_id in DEMONS:
            message.reply_text(
                "Bring An Order From Captain To Fight A Assasing Servent."
            )
        elif user_id in TIGERS:
            message.reply_text(
                "Bring An Order From Soldier To Fight A Lancer Servent"
            )
        elif user_id in WOLVES:
            message.reply_text("Trader Access Make Them Ban Immune!")
        else:
            message.reply_text("I Cannot Banned Admin.")
        return log_message
    if message.text.startswith("/s"):
        silent = True
        if not can_delete(chat, context.bot.id):
            return ""
    else:
        silent = False
    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#{'S' if silent else ''}Banned\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )
    if reason:
        log += "<b>Reason:</b> {} ..".format(reason)

    try:
        chat.ban_member(user_id)

        if silent:
            if message.reply_to_message:
                message.reply_to_message.delete()
            message.delete()
            return log

        # bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        reply = (
            f"{mention_html(member.user.id, html.escape(member.user.first_name))} [<code>{member.user.id}</code>] Banned."
        )
        if reason:
            reply += f"\nReason: {html.escape(reason)} .."

        bot.sendMessage(
            chat.id,
            reply,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="🔄  Unban", callback_data=f"unbanb_unban={user_id}"
                        ),
                        InlineKeyboardButton(text="🗑️  Delete", callback_data="unbanb_del"),
                    ]
                ]
            ),
            parse_mode=ParseMode.HTML,
        )
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            if silent:
                return log
            message.reply_text("Banned User!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Huh...That Didn't Work...")

    return log_message


@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def temp_ban(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("User Not Found.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise
        message.reply_text("I Can't Seem To Find This User.")
        return log_message
    if user_id == bot.id:
        message.reply_text("I'm Not Gonna Ban Myself, Are You Crazy?..Lol")
        return log_message

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("I Don't Feel Like It.")
        return log_message

    if not reason:
        message.reply_text("You Haven't Specified A Time To Ban This User For!")
        return log_message

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    bantime = extract_time(message, time_val)

    if not bantime:
        return log_message

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        "#Temp_Banned\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}\n"
        f"<b>Time:</b> {time_val}"
    )
    if reason:
        log += "\nReason: {} ʙᴀʙʏ🥀".format(reason)

    try:
        chat.ban_member(user_id, until_date=bantime)
        # bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker

        reply_msg = (
            f"{mention_html(member.user.id, html.escape(member.user.first_name))} [<code>{member.user.id}</code>] Temporary Banned"
            f" For (`{time_val}`). .."
        )

        if reason:
            reply_msg += f"\nReason: `{html.escape(reason)}` ."

        bot.sendMessage(
            chat.id,
            reply_msg,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="🔄  Unban", callback_data=f"unbanb_unban={user_id}"
                        ),
                        InlineKeyboardButton(text="🗑️  Delete", callback_data="unbanb_del"),
                    ]
                ]
            ),
            parse_mode=ParseMode.HTML,
        )
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(
                f"{mention_html(member.user.id, html.escape(member.user.first_name))} [<code>{member.user.id}</code>] Banned For {time_val} ..", quote=False
            )
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Well Damn, I Can't Ban That User.")

    return log_message


@connection_status
@bot_admin
@can_restrict
@user_admin_no_reply
@user_can_ban
@loggable
def unbanb_btn(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    query = update.callback_query
    chat = update.effective_chat
    user = update.effective_user
    if query.data != "unbanb_del":
        splitter = query.data.split("=")
        query_match = splitter[0]
        if query_match == "unbanb_unban":
            user_id = splitter[1]
            if not is_user_admin(chat, int(user.id)):
                bot.answer_callback_query(
                    query.id,
                    text="You Don't Have Enough Right To Unmute People",
                    show_alert=True,
                )
                return ""
            log_message = ""
            try:
                member = chat.get_member(user_id)
            except BadRequest:
                pass
            chat.unban_member(user_id)
            query.message.edit_text(
                f"{member.user.first_name} [{member.user.id}] Unbanned."
            )
            bot.answer_callback_query(query.id, text="Unbanned!")
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#Unbanned\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
            )

    else:
        if not is_user_admin(chat, int(user.id)):
            bot.answer_callback_query(
                query.id,
                text="You Don't Have Enough Rights To Delete This Message.",
                show_alert=True,
            )
            return ""
        query.message.delete()
        bot.answer_callback_query(query.id, text="Deleted..!")
        return ""

    
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def punch(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("User Not Found")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        message.reply_text("I Can't Seem To Find This User.")
        return log_message
    if user_id == bot.id:
        message.reply_text(".Yeahhh I'm Not Gonna Do That")
        return log_message

    if is_user_ban_protected(chat, user_id):
        message.reply_text("I Really Wish I Could Punch This User...")
        return log_message

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        # bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        bot.sendMessage(
            chat.id,
            f"{mention_html(member.user.id, html.escape(member.user.first_name))} [<code>{member.user.id}</code>] Kicked.",
            parse_mode=ParseMode.HTML
        )
        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#Kicked\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        )
        if reason:
            log += f"\n<b>Reason:</b> {reason} ."

        return log

    else:
        message.reply_text("Well Damn, I Can't Punch That User.")

    return log_message



@bot_admin
@can_restrict
def punchme(update: Update, context: CallbackContext):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("I Wish, I Could.....But You're An Admin .")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text(
            "Punches You Out Of The Group!!",
        )
    else:
        update.effective_message.reply_text("Huh? I Can't. ")


@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def unban(update: Update, context: CallbackContext) -> Optional[str]:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""
    bot, args = context.bot, context.args
    if message.reply_to_message and message.reply_to_message.sender_chat:
        r = bot.unban_chat_sender_chat(chat_id=chat.id, sender_chat_id=message.reply_to_message.sender_chat.id)
        if r:
            message.reply_text("Channel {} Was Unbanned Successfully From {} .".format(
                html.escape(message.reply_to_message.sender_chat.title),
                html.escape(chat.title)
            ),
                parse_mode="html"
            )
        else:
            message.reply_text("Failed To Unban Channel")
        return

    user_id, reason = extract_user_and_text(message, args)
    if not user_id:
        message.reply_text("User Not Found.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise
        message.reply_text("I Can't Seem To Find This User.")
        return log_message
    if user_id == bot.id:
        message.reply_text("How Would I Unban Myself If I Wasn't Here...?")
        return log_message

    if is_user_in_chat(chat, user_id):
        message.reply_text(f"User Not Found .")
        return log_message

    chat.unban_member(user_id)
    message.reply_text(
        f"{member.user.first_name} [{member.user.id}] Unbanned.."
    )

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )
    if reason:
        log += f"\n<b>Reason:</b> {reason}.."

    return log


@connection_status
@bot_admin
@can_restrict
@gloggable
def selfunban(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    if user.id not in DRAGONS or user.id not in TIGERS:
        return

    try:
        chat_id = int(args[0])
    except:
        message.reply_text("Give Me A Valid Chat Id.")
        return

    chat = bot.getChat(chat_id)

    try:
        member = chat.get_member(user.id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I Can't Seem To Find This User.")
            return
        else:
            raise

    if is_user_in_chat(chat, user.id):
        message.reply_text("Aren't You Already In The Chat??")
        return

    chat.unban_member(user.id)
    message.reply_text(f"Yep, I Have Unbanned The User.")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))} ."
    )

    return log


@bot_admin
@can_restrict
@loggable
def banme(update: Update, context: CallbackContext):
    user_id = update.effective_message.from_user.id
    chat = update.effective_chat
    user = update.effective_user
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("I Cannot Banned Admin.")
        return

    res = update.effective_chat.ban_member(user_id)
    if res:
        update.effective_message.reply_text("Yes, You're Right")
        return (
            "<b>{}:</b>"
            "\n#Banme"
            "\n<b>User:</b> {}"
            "\n<b>ID:</b> <code>{}</code>".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                user_id,
            )
        )

    else:
        update.effective_message.reply_text("Huh? I Can't.")


@dev_plus
def snipe(update: Update, context: CallbackContext):
    args = context.args
    bot = context.bot
    try:
        chat_id = str(args[0])
        del args[0]
    except TypeError:
        update.effective_message.reply_text("Please Give Me A Chat To Echo To!")
    to_send = " ".join(args)
    if len(to_send) >= 2:
        try:
            bot.sendMessage(int(chat_id), str(to_send))
        except TelegramError:
            LOGGER.warning("Couldn't send to group %s", str(chat_id))
            update.effective_message.reply_text(
                "Couldn't Send The Message Perhaps I'm Not Part Of That Group?"
            )


__help__ = """
*User Commands:*

» `/kickme`*:* Kicks The User Whi Issued The Command 

*Admins Only:*

» `/ban` <Userhandle>*:* Bans A User.(Via Handle, Or Reply)
» `/sban` <Userhandle>*:* Silently Ban A User. Deletew Command, Replied Message And Doesn't Reply. (Via Handle, Or Reply)
» `/tban` <Userhandle> X(M/H/D)*:* Bans A User X Time. (Via Handle, Or Reply). M = Minutes, H = Hours, D = Days.
» `/unban` <Userhandle>*:* Unbans A User. (Via Handle, Or Reply)
» `/kick` <Userhandle>*:* Kicks A User Out Of The Group, (Via Handle, Or Reply)
» `/mute` <Userhandle>*:* Silence A User, Can Also Be Used As A Reply, Muting The Replied To User.
» `/tmute` <Userhandle> X(M/H/D)*:* Mutes A User For X Time. (Via Handle, Or Reply). M = Minutes, H = Hours, D = Days.
» `/unmute` <Userhandle>*:* Unmutes A User. Can Also Be Used As A Reply, Muting The Replied To User.

*Channel Bans*

`/channelban`*:* Bans Channel Action In Your Group
`/cban`*:* Bans Channel Action In Your Group 
`/channelunban`*:* Unbans Channel Action in Your Group 
`/uncban`*:* Bans Channel Action In Your Group

*Global~Bans*

`/gmute`*:* Globally Mutes User Which Has Been Tagged 
`/ungmute`*:* Globally unmutes User Which Has Been Tagged
`/gmutelist`*:* List Of G-Mute Users In The Database 
`/gmutespam`*:* G-Mute For Spamming 
`/gban`*:* Globally Bans A User Which Has Been Tagged 
`/ungban`*:* Globally Unbans A User Which Has Been Tagged 
`/gbanlist`*:* List Of All G-Ban Users In The Database 

*Remote commands:*

 » `/rban`*:* user group*:* Remote Ban 
 » `/runban`*:* user group*:* Remote Unban
 » `/rpunch`*:* user group*:* Remote Kick
 » `/rmute`*:* user group*:* Remote Mute
 » `/runmute`*:* user group*:* Remote Unmute 
"""


__mod_name__ = "Bans"

BAN_HANDLER = CommandHandler(["ban", "sban"], ban, run_async=True)
TEMPBAN_HANDLER = CommandHandler(["tban"], temp_ban, run_async=True)
KICK_HANDLER = CommandHandler(["kick", "punch"], punch, run_async=True)
UNBAN_HANDLER = CommandHandler("unban", unban, run_async=True)
ROAR_HANDLER = CommandHandler("roar", selfunban, run_async=True)
UNBAN_BUTTON_HANDLER = CallbackQueryHandler(unbanb_btn, pattern=r"unbanb_")
KICKME_HANDLER = DisableAbleCommandHandler(["kickme", "punchme"], punchme, filters=Filters.chat_type.groups, run_async=True)
SNIPE_HANDLER = CommandHandler("snipe", snipe, pass_args=True, filters=CustomFilters.sudo_filter, run_async=True)
BANME_HANDLER = CommandHandler("banme", banme, run_async=True)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(ROAR_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(UNBAN_BUTTON_HANDLER)
dispatcher.add_handler(SNIPE_HANDLER)
dispatcher.add_handler(BANME_HANDLER)

__handlers__ = [
    BAN_HANDLER,
    TEMPBAN_HANDLER,
    KICK_HANDLER,
    UNBAN_HANDLER,
    ROAR_HANDLER,
    KICKME_HANDLER,
    UNBAN_BUTTON_HANDLER,
    SNIPE_HANDLER,
    BANME_HANDLER,
]
