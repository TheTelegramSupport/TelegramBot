import html
import re
from typing import Optional

from Marie import LOGGER, TIGERS, dispatcher
from Marie.modules.helper_funcs.chat_status import (
    bot_admin,
    can_restrict,
    connection_status,
    is_user_admin,
    user_admin,
    user_admin_no_reply,
)
from Marie.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from Marie.modules.helper_funcs.string_handling import extract_time
from Marie.modules.log_channel import loggable
from telegram import (
    Bot, 
    Chat, 
    ChatPermissions, 
    ParseMode, 
    Update, 
    User, 
    CallbackQuery,
    InlineKeyboardButton, 
    InlineKeyboardMarkup
)
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, run_async, CallbackQueryHandler
from telegram.utils.helpers import mention_html


def check_user(user_id: int, bot: Bot, chat: Chat) -> Optional[str]:
    
    if not user_id:
        reply = "User Not Found"
        return reply

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "user not found":
            reply = "I Can't Seem To Find This User"
            return reply
        raise

    if user_id == bot.id:
        reply = "I'm Not Gonna Mute Myself, How High Are You?"
        return reply

    if is_user_admin(chat, user_id, member) or user_id in TIGERS:
        reply = "Can't. Find Someone Else To Mute But Not This One."
        return reply

    return None


@connection_status
@bot_admin
@user_admin
@loggable
def mute(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    
    user_id, reason = extract_user_and_text(message, args)
    reply = check_user(user_id, bot, chat)
   

    if reply:
        message.reply_text(reply)
        return ""

    
    member = chat.get_member(user_id)

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#Mute\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    if reason:
        log += f"<b>Reason:</b> {reason}"

    if member.can_send_messages is None or member.can_send_messages:
        chat_permissions = ChatPermissions(can_send_messages=False)
        bot.restrict_chat_member(chat.id, user_id, chat_permissions)    
        msg = (
            f"{mention_html(member.user.id, member.user.first_name)} [<code>{member.user.id}</code>] Is Now Muted."
            )
        if reason:
            msg += f"\nReason: {html.escape(reason)}   Shut up."

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "Unmute", callback_data="unmute_({})".format(member.user.id))
        ]])
        bot.sendMessage(
            chat.id,
            msg,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
        return log
    message.reply_text("This User Is Already Muted!")

    return ""
            	
            	         
@connection_status
@bot_admin
@user_admin
@loggable
def unmute(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = extract_user_and_text(message, args)
    if not user_id:
        message.reply_text(
            "You'll Need To Either Give Me A Username To Unmute, Or Reply To Someone To Be Unmuted."
        )
        return ""

    member = chat.get_member(int(user_id))

    if member.status in ("kicked", "left"):
        message.reply_text(
            "This User Isn't Even In The Chat, Unmuting Then Won't Make Them Talk More Than They"
            "Already Done!",
        )

    elif (
            member.can_send_messages
            and member.can_send_media_messages
            and member.can_send_other_messages
            and member.can_add_web_page_previews
        ):
        message.reply_text("This User Already Had The Right To Speak .")
    else:
        chat_permissions = ChatPermissions(
            can_send_messages=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_send_polls=True,
            can_change_info=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
        )
        try:
            bot.restrict_chat_member(chat.id, int(user_id), chat_permissions)
        except BadRequest:
            pass
        bot.sendMessage(
        chat.id,
        "{} [<code>{}</code>] Was Unmuted .".format(
            mention_html(member.user.id, member.user.first_name), member.user.id
        ),
        parse_mode=ParseMode.HTML,
        )
        return (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#Unmute\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
        )
    return ""


@connection_status
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_mute(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = extract_user_and_text(message, args)
    reply = check_user(user_id, bot, chat)


    if reply:
        message.reply_text(reply)
        return ""

    member = chat.get_member(user_id)

    if not reason:
        message.reply_text("You Haven't Specified A Time To Mute This User For!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    mutetime = extract_time(message, time_val)

    if not mutetime:
        return ""

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#Temp_Muted\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}\n"
        f"<b>Time:</b> {time_val}"
    )
    if reason:
        log += f"\n\n<b>Reason:</b> {reason}"

    try:
        if member.can_send_messages is None or member.can_send_messages:
            chat_permissions = ChatPermissions(can_send_messages=False)
            bot.restrict_chat_member(
                chat.id, user_id, chat_permissions, until_date=mutetime,
            )     
            msg = (
                f"{mention_html(member.user.id, member.user.first_name)} [<code>{member.user.id}</code>] Is Now Muted"
                f"\n\nMuted For: (<code>{time_val}</code>)\n"
            )

            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "Unmute", callback_data="unmute_({})".format(member.user.id))
            ]])
            bot.sendMessage(chat.id, msg, reply_markup=keyboard, parse_mode=ParseMode.HTML)

            return log
        message.reply_text("This User Is Already Muted.")

    except BadRequest as excp:
        if excp.message == "reply message not found":
            # Do not reply
            message.reply_text(f"Muted for {time_val}!", quote=False)
            return log
        LOGGER.warning(update)
        LOGGER.exception(
            "Error muting user %s in chat %s (%s) due to %s",
            user_id,
            chat.title,
            chat.id,
            excp.message,
        )
        message.reply_text("Well Damn, I Can't Mute That User.")

    return ""

@user_admin_no_reply
@bot_admin
@loggable
def button(update: Update, context: CallbackContext) -> str:
    query: Optional[CallbackQuery] = update.callback_query
    user: Optional[User] = update.effective_user
    bot: Optional[Bot] = context.bot
    match = re.match(r"unmute_\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat: Optional[Chat] = update.effective_chat
        member = chat.get_member(user_id)
        chat_permissions = ChatPermissions (
                can_send_messages=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_send_polls=True,
                can_change_info=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
        )                
        unmuted = bot.restrict_chat_member(chat.id, int(user_id), chat_permissions)
        if unmuted:
        	update.effective_message.edit_text(
        	    f"{mention_html(member.user.id, member.user.first_name)} [<code>{member.user.id}</code>] Now Can Speak Again.",
        	    parse_mode=ParseMode.HTML,
        	)
        	query.answer("Unmuted!")
        	return (
                    f"<b>{html.escape(chat.title)}:</b>\n" 
                    f"#Unmute\n" 
                    f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                    f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
                )
    else:
        update.effective_message.edit_text(
            "This User Not Muted Or Has Left The Group!"
        )
        return ""
            

MUTE_HANDLER = CommandHandler("mute", mute, run_async=True)
UNMUTE_HANDLER = CommandHandler("unmute", unmute, run_async=True)
TEMPMUTE_HANDLER = CommandHandler(["tmute", "tempmute"], temp_mute, run_async=True)
UNMUTE_BUTTON_HANDLER = CallbackQueryHandler(button, pattern=r"unmute_")

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
dispatcher.add_handler(TEMPMUTE_HANDLER)
dispatcher.add_handler(UNMUTE_BUTTON_HANDLER)

__mod_name__ = "Mutes"
__handlers__ = [MUTE_HANDLER, UNMUTE_HANDLER, TEMPMUTE_HANDLER]
