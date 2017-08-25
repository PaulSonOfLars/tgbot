from telegram.ext import CommandHandler
from telegram.ext.dispatcher import run_async

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs import is_bot_admin, is_user_admin


@run_async
def promote(bot, update):
    chat = update.effective_chat
    message = update.effective_message
    if is_bot_admin(chat, bot.id) and is_user_admin(chat, message.from_user.id):
        chat_id = update.effective_chat.id
        prev_message = update.effective_message.reply_to_message
        if prev_message:
            user_id = prev_message.from_user.id
            # NOTE: Doesnt work atm. TG issue.
            # res = bot.promoteChatMember(chat_id, user_id,
            #                             can_change_info=True,
            #                             can_post_messages=True,
            #                             can_edit_messages=True,
            #                             can_delete_messages=True,
            #                             can_invite_users=True,
            #                             can_restrict_members=True,
            #                             can_pin_messages=True,
            #                             can_promote_members=True)

            # NOTE: but this works. issue due to NoneType in post/edit messages.
            res = bot.promoteChatMember(chat_id, user_id,
                                        can_change_info=True,
                                        can_delete_messages=True,
                                        can_invite_users=True,
                                        can_restrict_members=True,
                                        can_pin_messages=True,
                                        can_promote_members=True)
            if res:
                update.effective_message.reply_text("successfully promoted!")


@run_async
def demote(bot, update):
    chat = update.effective_chat
    message = update.effective_message
    if is_bot_admin(chat, bot.id) and is_user_admin(chat, message.from_user.id):
        chat_id = update.effective_chat.id
        prev_message = update.effective_message.reply_to_message
        if prev_message:
            user_id = prev_message.from_user.id
            res = bot.promoteChatMember(int(chat_id), int(user_id),
                                        can_change_info=False,
                                        can_post_messages=False,
                                        can_edit_messages=False,
                                        can_delete_messages=False,
                                        can_invite_users=False,
                                        can_restrict_members=False,
                                        can_pin_messages=False,
                                        can_promote_members=False)
            if res:
                update.effective_message.reply_text("successfully demoted!")


@run_async
def pin(bot, update, args):
    chat = update.effective_chat
    message = update.effective_message
    if is_bot_admin(chat, bot.id) and is_user_admin(chat, message.from_user.id):
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        is_group = chat_type != "private" and chat_type != "channel"

        prev_message = update.effective_message.reply_to_message

        is_silent = False
        if len(args) >= 1:
            is_silent = args[0].lower() == 'silent'

        if prev_message and is_group:
            bot.pinChatMessage(chat_id, prev_message.message_id, disable_notification=is_silent)


@run_async
def unpin(bot, update):
    chat = update.effective_chat
    message = update.effective_message
    if is_bot_admin(chat, bot.id) and is_user_admin(chat, message.from_user.id):
        chat_id = update.effective_chat.id
        bot.unpinChatMessage(chat_id)


@run_async
def kick(bot, update):
    chat = update.effective_chat
    message = update.effective_message
    if is_bot_admin(chat, bot.id) and is_user_admin(chat, message.from_user.id):
        prev_message = update.effective_message.reply_to_message

        if prev_message:
            user_id = prev_message.from_user.id
            res = update.effective_chat.kick_member(user_id)
            if res:
                update.effective_message.reply_text("Kicked!")


@run_async
def kickme(bot, update):
    chat = update.effective_chat
    if is_bot_admin(chat, bot.id):
        user_id = update.effective_message.from_user.id
        user_is_admin = update.effective_chat.get_member(user_id).status == 'administrator'
        if user_is_admin:
            update.effective_message.reply_text("I would if I could... but you're an admin.")
            return
        res = update.effective_chat.kick_member(user_id)
        if res:
            update.effective_message.reply_text("No problem.")


@run_async
def unkick(bot, update, args):
    chat = update.effective_chat
    message = update.effective_message
    if is_bot_admin(chat, bot.id) and is_user_admin(chat, message.from_user.id):
        if len(args) >= 1:
            user_id = args[0]
        else:
            update.effective_message.reply_text("Give me a numeric user ID!")
            return
        update.effective_chat.unban_member(user_id)


@run_async
def invite(bot, update):
    chat = update.effective_chat
    message = update.effective_message
    if is_bot_admin(chat, bot.id) and is_user_admin(chat, message.from_user.id):
        if chat.username:
            update.effective_message.reply_text(chat.username)
        else:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)

docs = """
 - /pin: pins the message replied to
 - /unpin: unpins the currently pinned message
 - /ban: bans a user
 - /unban <user_id>: unbans a user given his user id
 - /kickme: kicks the user
 - /invite: gets invitelink
 - /promote: promotes the user replied to
 - /demote: demotes the user replied to
"""

PIN_HANDLER = CommandHandler("pin", pin, pass_args=True)
UNPIN_HANDLER = CommandHandler("unpin", unpin)

KICK_HANDLER = CommandHandler("ban", kick)
UNKICK_HANDLER = CommandHandler("unban", unkick, pass_args=True)
KICKME_HANDLER = CommandHandler("kickme", kickme)

INVITE_HANDLER = CommandHandler("invite", invite)

PROMOTE_HANDLER = CommandHandler("promote", promote)
DEMOTE_HANDLER = CommandHandler("demote", demote)

dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(UNKICK_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)

