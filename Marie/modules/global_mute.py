import html
from io import BytesIO
from typing import Optional, List

from telegram import ChatPermissions
from telegram import Message, Update, Bot, User, Chat
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

import Marie.modules.sql.global_mutes_sql as sql
from Marie import dispatcher, OWNER_ID, DEV_USERS,DRAGONS,DEMONS, TIGERS,STRICT_GMUTE
from Marie.modules.helper_funcs.chat_status import user_admin, is_user_admin
from Marie.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from Marie.modules.helper_funcs.filters import CustomFilters
from Marie.modules.sql.users_sql import get_all_chats

GMUTE_ENFORCE_GROUP = 6

OFFICERS = [OWNER_ID] + DEV_USERS + DRAGONS + DEMONS + TIGERS


ERROR_DUMP = None

@run_async
def gmute(update, context):
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat
    args = context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You Don't Seem To Be Referring To A User.")
        return

    if int(user_id) in OFFICERS:
        message.reply_text("I Can't Gmute My Sudo Users .")
        return

    if user_id == context.bot.id:
        message.reply_text("I Can't Gmute Myself.")
        return

    if not reason:
        message.reply_text("Please Give A Reason Why Are You Want To Gmute This User!")
        return

    try:
        user_chat = context.bot.get_chat(user_id)
    except BadRequest as excp:
        message.reply_text(excp.message)
        return

    if user_chat.type != 'private':
        message.reply_text("That's Not A User!")
        return

    if sql.is_user_gmuted(user_id):
        if not reason:
            message.reply_text("This User Is Already Gmuted; I'd change The Reason, But You Haven't Given Me One...")
            return

        success = sql.update_gmute_reason(user_id, user_chat.username or user_chat.first_name, reason)
        if success:
            message.reply_text("I've Gone And Updated The Gmute Reason Though!")
        else:
            message.reply_text("I Thought This Person Was Gmuted.")

        return

    message.reply_text("Gets Duct Tape Ready")

    muter = update.effective_user  # type: Optional[User]


    sql.gmute_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gmutes
        if not sql.does_chat_gmute(chat_id):
            continue

        try:
            context.bot.restrict_chat_member(chat_id, user_id, permissions=ChatPermissions(can_send_messages=False))
        except BadRequest as excp:
            if excp.message == "User is an administrator of the chat":
                pass
            elif excp.message == "Chat not found":
                pass
            elif excp.message == "Not enough rights to restrict/unrestrict chat member":
                pass
            elif excp.message == "User_not_participant":
                pass
            elif excp.message == "Peer_id_invalid":  # Suspect this happens when a group is suspended by telegram.
                pass
            elif excp.message == "Group chat was deactivated":
                pass
            elif excp.message == "Need to be inviter of a user to kick it from a basic group":
                pass
            elif excp.message == "Chat_admin_required":
                pass
            elif excp.message == "Only the creator of a basic group can kick group administrators":
                pass
            elif excp.message == "Method is available only for supergroups":
                pass
            elif excp.message == "Can't demote chat creator":
                pass
            else:
                message.reply_text("ᴜɴᴇxᴘᴇᴄᴛᴇᴅ ᴇʀʀᴏʀ!")
                context.bot.send_message(ERROR_DUMP, "Could Not Gmute Due To: {} .".format(excp.message))
                sql.ungmute_user(user_id)
                return
        except TelegramError:
            pass

    message.reply_text("They Won't Be Talking Again Anytime Soon.")


@run_async
def ungmute(update, context):
    message = update.effective_message  # type: Optional[Message]
    bot = context.bot
    args = context.args
    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You Don't Seem To Be Referring To A User.")
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("That's Not A User!")
        return

    if not sql.is_user_gmuted(user_id):
        message.reply_text("This User Is Not Gmuted!")
        return

    muter = update.effective_user  # type: Optional[User]

    message.reply_text("I'll Let {} Speak Again, Globally.".format(user_chat.first_name))


    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gmutes
        if not sql.does_chat_gmute(chat_id):
            continue

        try:
            member = context.bot.get_chat_member(chat_id, user_id)
            if member.status == 'restricted':
                context.bot.restrict_chat_member(chat_id, int(user_id),
                                     permissions=ChatPermissions(
                                     can_send_messages=True,
                                     can_invite_users=True,
                                     can_pin_messages=True,
                                     can_send_polls=True,
                                     can_change_info=True,
                                     can_send_media_messages=True,
                                     can_send_other_messages=True,
                                     can_add_web_page_previews=True,)
                                                )

        except BadRequest as excp:
            if excp.message == "User is an administrator of the chat":
                pass
            elif excp.message == "Chat not found":
                pass
            elif excp.message == "Not enough rights to restrict/unrestrict chat member":
                pass
            elif excp.message == "User_not_participant":
                pass
            elif excp.message == "Method is available for supergroup and channel chats only":
                pass
            elif excp.message == "Not in the chat":
                pass
            elif excp.message == "Channel_private":
                pass
            elif excp.message == "Chat_admin_required":
                pass
            else:
                message.reply_text("Unexpected Error!")
                bot.send_message(ERROR_DUMP, "Could Not Un-Gmute Due To: {} .".format(excp.message))
                return
        except TelegramError:
            pass

    sql.ungmute_user(user_id)

    message.reply_text("Person Has Been Un-Gmuted.")


@run_async
def gmutelist(update, context):
    muted_users = sql.get_gmute_list()

    if not muted_users:
        update.effective_message.reply_text("There Aren't Any Gmuted Users! You're Kinder Than I Expected...")
        return

    mutefile = 'Screw these guys.\n'
    for user in muted_users:
        mutefile += "[x] {} - {}\n".format(user["name"], user["user_id"])
        if user["reason"]:
            mutefile += "Reason: {}\n".format(user["reason"])

    with BytesIO(str.encode(mutefile)) as output:
        output.name = "gmutelist.txt"
        update.effective_message.reply_document(document=output, filename="gmutelist.txt",
                                                caption="Here Is The List Of Currently Gmuted Users.")


def check_and_mute(update, user_id, should_message=True):
    if sql.is_user_gmuted(user_id):
        context.bot.restrict_chat_member(update.effective_chat.id, user_id, can_send_messages=False)
        if should_message:
            update.effective_message.reply_text("This Is A Bad Person, I'll Silence Them For You!")


@run_async
def enforce_gmute(update, context):
    # Not using @restrict handler to avoid spamming - just ignore if cant gmute.
    if sql.does_chat_gmute(update.effective_chat.id) and update.effective_chat.get_member(context.bot.id).can_restrict_members:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        msg = update.effective_message  # type: Optional[Message]

        if user and not is_user_admin(chat, user.id):
            check_and_mute(update, user.id, should_message=True)
        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_mute(update, mem.id, should_message=True)
        if msg.reply_to_message:
            user = msg.reply_to_message.from_user  # type: Optional[User]
            if user and not is_user_admin(chat, user.id):
                check_and_mute(update, user.id, should_message=True)

@run_async
@user_admin
def gmutestat(update, context):
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gmutes(update.effective_chat.id)
            update.effective_message.reply_text("I've Enabled Gmutes In This Group. This Will Help Protect You"
                                                "From Spammers, Unsavory Characters, And Alone.")
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gmutes(update.effective_chat.id)
            update.effective_message.reply_text("I've Disabled Gmutes In ThisThis Group. Gmutes Won't Affect Your Users"
                                                "Anymore. You'll Be Less Protected From Alone Though!")
    else:
        update.effective_message.reply_text("Give Me Some Arguments To Choose A Setting! on/off, yes/no! .\n\n"
                                            "Your Current Setting Is: {}\n"
                                            "When True, Any Gmutes That Happen Will Also Happen In Your Group. "
                                            "When False, They Won't, Leaving You At The Possible Mercy Of "
                                            "Spammers.".format(sql.does_chat_gmute(update.effective_chat.id)))



def __user_info__(user_id):
    is_gmuted = sql.is_user_gmuted(user_id)
    text = "<b>Globally Muted: </b>{}"

    if user_id == dispatcher.bot.id:
        return ""
    if int(user_id) in OFFICERS:
        return ""

    if is_gmuted:
        text = text.format("Yes")
        user = sql.get_gmuted_user(user_id)
        if user.reason:
            text += "\nReason: {} .".format(html.escape(user.reason))
    else:
        text = text.format("No")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)




GMUTE_HANDLER = CommandHandler("gmute", gmute, pass_args=True,
                              filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
UNGMUTE_HANDLER = CommandHandler("ungmute", ungmute, pass_args=True,
                                filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
GMUTE_LIST = CommandHandler("gmutelist", gmutelist,
                           filters=CustomFilters.sudo_filter | CustomFilters.support_filter)

GMUTE_STATUS = CommandHandler("gmutespam", gmutestat, pass_args=True, filters=Filters.group)

GMUTE_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gmute)

dispatcher.add_handler(GMUTE_HANDLER)
dispatcher.add_handler(UNGMUTE_HANDLER)
dispatcher.add_handler(GMUTE_LIST)
dispatcher.add_handler(GMUTE_STATUS)

if STRICT_GMUTE:
    dispatcher.add_handler(GMUTE_ENFORCER, GMUTE_ENFORCE_GROUP)
