from Marie import dispatcher
from Marie.modules.helper_funcs.chat_status import (
    bot_admin, is_bot_admin, is_user_ban_protected, is_user_in_chat)
from Marie.modules.helper_funcs.extraction import extract_user_and_text
from Marie.modules.helper_funcs.filters import CustomFilters
from telegram import Update, ChatPermissions
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, run_async

RBAN_ERRORS = {
    "User is an administrator of the chat", "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant", "Peer_id_invalid", "Group chat was deactivated",
    "Need to be inviter of a user to punch it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can punch group administrators",
    "Channel_private", "Not in the chat"
}

RUNBAN_ERRORS = {
    "User is an administrator of the chat", "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant", "Peer_id_invalid", "Group chat was deactivated",
    "Need to be inviter of a user to punch it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can punch group administrators",
    "Channel_private", "Not in the chat"
}

RKICK_ERRORS = {
    "User is an administrator of the chat", "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant", "Peer_id_invalid", "Group chat was deactivated",
    "Need to be inviter of a user to punch it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can punch group administrators",
    "Channel_private", "Not in the chat"
}

RMUTE_ERRORS = {
    "User is an administrator of the chat", "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant", "Peer_id_invalid", "Group chat was deactivated",
    "Need to be inviter of a user to punch it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can punch group administrators",
    "Channel_private", "Not in the chat"
}

RUNMUTE_ERRORS = {
    "User is an administrator of the chat", "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant", "Peer_id_invalid", "Group chat was deactivated",
    "Need to be inviter of a user to punch it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can punch group administrators",
    "Channel_private", "Not in the chat"
}


@run_async
@bot_admin
def rban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("You Don't Seem To Be Referring To A Chat/User.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "You Don't Seem To Referring To A User Or The ID Specified Is Incorrect.."
        )
        return
    elif not chat_id:
        message.reply_text("You Don't Seem To Be Referring To A Chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text(
                "Chat Not Found! Make Sure You Entered A Valid Chat ID And I'm Part Of That Chat."
            )
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("I'm Sorry, But That's A Private Chat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(
            bot.id).can_restrict_members:
        message.reply_text(
            "I Can't Restrict People There! Make Sure I'm Admin And Can Ban Users."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I Can't Seem To Find This User")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("I Really Wish I Could Ban Admins...")
        return

    if user_id == bot.id:
        message.reply_text("I'm Not Gonna Ban Myself, Aare You Crazy?")
        return

    try:
        chat.kick_member(user_id)
        message.reply_text("Banned From Chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Banned!', quote=False)
        elif excp.message in RBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s",
                             user_id, chat.title, chat.id, excp.message)
            message.reply_text("Well Damn, I Can't Ban That User.")


@run_async
@bot_admin
def runban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("You Don't Seem To Be Referring To A Chat/User.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "You Don't Seem To Be Referring To A User Or The ID Specified In Incorrect.."
        )
        return
    elif not chat_id:
        message.reply_text("You Don't Seem To Be Referring To A Chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text(
                "Chat Not Found! Make Sure You Entered A Valid Chat ID And I'm Part Of That Chat."
            )
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("I'm Sorry, But That's A Private Chat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(
            bot.id).can_restrict_members:
        message.reply_text(
            "I Can't Unrestrict People There! Make Sure I'm Admin And Can Unban Users.",
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I Can't Seem To Find This User... there")
            return
        else:
            raise

    if is_user_in_chat(chat, user_id):
        message.reply_text(
            "Why Are You Trying To Remotely Unban Someone That's Already In That Chat?"
        )
        return

    if user_id == bot.id:
        message.reply_text("I'm Not Gonna Unabn Myself, I'm An Admin There!")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("Yep, This User Can Join That Chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Unbanned!', quote=False)
        elif excp.message in RUNBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR unbanning user %s in chat %s (%s) due to %s", user_id,
                chat.title, chat.id, excp.message)
            message.reply_text("Well Damn, I Can't Unban That User.")


@run_async
@bot_admin
def rkick(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("You Don't Seem To Be Referring To A Chat/User.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "You Don't Seem To Be Referring To A User Or The ID Specified Is Incorrect.."
        )
        return
    elif not chat_id:
        message.reply_text("ʏᴏᴜ ᴅᴏɴ'ᴛ ꜱᴇᴇᴍ ᴛᴏ ʙᴇ ʀᴇꜰᴇʀʀɪɴɢ ᴛᴏ ᴀ ᴄʜᴀᴛ ʙᴀʙʏ🥀 You Don't Seem Yo Be Referring.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text(
                "Chat Not Found! Make Sure You Entered A Valid Chat ID And I'm Part Of That Chat."
            )
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("I'm Sorry, But That's Private Chat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(
            bot.id).can_restrict_members:
        message.reply_text(
            "I Can't Restrict People There! Make Sure I'm Admin And Can Punch Users.",
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I Can't Seem To Find This User")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("I Really Wish I Could Punch Admins...")
        return

    if user_id == bot.id:
        message.reply_text("I'm Not Gonna Punch Myself, Are You Crazy?")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("Punched From Chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('ᴘᴜɴᴄʜᴇᴅ..!!', quote=False)
        elif excp.message in RKICK_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR punching user %s in chat %s (%s) due to %s",
                             user_id, chat.title, chat.id, excp.message)
            message.reply_text("Well Damn, I Can't Punch That User.")


@run_async
@bot_admin
def rmute(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("You Don't Seem To Be Referring To A Chat/User.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "You Don't Seem To Be Referring To A User Or The ID Specified Is Incorrect.."
        )
        return
    elif not chat_id:
        message.reply_text("You Don't Seem To Be Referring To A Chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text(
                "Chat Not Found! Make Sure You Entered A Valid Chat Id And I'm Part Of That Chat."
            )
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("I'm Sorry, But That's A Private Chat.!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(
            bot.id).can_restrict_members:
        message.reply_text(
            "I Can't Restrict People There! Make Sure I'm Admin And Can Mute Users.",
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I Can't Seem To Find This User")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("I Really Wish I Could Mute Admins...")
        return

    if user_id == bot.id:
        message.reply_text("I'm Not Gonna Mute Myself, Are You Crazy?")
        return

    try:
        bot.restrict_chat_member(
            chat.id,
            user_id,
            permissions=ChatPermissions(can_send_messages=False))
        message.reply_text("Muted From The Chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Muted!', quote=False)
        elif excp.message in RMUTE_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR mute user %s in chat %s (%s) due to %s",
                             user_id, chat.title, chat.id, excp.message)
            message.reply_text("Well Damn, I Can't Mute That User.")


@run_async
@bot_admin
def runmute(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("You Don't Seem To Be Referring To A Chat/User.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "You Don't Seem To Be Referring To A User Or The ID Specified Is Incorrect.."
        )
        return
    elif not chat_id:
        message.reply_text("You Don't Seem To Be Referring To A Chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text(
                "Chat Not Found! Make Sure You Entered A Valid Chat Id And I'm Part Of That Chat."
            )
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("I'm Sorry, But That's A Private Chat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(
            bot.id).can_restrict_members:
        message.reply_text(
            "I Can't Unrestrict People There! Make Sure I'm Admin And Can Unban Users.",
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I Can't Seem To Find This User there")
            return
        else:
            raise

    if is_user_in_chat(chat, user_id):
        if member.can_send_messages and member.can_send_media_messages \
           and member.can_send_other_messages and member.can_add_web_page_previews:
            message.reply_text(
                "This User Already Has The Right To Speak In That Chat.")
            return

    if user_id == bot.id:
        message.reply_text("I'm Not Gonna Unmute Myself, I'm An Admin There!")
        return

    try:
        bot.restrict_chat_member(
            chat.id,
            int(user_id),
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True))
        message.reply_text("Yep, This User Can Talk In That Chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Unmuted.. Okay !', quote=False)
        elif excp.message in RUNMUTE_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR unmnuting user %s in chat %s (%s) due to %s", user_id,
                chat.title, chat.id, excp.message)
            message.reply_text("Well Danm, I Can't Unmute That User..!.")


RBAN_HANDLER = CommandHandler("rban", rban, filters=CustomFilters.sudo_filter)
RUNBAN_HANDLER = CommandHandler(
    "runban", runban, filters=CustomFilters.sudo_filter)
RKICK_HANDLER = CommandHandler(
    "rpunch", rkick, filters=CustomFilters.sudo_filter)
RMUTE_HANDLER = CommandHandler(
    "rmute", rmute, filters=CustomFilters.sudo_filter)
RUNMUTE_HANDLER = CommandHandler(
    "runmute", runmute, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(RBAN_HANDLER)
dispatcher.add_handler(RUNBAN_HANDLER)
dispatcher.add_handler(RKICK_HANDLER)
dispatcher.add_handler(RMUTE_HANDLER)
dispatcher.add_handler(RUNMUTE_HANDLER)
