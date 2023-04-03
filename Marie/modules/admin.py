
import html
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, run_async
from telegram.utils.helpers import mention_html

from Marie import DRAGONS, dispatcher
from Marie.modules.disable import DisableAbleCommandHandler
from Marie.modules.helper_funcs.admin_rights import user_can_changeinfo
from Marie.modules.helper_funcs.alternate import send_message
from Marie.modules.helper_funcs.chat_status import (
    ADMIN_CACHE,
    bot_admin,
    can_pin,
    can_promote,
    connection_status,
    user_admin,
)
from Marie.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from Marie.modules.log_channel import loggable


@run_async
@bot_admin
@user_admin
def set_sticker(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        return msg.reply_text(
            "» You Don't Have Permissions To Change Group Info!"
        )

    if msg.reply_to_message:
        if not msg.reply_to_message.sticker:
            return msg.reply_text(
                "» Reply To A Sticker To Set It As Group Sticker Pack!"
            )
        stkr = msg.reply_to_message.sticker.set_name
        try:
            context.bot.set_chat_sticker_set(chat.id, stkr)
            msg.reply_text(f"» Successfully Set Group Stickers In{chat.title} !")
        except BadRequest as excp:
            if excp.message == "Participants_too_few":
                return msg.reply_text(
                    "» Your Group Needs Minimum 100 Members For Setting A Sticker Pack As Group Sticker Pack!"
                )
            msg.reply_text(f"Error ! {excp.message}..Okay!.")
    else:
        msg.reply_text("» Reply To A Sticker To Set It As Group Sticker Pack!")


@run_async
@bot_admin
@user_admin
def setchatpic(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("» You Don't Have Permissions To Change Group Info!")
        return

    if msg.reply_to_message:
        if msg.reply_to_message.photo:
            pic_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            pic_id = msg.reply_to_message.document.file_id
        else:
            msg.reply_text("» You Can Only Set Photos As Group Pfp!")
            return
        dlmsg = msg.reply_text("» Changing Group's Profile Pic...")
        tpic = context.bot.get_file(pic_id)
        tpic.download("gpic.png")
        try:
            with open("gpic.png", "rb") as chatp:
                context.bot.set_chat_photo(int(chat.id), photo=chatp)
                msg.reply_text("» Successfully Set Group Profile Pic")
        except BadRequest as excp:
            msg.reply_text(f"Getting...Error ! {excp.message}")
        finally:
            dlmsg.delete()
            if os.path.isfile("gpic.png"):
                os.remove("gpic.png")
    else:
        msg.reply_text("» Reply To A Photo Or File To Set It As Group Profile Pic!")


@run_async
@bot_admin
@user_admin
def rmchatpic(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("» You Don't Have Permissions To Change Group Info!")
        return
    try:
        context.bot.delete_chat_photo(int(chat.id))
        msg.reply_text("» Successfully Deleted Group's Default Profile Pic!")
    except BadRequest as excp:
        msg.reply_text(f"Error ! {excp.message} ..Okay.")
        return


@run_async
@bot_admin
@user_admin
def set_desc(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        return msg.reply_text(
            "» You Don't Have Permissions To Change Group Info!"
        )

    tesc = msg.text.split(None, 1)
    if len(tesc) >= 2:
        desc = tesc[1]
    else:
        return msg.reply_text("» wtf, You Want To Set An Empty Description!")
    try:
        if len(desc) > 255:
            return msg.reply_text(
                "» Description Must Be Less Than 255 Words Or Characters!"
            )
        context.bot.set_chat_description(chat.id, desc)
        msg.reply_text(f"» Successfully Updated Chat Description In {chat.title} ..!")
    except BadRequest as excp:
        msg.reply_text(f"Error ! {excp.message}...")


@run_async
@bot_admin
@user_admin
def setchat_title(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    args = context.args

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("» You Don't Have Permissions To Change Group Info!")
        return

    title = " ".join(args)
    if not title:
        msg.reply_text("» Enter Some Text To Set As New Chat Tittle!")
        return

    try:
        context.bot.set_chat_title(int(chat.id), str(title))
        msg.reply_text(
            f"» Successfully Set <b>{title}</b> As New Chat Tittle!",
            parse_mode=ParseMode.HTML,
        )
    except BadRequest as excp:
        msg.reply_text(f"Error ! {excp.message} ....")
        return


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def promote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = chat.get_member(user.id)

    if (
        not (promoter.can_promote_members or promoter.status == "creator")
        and user.id not in DRAGONS
    ):
        message.reply_text("» You Don't Have Permissions To Add New Admins!")
        return

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "» I Don't Know Who's That User, Never Seen Him In Any Of The Chats Where I Am Present!",
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status in ("administrator", "creator"):
        message.reply_text("» Àccording To Me That User Is Already An Admin!")
        return

    if user_id == bot.id:
        message.reply_text(
            "» I Can't Promote Myself, My Owner Didn't Told Me To Do So."
        )
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            can_manage_voice_chats=bot_member.can_manage_voice_chats,
            can_pin_messages=bot_member.can_pin_messages,
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text("» As I Can Seem That User Is Not Present There.")
        else:
            message.reply_text(
                "» Something Went Wrong, Maybe Someone Promoted That User Before Me."
            )
        return

    bot.sendMessage(
        chat.id,
        f"<b>» Promoting A User In</b> {chat.title}\n\nPromoted : {mention_html(user_member.user.id, user_member.user.first_name)}\nPromoter : {mention_html(user.id, user.first_name)}",
        parse_mode=ParseMode.HTML,
    )

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#Promoted\n"
        f"<b>Promoter :</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User :</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def lowpromote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = chat.get_member(user.id)

    if (
        not (promoter.can_promote_members or promoter.status == "creator")
        and user.id not in DRAGONS
    ):
        message.reply_text("» You Don't Have Permissions To Add New Admins")
        return

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "» I Don't Know Who's That User, Never Seen Him In Any Of The Chats Where I Am Present !",
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status in ("administrator", "creator"):
        message.reply_text("» Àccording To Me That User Is Already An Admin!")
        return

    if user_id == bot.id:
        message.reply_text(
            "» I Can't Promote Myself, My Owner Didn't Told Me To Do So."
        )
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            can_pin_messages=bot_member.can_pin_messages,
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text("» As I Can Seem That User Is Not Present There.")
        else:
            message.reply_text(
                "» Something Went Wrong, Maybe Someone Promoted That User Before."
            )
        return

    bot.sendMessage(
        chat.id,
        f"<b>» Low Promoting A User In </b>{chat.title}\n\n<b>Promoted :</b> {mention_html(user_member.user.id, user_member.user.first_name)}\nPromoter : {mention_html(user.id, user.first_name)}",
        parse_mode=ParseMode.HTML,
    )

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#LowPromoted\n"
        f"<b>Promoter :</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User :</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def fullpromote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = chat.get_member(user.id)

    if (
        not (promoter.can_promote_members or promoter.status == "creator")
        and user.id not in DRAGONS
    ):
        message.reply_text("» You Don't Have Permissions To Add New Admins")
        return

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "» I Don't Know Who's That User, Never Seen Him In Any Of The Chats Where I Am Present!",
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status in ("administrator", "creator"):
        message.reply_text("» Àccording To Me That User Is Already An Admin!")
        return

    if user_id == bot.id:
        message.reply_text(
            "» I Can't Promote Myself, My Owner Didn't Told Me To Do So."
        )
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            can_promote_members=bot_member.can_promote_members,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
            can_manage_voice_chats=bot_member.can_manage_voice_chats,
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text("» As I Can Seem That User Is Not Present There.")
        else:
            message.reply_text(
                "» Something Went Wrong, Maybe Someone Promoted That User Before Me."
            )
        return

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    " Demote ",
                    callback_data="demote_({})".format(user_member.user.id),
                )
            ]
        ]
    )

    bot.sendMessage(
        chat.id,
        f"» FullPromoting A User In <b>{chat.title}</b>\n\n<b>User : {mention_html(user_member.user.id, user_member.user.first_name)}</b>\n<b>Promoter: {mention_html(user.id, user.first_name)}</b>",
        parse_mode=ParseMode.HTML,
    )

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#FullPromoted\n"
        f"<b>Promoter :</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User :</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def demote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "» I Don't Know Who's That User, Never Seen Him In Any Of The Chats Where I Am Present!",
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status == "creator":
        message.reply_text(
            "» That User Is Owner Of The Chat And I Don't Want To Put Myself In Danger."
        )
        return

    if not user_member.status == "administrator":
        message.reply_text("» According To Me That User Is Not An Admin Here")
        return

    if user_id == bot.id:
        message.reply_text("» I Can't Demote Myself, But If You Want I Can Leave.")
        return

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_manage_voice_chats=False,
        )

        bot.sendMessage(
            chat.id,
            f"» Successfully Demoted A Admin In <b>{chat.title}</b>\n\nDemoted : <b>{mention_html(user_member.user.id, user_member.user.first_name)}</b>\nDemoter : {mention_html(user.id, user.first_name)}",
            parse_mode=ParseMode.HTML,
        )

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#Demoted\n"
            f"<b>Demoter :</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Demoted :</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message
    except BadRequest:
        message.reply_text(
            "» Failed To Demote Maybe I'm Not An Admin Or Maybe Someone Else Promoted That"
            " User !",
        )
        return


@run_async
@user_admin
def refresh_admin(update, _):
    try:
        ADMIN_CACHE.pop(update.effective_chat.id)
    except KeyError:
        pass

    update.effective_message.reply_text("» Successfully Refreshed Admin Cache!")


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
def set_title(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message

    user_id, title = extract_user_and_text(message, args)
    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if not user_id:
        message.reply_text(
            "» I Don't Know Who's That User, Never Seen Him In Any Of The Chats Where I Am Present!",
        )
        return

    if user_member.status == "creator":
        message.reply_text(
            "» That User Is Owner Of The Chat And I Don't Want To Put Myself In Danger.",
        )
        return

    if user_member.status != "administrator":
        message.reply_text(
            "» I Can Only Set Title For Admins!",
        )
        return

    if user_id == bot.id:
        message.reply_text(
            "» I Can't Set Title For Myself, My Owner Didn't Told Me To Do So.",
        )
        return

    if not title:
        message.reply_text(
            "» You Think That Setting Blank Title Will Change Sometimes "
        )
        return

    if len(title) > 16:
        message.reply_text(
            "» The Tittle Length Is Longer Than 16 Words Or Characters So Truncating It To 16 Word.",
        )

    try:
        bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
    except BadRequest:
        message.reply_text(
            "» Maybe That User Is Not Promoted By Me Or Maybe You sent Something That Can't Be Set As Tittle."
        )
        return

    bot.sendMessage(
        chat.id,
        f"» Successfully Set Tittle For <code>{user_member.user.first_name or user_id}</code> "
        f"ᴛᴏ <code>{html.escape(title[:16])}</code>!",
        parse_mode=ParseMode.HTML,
    )


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def pin(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message
    msg_id = msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id

    if msg.chat.username:
        # If chat has a username, use this format
        link_chat_id = msg.chat.username
        message_link = f"https://t.me/{link_chat_id}/{msg_id}"
    elif (str(msg.chat.id)).startswith("-100"):
        # If chat does not have a username, use this
        link_chat_id = (str(msg.chat.id)).replace("-100", "")
        message_link = f"https://t.me/c/{link_chat_id}/{msg_id}"

    is_group = chat.type not in ("private", "channel")
    prev_message = update.effective_message.reply_to_message

    if prev_message is None:
        msg.reply_text("» Reply To A Message To Pin It!")
        return

    is_silent = True
    if len(args) >= 1:
        is_silent = (
            args[0].lower() != "notify"
            or args[0].lower() == "loud"
            or args[0].lower() == "violent"
        )

    if prev_message and is_group:
        try:
            bot.pinChatMessage(
                chat.id, prev_message.message_id, disable_notification=is_silent
            )
            msg.reply_text(
                f"» Successfully Pinned That Message.\nClick On The Button Below To See The Message.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Message", url=f"{message_link}")]]
                ),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as excp:
            if excp.message != "Chat_not_modified":
                raise

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"Pinned-A-Message\n"
            f"<b>Pinned By :</b> {mention_html(user.id, html.escape(user.first_name))}"
        )

        return log_message


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def unpin(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    msg_id = msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id
    unpinner = chat.get_member(user.id)

    if (
        not (unpinner.can_pin_messages or unpinner.status == "creator")
        and user.id not in DRAGONS
    ):
        message.reply_text(
            "» You Don't Have Permissions To Pin/Unpin Messages In This Chat!"
        )
        return

    if msg.chat.username:
        # If chat has a username, use this format
        link_chat_id = msg.chat.username
        message_link = f"https://t.me/{link_chat_id}/{msg_id}"
    elif (str(msg.chat.id)).startswith("-100"):
        # If chat does not have a username, use this
        link_chat_id = (str(msg.chat.id)).replace("-100", "")
        message_link = f"https://t.me/c/{link_chat_id}/{msg_id}"

    is_group = chat.type not in ("private", "channel")
    prev_message = update.effective_message.reply_to_message

    if prev_message and is_group:
        try:
            context.bot.unpinChatMessage(chat.id, prev_message.message_id)
            msg.reply_text(
                f"» Successfully Unpinned <a href='{message_link}'> This Pinned Message</a>.",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as excp:
            if excp.message != "Chat_not_modified":
                raise

    if not prev_message and is_group:
        try:
            context.bot.unpinChatMessage(chat.id)
            msg.reply_text("» Successfully Unpinned The Last Pinned Message.")
        except BadRequest as excp:
            if excp.message == "Message to unpin not found":
                msg.reply_text(
                    "» I Can't Unpin That Message, Maybe That Message Is Too Old Or Maybe Someone Already Unpinned It."
                )
            else:
                raise

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"Unpinned-A-Message\n"
        f"<b>Unpinned By :</b> {mention_html(user.id, html.escape(user.first_name))}"
    )

    return log_message


@run_async
@bot_admin
def pinned(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    msg = update.effective_message
    msg_id = (
        update.effective_message.reply_to_message.message_id
        if update.effective_message.reply_to_message
        else update.effective_message.message_id
    )

    chat = bot.getChat(chat_id=msg.chat.id)
    if chat.pinned_message:
        pinned_id = chat.pinned_message.message_id
        if msg.chat.username:
            link_chat_id = msg.chat.username
            message_link = f"https://t.me/{link_chat_id}/{pinned_id}"
        elif (str(msg.chat.id)).startswith("-100"):
            link_chat_id = (str(msg.chat.id)).replace("-100", "")
            message_link = f"https://t.me/c/{link_chat_id}/{pinned_id}"

        msg.reply_text(
            f"Pinned On {html.escape(chat.title)} ...",
            reply_to_message_id=msg_id,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Message",
                            url=f"https://t.me/{link_chat_id}/{pinned_id}",
                        )
                    ]
                ]
            ),
        )

    else:
        msg.reply_text(
            f"» There's No Pinned Message In <b>{html.escape(chat.title)} ..!</b>",
            parse_mode=ParseMode.HTML,
        )


@run_async
@bot_admin
@user_admin
@connection_status
def invite(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat

    if chat.username:
        update.effective_message.reply_text(f"https://t.me/{chat.username}")
    elif chat.type in [chat.SUPERGROUP, chat.CHANNEL]:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text(
                "» I don't Have Permissions To Access Invite Links!",
            )
    else:
        update.effective_message.reply_text(
            "» I can Only Give Invite Links For Groups And Channel!",
        )


@run_async
@connection_status
def adminlist(update, context):
    chat = update.effective_chat ## type: Optional[Chat] -> unused variable
    user = update.effective_user  ## type: Optional[User]
    args = context.args  # -> unused variable
    bot = context.bot

    if update.effective_message.chat.type == "private":
        send_message(
            update.effective_message,
            "» This Command Can Only Be Used In Group's Not In PM.",
        )
        return

    update.effective_chat
    chat_id = update.effective_chat.id
    chat_name = update.effective_message.chat.title  # -> unused variable

    try:
        msg = update.effective_message.reply_text(
            "» Fetching Adminlist...",
            parse_mode=ParseMode.HTML,
        )
    except BadRequest:
        msg = update.effective_message.reply_text(
            "» Fetching Adminlist...",
            quote=False,
            parse_mode=ParseMode.HTML,
        )

    administrators = bot.getChatAdministrators(chat_id)
    text = "Admins In <b>{}</b>:".format(html.escape(update.effective_chat.title))

    for admin in administrators:
        user = admin.user
        status = admin.status
        custom_title = admin.custom_title

        if user.first_name == "":
            name = "☠ Deleted Accounts"
        else:
            name = "{}".format(
                mention_html(
                    user.id,
                    html.escape(user.first_name + " " + (user.last_name or "")),
                ),
            )

        if user.is_bot:
            administrators.remove(admin)
            continue

         # if user.username:
        # name = escape_markdown("@" + user.username)
        if status == "creator":
            text += "\n Owner :"
            text += "\n<code> • </code>{}\n".format(name)

            if custom_title:
                text += f"<code> ┗━ {html.escape(custom_title)}</code>\n"

    text += "\n Admins :"

    custom_admin_list = {}
    normal_admin_list = []

    for admin in administrators:
        user = admin.user
        status = admin.status
        custom_title = admin.custom_title

        if user.first_name == "":
            name = "☠ Deleted Accounts"
        else:
            name = "{}".format(
                mention_html(
                    user.id,
                    html.escape(user.first_name + " " + (user.last_name or "")),
                ),
            )
        # if user.username:
        #    name = escape_markdown("@" + user.username)
        if status == "administrator":
            if custom_title:
                try:
                    custom_admin_list[custom_title].append(name)
                except KeyError:
                    custom_admin_list.update({custom_title: [name]})
            else:
                normal_admin_list.append(name)

    for admin in normal_admin_list:
        text += "\n<code> • </code>{}".format(admin)

    for admin_group in custom_admin_list.copy():
        if len(custom_admin_list[admin_group]) == 1:
            text += "\n<code> • </code>{} | <code>{}</code>".format(
                custom_admin_list[admin_group][0],
                html.escape(admin_group),
            )
            custom_admin_list.pop(admin_group)

    text += "\n"
    for admin_group, value in custom_admin_list.items():
        text += "\n🔮 <code>{}</code>".format(admin_group)
        for admin in value:
            text += "\n<code> • </code>{}".format(admin)
        text += "\n"

    try:
        msg.edit_text(text, parse_mode=ParseMode.HTML)
    except BadRequest:  # if original message is deleted
        return


@run_async
@bot_admin
@can_promote
@user_admin
@loggable
def button(update: Update, context: CallbackContext) -> str:
    query: Optional[CallbackQuery] = update.callback_query
    user: Optional[User] = update.effective_user
    bot: Optional[Bot] = context.bot
    match = re.match(r"demote_\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat: Optional[Chat] = update.effective_chat
        member = chat.get_member(user_id)
        bot_member = chat.get_member(bot.id)
        bot_permissions = promoteChatMember(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            can_promote_members=bot_member.can_promote_members,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
            can_manage_voice_chats=bot_member.can_manage_voice_chats,
        )
        demoted = bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_manage_voice_chats=False,
        )
        if demoted:
            update.effective_message.edit_text(
                f"Demoter : {mention_html(user.id, user.first_name)}\nUser : {mention_html(member.user.id, member.user.first_name)}!",
                parse_mode=ParseMode.HTML,
            )
            query.answer("Demoted Successfully !")
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#Demote\n"
                f"<b>Demoter :</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>User :</b> {mention_html(member.user.id, member.user.first_name)}"
            )
    else:
        update.effective_message.edit_text(
            "» Failed To Demote, Maybe That User Is Not An Admin Or Maybe Left The Group!"
        )
        return ""


__help__ = """
*User Commands*:
» `/admins`*:* List Of Admins In The Chat
» `/pinned`*:* To Get The Current Pinned Message.
*The Following Commands Are Admins Only:* 
» `/pin`*:* Silently Pins The Message Replied To - Add `'Loud'` Or `'Notify'` To Give Notifs To User 
» `/unpin`*:* Unpins The Currently Pinned Message 
» `/invitelink`*:* Gets Invitation Link
» `/promote`*:* Promotes The User Replied To
» `/fullpromote`*:* Promotes The User Replied To With Full Rights
» `/demote`*:* Demotes The User Replied To
» `/title` <Tittle Here>*:* Sets A Custom Tittle For An Admin That The Bot Promoted
» `/admincache`*:* Force Refresh The Admins List
» `/del`*:* Deletes The Message You Replied To
» `/purge`*:* Deletes All Messages Between This And The Replied To Message.
» `/purge` <Integer X>*:* Deletes The Replied Message, And X Messages Following It If Replied To A Message.
» `/setgtitle` <Text>*:* Set Group Tittle 
» `/setgpic`*:* Reply To An Image To Set As Group Photo
» `/setdesc`*:* Set Group Description 
» `/setsticker`*:* Set Group Sticker 
*Rules*:
» `/rules`*:* Get The Rules For This Chat.
» `/setrules` <Your Rules Here>*:* Set The Rules For This Chat.
» `/clearrules`*:* Clear The Rules For This Chat.
"""

SET_DESC_HANDLER = CommandHandler("setdesc", set_desc)
SET_STICKER_HANDLER = CommandHandler("setsticker", set_sticker)
SETCHATPIC_HANDLER = CommandHandler("setgpic", setchatpic)
RMCHATPIC_HANDLER = CommandHandler("delgpic", rmchatpic)
SETCHAT_TITLE_HANDLER = CommandHandler("setgtitle", setchat_title)

ADMINLIST_HANDLER = DisableAbleCommandHandler(["admins", "staff"], adminlist)

PIN_HANDLER = CommandHandler("pin", pin)
UNPIN_HANDLER = CommandHandler("unpin", unpin)
PINNED_HANDLER = CommandHandler("pinned", pinned)

INVITE_HANDLER = DisableAbleCommandHandler("invitelink", invite)

PROMOTE_HANDLER = DisableAbleCommandHandler("promote", promote)
FULLPROMOTE_HANDLER = DisableAbleCommandHandler("fullpromote", fullpromote)
LOW_PROMOTE_HANDLER = DisableAbleCommandHandler("lowpromote", lowpromote)
DEMOTE_HANDLER = DisableAbleCommandHandler("demote", demote)

SET_TITLE_HANDLER = CommandHandler("title", set_title)
ADMIN_REFRESH_HANDLER = CommandHandler(
    ["admincache", "reload", "refresh"],
    refresh_admin,
)

dispatcher.add_handler(SET_DESC_HANDLER)
dispatcher.add_handler(SET_STICKER_HANDLER)
dispatcher.add_handler(SETCHATPIC_HANDLER)
dispatcher.add_handler(RMCHATPIC_HANDLER)
dispatcher.add_handler(SETCHAT_TITLE_HANDLER)
dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(PINNED_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(FULLPROMOTE_HANDLER)
dispatcher.add_handler(LOW_PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(SET_TITLE_HANDLER)
dispatcher.add_handler(ADMIN_REFRESH_HANDLER)

__mod_name__ = "Admins"
__command_list__ = [
    "setdesc" "setsticker" "setgpic" "delgpic" "setgtitle" "adminlist",
    "admins",
    "invitelink",
    "promote",
    "fullpromote",
    "lowpromote",
    "demote",
    "admincache",
]
__handlers__ = [
    SET_DESC_HANDLER,
    SET_STICKER_HANDLER,
    SETCHATPIC_HANDLER,
    RMCHATPIC_HANDLER,
    SETCHAT_TITLE_HANDLER,
    ADMINLIST_HANDLER,
    PIN_HANDLER,
    UNPIN_HANDLER,
    PINNED_HANDLER,
    INVITE_HANDLER,
    PROMOTE_HANDLER,
    FULLPROMOTE_HANDLER,
    LOW_PROMOTE_HANDLER,
    DEMOTE_HANDLER,
    SET_TITLE_HANDLER,
    ADMIN_REFRESH_HANDLER,
]
