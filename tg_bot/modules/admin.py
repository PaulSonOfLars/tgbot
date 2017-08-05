from telegram.ext import CommandHandler
from telegram.ext.dispatcher import run_async

from tg_bot import dispatcher


def is_admin(bot, update):
    return update.effective_chat.get_member(bot.id).status == 'administrator'


@run_async
def promote(bot, update):
    if is_admin(bot, update):
        chat_id = update.effective_chat.id
        prev_message = update.effective_message.reply_to_message
        if prev_message:
            user_id = prev_message.from_user.id
            res = bot.promoteChatMember(chat_id, user_id,
                                        can_change_info=True,
                                        can_post_messages=True,
                                        can_edit_messages=True,
                                        can_delete_messages=True,
                                        can_invite_users=True,
                                        can_restrict_members=True,
                                        can_pin_messages=True,
                                        can_promote_members=True)
            print("promoted " + str(res))


@run_async
def demote(bot, update):
    if is_admin(bot, update):
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
            print("promoted " + str(res))


@run_async
def restrict(bot, update):
    if is_admin(bot, update):
        chat_id = update.effective_chat.id
        prev_message = update.effective_message.reply_to_message
        if prev_message:
            user_id = prev_message.from_user.id
            print(str(user_id) + "is the user_id")
            print(str(chat_id) + "is the chat id")
            res = bot.promoteChatMember(int(chat_id), int(user_id),
                                        can_edit_message=True)
            print("promoted " + str(res))


@run_async
def pin(bot, update):
    if is_admin(bot, update):
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        group = chat_type != "private" and chat_type != "channel"

        prev_message = update.effective_message.reply_to_message

        if prev_message and group:
            bot.pinChatMessage(chat_id, prev_message.message_id)
            update.effective_message.reply_text("Pinned!")


pin_handler = CommandHandler("pin", pin)
promote_handler = CommandHandler("promote", promote)
demote_handler = CommandHandler("demote", demote)
restrict_handler = CommandHandler("restrict", restrict)

dispatcher.add_handler(pin_handler)
dispatcher.add_handler(promote_handler)
dispatcher.add_handler(demote_handler)
dispatcher.add_handler(restrict_handler)
