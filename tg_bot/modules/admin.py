from telegram import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs import is_user_admin, user_admin, bot_admin, can_pin, can_promote
from tg_bot.modules.users import get_user_id


@can_promote
@user_admin
@run_async
def promote(bot, update, args):
    chat_id = update.effective_chat.id
    message = update.effective_message
    prev_message = message.reply_to_message

    if len(args) >= 1 and args[0][0] == '@':
        user = args[0]
        user_id = get_user_id(user)
        if not user_id:
            message.reply_text("I don't have that user in my db. You'll be able to interact with them if "
                               "you reply to that person's message instead.")
            return
    elif prev_message:
        user_id = prev_message.from_user.id
        # set same perms as bot - bot can't assign higher perms than itself!

    else:
        return
    bot_member = update.effective_chat.get_member(bot.id)
    res = bot.promoteChatMember(chat_id, user_id,
                                can_change_info=bot_member.can_change_info,
                                can_post_messages=bot_member.can_post_messages,
                                can_edit_messages=bot_member.can_edit_messages,
                                can_delete_messages=bot_member.can_delete_messages,
                                can_invite_users=bot_member.can_invite_users,
                                can_restrict_members=bot_member.can_restrict_members,
                                can_pin_messages=bot_member.can_pin_messages,
                                can_promote_members=bot_member.can_promote_members)
    if res:
        update.effective_message.reply_text("Successfully promoted!")


@can_promote
@user_admin
@run_async
def demote(bot, update, args):
    chat = update.effective_chat
    message = update.effective_message
    prev_message = message.reply_to_message

    if len(args) >= 1 and args[0][0] == '@':
        user = args[0]
        user_id = get_user_id(user)
        if not user_id:
            message.reply_text("I don't have that user in my db. You'll be able to interact with them if "
                               "you reply to that person's message instead.")
            return
    elif prev_message:
        user_id = prev_message.from_user.id
    else:
        return

    if chat.get_member(user_id).status == 'creator':
        message.reply_text("This person CREATED the chat, how would I demote him?")
        return

    if not chat.get_member(user_id).status == 'administrator':
        message.reply_text("Can't demote what wasn't promoted!")
        return

    try:
        res = bot.promoteChatMember(int(chat.id), int(user_id),
                                    can_change_info=False,
                                    can_post_messages=False,
                                    can_edit_messages=False,
                                    can_delete_messages=False,
                                    can_invite_users=False,
                                    can_restrict_members=False,
                                    can_pin_messages=False,
                                    can_promote_members=False)
        if res:
            message.reply_text("Successfully demoted!")
        else:
            message.reply_text("Could not demote.")
    except BadRequest:
        message.reply_text("Could not demote. Maybe the admin status was appointed by another "
                           "user, so I can't act upon him!")


@can_pin
@user_admin
@run_async
def pin(bot, update, args):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    is_group = chat_type != "private" and chat_type != "channel"

    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = not (args[0].lower() == 'notify' or args[0].lower() == 'loud')

    if prev_message and is_group:
        bot.pinChatMessage(chat_id, prev_message.message_id, disable_notification=is_silent)


@can_pin
@user_admin
@run_async
def unpin(bot, update):
    chat_id = update.effective_chat.id
    bot.unpinChatMessage(chat_id)


@bot_admin
@user_admin
@run_async
def kick(bot, update, args):
    chat = update.effective_chat
    message = update.effective_message
    prev_message = message.reply_to_message

    if len(args) >= 1 and args[0][0] == '@':
        user = args[0]
        user_id = get_user_id(user)
        if not user_id:
            message.reply_text("I don't have that user in my db. You'll be able to interact with them if "
                               "you reply to that person's message instead.")
            return
    elif prev_message:
        user_id = prev_message.from_user.id
    else:
        return
    if is_user_admin(chat, user_id):
        message.reply_text("I really wish I could kick admins...")
        return
    res = update.effective_chat.kick_member(user_id)
    if res:
        bot.send_sticker(update.effective_chat.id, 'CAADAgADOwADPPEcAXkko5EB3YGYAg')
        message.reply_text("Kicked!")
    else:
        message.reply_text("Well damn, I can't kick that user.")


@bot_admin
@run_async
def kickme(bot, update):
    user_id = update.effective_message.from_user.id
    user_is_admin = update.effective_chat.get_member(user_id).status == 'administrator'
    if user_is_admin:
        update.effective_message.reply_text("I wish I could... but you're an admin.")
        return
    res = update.effective_chat.kick_member(user_id)
    if res:
        update.effective_message.reply_text("No problem.")
    else:
        update.effective_message.reply_text("Huh? I can't :/")


@bot_admin
@user_admin
@run_async
def unkick(bot, update, args):
    message = update.effective_message

    if len(args) >= 1 and args[0][0] == '@':
        user = args[0]
        user_id = get_user_id(user)
        if not user_id:
            message.reply_text("I don't have that user in my db. You'll be able to interact with them if "
                               "you reply to that person's message instead.")
            return
    else:
        return
    update.effective_chat.unban_member(user_id)


@bot_admin
@user_admin
@run_async
def invite(bot, update):
    chat = update.effective_chat
    if chat.username:
        update.effective_message.reply_text(chat.username)
    else:
        invitelink = bot.exportChatInviteLink(chat.id)
        update.effective_message.reply_text(invitelink)


@run_async
def adminlist(bot, update):
    administrators = update.effective_chat.get_administrators()
    text = "Admins in *{}*:".format(update.effective_chat.title or "this chat")
    for admin in administrators:
        user = admin.user
        name = user.first_name + (user.last_name or "")
        if user.username:
            name = "@" + user.username
        text += "\n - {}".format(escape_markdown(name))

    update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


__help__ = """
 - /pin: silently pins the message replied to - add 'loud' or 'notify' to give notifs to users.
 - /unpin: unpins the currently pinned message
 - /ban: bans a user
 - /unban <user_id>: unbans a user given his user id
 - /kickme: kicks the user
 - /invitelink: gets invitelink
 - /promote: promotes the user replied to
 - /demote: demotes the user replied to
 - /adminlist: list of admins in the chat
"""

PIN_HANDLER = CommandHandler("pin", pin, pass_args=True)
UNPIN_HANDLER = CommandHandler("unpin", unpin)

KICK_HANDLER = CommandHandler("ban", kick, pass_args=True)
UNKICK_HANDLER = CommandHandler("unban", unkick, pass_args=True)
KICKME_HANDLER = CommandHandler("kickme", kickme)

INVITE_HANDLER = CommandHandler("invitelink", invite)

PROMOTE_HANDLER = CommandHandler("promote", promote, pass_args=True)
DEMOTE_HANDLER = CommandHandler("demote", demote, pass_args=True)

ADMINLIST_HANDLER = CommandHandler("adminlist", adminlist, filters=Filters.group)

dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(UNKICK_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(ADMINLIST_HANDLER)
