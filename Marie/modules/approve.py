import html
from Marie.modules.disable import DisableAbleCommandHandler
from Marie import dispatcher, DRAGONS
from Marie.modules.helper_funcs.extraction import extract_user
from telegram.ext import CallbackContext, CallbackQueryHandler
import Marie.modules.sql.approve_sql as sql
from Marie.modules.helper_funcs.chat_status import user_admin
from Marie.modules.log_channel import loggable
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.utils.helpers import mention_html
from telegram.error import BadRequest


@loggable
@user_admin
def approve(update, context):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "I don't Know Who You're Talking About, You're Going To Need To Specify A User!",
        )
        return ""
    try:
        member = chat.get_member(user_id)
    except BadRequest:
        return ""
    if member.status in ("administrator", "creator"):
        message.reply_text(
            "User Is Already Admin - Locks, Blocklists, And Antiflood Already Don't Apply To Them.",
        )
        return ""
    if sql.is_approved(message.chat_id, user_id):
        message.reply_text(
            f"[{member.user['first_name']}](tg://user?id={member.user['id']}) Is Already Approved I {chat_title} .",
            parse_mode=ParseMode.MARKDOWN,
        )
        return ""
    sql.approve(message.chat_id, user_id)
    message.reply_text(
        f"[{member.user['first_name']}](tg://user?id={member.user['id']}) Has Been Approved In {chat_title} .! They Will Now Be Ignored By Automated Admin Actions Like Licks, Blocklists, And Anti Flood.",
        parse_mode=ParseMode.MARKDOWN,
    )
    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#Approved\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    return log_message


@loggable
@user_admin
def disapprove(update, context):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "I don't Know Who's You Talking About, You're Going To Need To Specify A User!",
        )
        return ""
    try:
        member = chat.get_member(user_id)
    except BadRequest:
        return ""
    if member.status in ("administrator", "creator"):
        message.reply_text("This User Is An Admin, They Can't Be Unapproved.")
        return ""
    if not sql.is_approved(message.chat_id, user_id):
        message.reply_text(f"{member.user['first_name']} isn't Approved Yet!")
        return ""
    sql.disapprove(message.chat_id, user_id)
    message.reply_text(
        f"{member.user['first_name']} Is No Longer Approved In {chat_title} ...",
    )
    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#Unapproved\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    return log_message


@user_admin
def approved(update, context):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    msg = "The Following Users Are Approved.\n"
    approved_users = sql.list_approved(message.chat_id)
    for i in approved_users:
        member = chat.get_member(int(i.user_id))
        msg += f"- `{i.user_id}`: {member.user['first_name']}\n"
    if msg.endswith("approved.\n"):
        message.reply_text(f"No Users Are Approved In {chat_title} ...")
        return ""
    message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


@user_admin
def approval(update, context):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user_id = extract_user(message, args)
    member = chat.get_member(int(user_id))
    if not user_id:
        message.reply_text(
            "I don't Know Who You're Talking About, You're Going To Need To Specify A User!",
        )
        return ""
    if sql.is_approved(message.chat_id, user_id):
        message.reply_text(
            f"{member.user['first_name']} Is An Approved Usern Locks, Antiflood, And Blocklists Won't Apply To Them.",
        )
    else:
        message.reply_text(
            f"{member.user['first_name']} Is Not An Approved User. They Are Affected By Normal Commands.",
        )


def unapproveall(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in DRAGONS:
        update.effective_message.reply_text(
            "Only The Chat Owner Can Unapproved All User At Once.",
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Unapprove all users",
                        callback_data="unapproveall_user",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="Cancel",
                        callback_data="unapproveall_cancel",
                    ),
                ],
            ],
        )
        update.effective_message.reply_text(
            f"Are You Sure You Would Like To Unapproved All User In{chat.title}? This Action Can't Be Undone.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )


def unapproveall_btn(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = update.effective_chat
    message = update.effective_message
    member = chat.get_member(query.from_user.id)
    if query.data == "unapproveall_user":
        if member.status == "creator" or query.from_user.id in DRAGONS:
            approved_users = sql.list_approved(chat.id)
            users = [int(i.user_id) for i in approved_users]
            for user_id in users:
                sql.disapprove(chat.id, user_id)
            message.edit_text("Successfully Unapproved All User In This Chat.")
            return

        if member.status == "administrator":
            query.answer("Only Owner Of The Chat Can Do This.")

        if member.status == "member":
            query.answer("You Need To Be Admin To Do This.")
    elif query.data == "unapproveall_cancel":
        if member.status == "creator" or query.from_user.id in DRAGONS:
            message.edit_text("Removing Of All Approved Users Has Been Cancelled.")
            return ""
        if member.status == "administrator":
            query.answer("Only Owner Of The Chat Can Do This.")
        if member.status == "member":
            query.answer("You Need To Be Admin To Do This.")


__help__ = """
Sometimes, You Might Trust A User Not To Send Unwanted Content. Maybe Not Enough To Make Them Admin, But You Might Be Ok With Locks, Blacklists, And Antiflood Not Applying To Them.

That's What Approvals Are For - Approve Of Trust Worthy Users To Allow Them To Send
*Admin commands:*
» `/approval`*:* Check A User's Approval Status In This Chat.
» `/approve`*:* Approve Of A User. Lovks Blacklists, And Antiflood Won't Apply To Then Anymore.
» `/unapprove`*:* Unapprove Of A User. They Will Now Be Subject To Locks, Blacklists, And Antiflood Again.
» `/approved`*:* List All Approved Users.
» `/unapproveall`*:* Unapprove *All* Users In A Chat. This Cannot Be Undone.
"""

APPROVE = DisableAbleCommandHandler("approve", approve, run_async=True)
DISAPPROVE = DisableAbleCommandHandler("unapprove", disapprove, run_async=True)
APPROVED = DisableAbleCommandHandler("approved", approved, run_async=True)
APPROVAL = DisableAbleCommandHandler("approval", approval, run_async=True)
UNAPPROVEALL = DisableAbleCommandHandler("unapproveall", unapproveall, run_async=True)
UNAPPROVEALL_BTN = CallbackQueryHandler(
    unapproveall_btn, pattern=r"unapproveall_.*", run_async=True
)

dispatcher.add_handler(APPROVE)
dispatcher.add_handler(DISAPPROVE)
dispatcher.add_handler(APPROVED)
dispatcher.add_handler(APPROVAL)
dispatcher.add_handler(UNAPPROVEALL)
dispatcher.add_handler(UNAPPROVEALL_BTN)

__mod_name__ = "Approvals"
__command_list__ = ["approve", "unapprove", "approved", "approval"]
__handlers__ = [APPROVE, DISAPPROVE, APPROVED, APPROVAL]
