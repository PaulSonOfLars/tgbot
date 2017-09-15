import re
from functools import wraps

from tg_bot.config import Development as Config


def can_delete(chat, bot_id):
    return chat.get_member(bot_id).can_delete_messages


def is_user_admin(chat, user_id):
    return chat.get_member(user_id).status == 'administrator' or chat.get_member(user_id).status == 'creator'


def is_bot_admin(chat, bot_id):
    return chat.get_member(bot_id).status == 'administrator' or chat.get_member(bot_id).status == 'creator'


def bot_can_delete(func):
    @wraps(func)
    def delete_rights(bot, update, *args, **kwargs):
        if update.effective_chat.get_member(bot.id).can_delete_messages:
            func(bot, update, *args, **kwargs)
        else:
            update.effective_message.reply_text("I can't delete messages here! "
                                                "Make sure I'm admin and can delete other user's messages.")

    return delete_rights


def can_pin(func):
    @wraps(func)
    def pin_rights(bot, update, *args, **kwargs):
        if update.effective_chat.get_member(bot.id).can_pin_messages:
            func(bot, update, *args, **kwargs)
        else:
            update.effective_message.reply_text("I can't pin messages here! "
                                                "Make sure I'm admin and can pin messages.")

    return pin_rights


def can_promote(func):
    @wraps(func)
    def promote_rights(bot, update, *args, **kwargs):
        if update.effective_chat.get_member(bot.id).can_promote_members:
            func(bot, update, *args, **kwargs)
        else:
            update.effective_message.reply_text("I can't promote/demote people here! "
                                                "Make sure I'm admin and can appoint new admins.")

    return promote_rights


def bot_admin(func):
    @wraps(func)
    def is_admin(bot, update, *args, **kwargs):
        if is_bot_admin(update.effective_chat, bot.id):
            func(bot, update, *args, **kwargs)
        else:
            update.effective_message.reply_text("I ain't admin!")

    return is_admin


def user_admin(func):
    @wraps(func)
    def is_admin(bot, update, *args, **kwargs):
        user_id = update.effective_message.from_user.id
        if is_user_admin(update.effective_chat, user_id) or user_id == Config.OWNER_ID:
            func(bot, update, *args, **kwargs)
        else:
            update.effective_message.reply_text("Who dis non-admin telling me what to do?")

    return is_admin


def markdown_parser(txt):
    """
    regex: matches all double *, _, ` as well as valid []() formations.
    if these dont match, match lone *, _ \` and [ assign them the groupname `esc` - and escape them.

    :param txt:  text to parse
    :return: valid markdown string
    """
    match_md = r'\*(.*?)\*|' \
               r'_(.*?)_|' \
               r'`(.*?)`|' \
               r'(?<!\\)(\[.*?\])(\(.*?\))|' \
               r'(?P<esc>[\*`_\[])'
    offset = 0  # offset to be used as adding a \ character causes the string to shift
    for e in re.finditer(match_md, txt):
        # if e.group('astx') or e.group('bctck') or e.group('undes') or e.group('sqbrkt'):
        if e.group('esc'):
            start = e.start()
            txt = txt[:start+offset] + '\\' + txt[start+offset:]
            offset += 1
    return txt
