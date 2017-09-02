from functools import wraps
from tg_bot.config import Development as Config


def can_delete(chat, bot_id):
    return chat.get_member(bot_id).can_delete_messages


def is_user_admin(chat, user_id):
    return chat.get_member(user_id).status == 'administrator'


def is_bot_admin(chat, bot_id):
    return chat.get_member(bot_id).status == 'administrator'


def bot_admin(func):
    @wraps(func)
    def is_admin(bot, update, *args, **kwargs):
        if update.effective_chat.get_member(bot.id).status == 'administrator':
            func(bot, update, *args, **kwargs)
        else:
            update.effective_message.reply_text("I ain't admin!")

    return is_admin


def user_admin(func):
    @wraps(func)
    def is_admin(bot, update, *args, **kwargs):
        user_id = update.effective_message.from_user.id
        if update.effective_chat.get_member(user_id).status == 'administrator' or user_id == Config.OWNER_ID:
            func(bot, update, *args, **kwargs)
        else:
            update.effective_message.reply_text("Who dis non-admin telling me what to do?")

    return is_admin


def is_reply(func):
    @wraps(func)
    def reply(bot, update, *args, **kwargs):
        if update.effective_message.reply_to_message:
            func(bot, update, *args, **kwargs)

    return reply
