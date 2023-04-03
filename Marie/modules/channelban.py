import html
from typing import Optional
from telegram import (
    ParseMode,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import CallbackContext, Filters, CommandHandler, run_async, CallbackQueryHandler
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html

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
import Marie.modules.sql.users_sql as sql
from Marie.modules.disable import DisableAbleCommandHandler
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
)
from Marie.modules.helper_funcs.extraction import extract_user_and_text
from Marie.modules.helper_funcs.string_handling import extract_time
from Marie.modules.log_channel import gloggable, loggable
from Marie.modules.helper_funcs.anonymous import user_admin, AdminPerms


UNBAN_IMG= "https://telegra.ph/file/9b78eb3d3c8afdd9522ed.jpg"
BAN_IMG= "https://telegra.ph/file/8bbca5d5cfc5e5768b960.jpg"

@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
def cban(update: Update, context: CallbackContext) -> Optional[str]: 
    chat = update.effective_chat  
    user = update.effective_user 
    message = update.effective_message 
    args = context.args
    bot = context.bot
    log_message = ""
    reason = ""
    if message.reply_to_message and message.reply_to_message.sender_chat:
        r = bot._request.post(bot.base_url + '/banChatSenderChat', {
            'sender_chat_id': message.reply_to_message.sender_chat.id,
            'chat_id': chat.id
        },
                              )
        if r:
            message.reply_video(BAN_IMG,caption="Channel {} Was Banned Successfully From {} .".format(
                html.escape(message.reply_to_message.sender_chat.title),
                html.escape(chat.title)
            ),
                parse_mode="html"
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#Channel\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>Channel:</b> {mention_html(channel.id, html.escape(chat.title))} ({message.reply_to_message.sender_chat.id})"
            )
        else:
            message.reply_text("Failed To Ban Channel")
        return

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("I Doubt That's A User.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        message.reply_text("Can't Seem To Find This Person.")
        return log_message
    if user_id == context.bot.id:
        message.reply_text("Oh Yeah, Ban Myself lol")
        return log_message

    if is_user_ban_protected(update, user_id, member) and user not in DEV_USERS:
        if user_id == OWNER_ID:
            message.reply_text("I'd Never Ban My Owner.")
        elif user_id in DEV_USERS:
            message.reply_text("I Can't Act Against Our Own.")
        elif user_id in DRAGONS:
            message.reply_text("My Sudos Are Ban Immune")
        elif user_id in DEMONS:
            message.reply_text("My Support Users Are Ban Immune")
        elif user_id in TIGERS:
            message.reply_text("Sorry, He Is Tiger Level Disaster.")
        elif user_id in WOLVES:
            message.reply_text("Neptunians Are Ban Immune!")
        else:
            message.reply_text("This User Has Immunity And Can't Be Banned.")
        return log_message
    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#Banned\n"
        f"<b>Banned:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
    )
    if reason:
        log += "\n<b>Reason:</b> {} okay".format(reason)

    try:
        chat.ban_member(user_id)
        # context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        context.bot.sendMessage(
            chat.id,
            "{} Was Banned By {} In <b>{}</B> \n<b>Reason</b>: <code>{}</code>".format(
                mention_html(member.user.id, member.user.first_name), mention_html(user.id, user.first_name),
                message.chat.title, reason
            ),
            parse_mode=ParseMode.HTML,
        )
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("Banned!", quote=False)
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
            message.reply_text("Well Damm I Can't Ban That User.")

    return ""
  
@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
def uncban(update: Update, context: CallbackContext) -> Optional[str]:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""
    bot, args = context.bot, context.args
    if message.reply_to_message and message.reply_to_message.sender_chat:
        r = bot.unban_chat_sender_chat(chat_id=chat.id, sender_chat_id=message.reply_to_message.sender_chat.id)
        if r:
            message.reply_video(UNBAN_IMG,caption="Channel {} Was Unbanned Successfully From {} .".format(
                html.escape(message.reply_to_message.sender_chat.title),
                html.escape(chat.title)
            ),
                parse_mode="html"
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UnCbanned\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>Channel:</b> {html.escape(message.reply_to_message.sender_chat.title)} ({message.reply_to_message.sender_chat.id})"
            )
        else:
            message.reply_text("Failed To Unban Channel")
        return
    user_id, reason = extract_user_and_text(message, args)
    if not user_id:
        message.reply_text("I Doubt That's A User.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != 'User not found':
            raise
        message.reply_text("I Can't Seem To Find This User.")
        return log_message
    if user_id == bot.id:
        message.reply_text("How Would I Unban Myself If I Wasn't Here...?")
        return log_message

    if is_user_in_chat(chat, user_id):
        message.reply_text("Isn't This Person Already Here??")
        return log_message

    chat.unban_member(user_id)
    bot.sendMessage(
        chat.id,
        "{} Was Unbanned By {} In <b>{}</b> .\n<b>Reason</b>: <code>{}</code>".format(
            mention_html(member.user.id, member.user.first_name), mention_html(user.id, user.first_name),
            message.chat.title, reason
        ),
        parse_mode=ParseMode.HTML,
    )

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UnCbanned\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
    )
    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    return log
    
    
UNCBAN_HANDLER = CommandHandler(["channelunban", "uncban"], uncban)
CBAN_HANDLER = CommandHandler(["cban", "channelban"], cban)
    
dispatcher.add_handler(UNCBAN_HANDLER)
dispatcher.add_handler(CBAN_HANDLER)
    
    
    
