import re
from functools import wraps

from telegram.utils.helpers import escape_markdown


from tg_bot import OWNER_ID


def can_delete(chat, bot_id):
    return chat.get_member(bot_id).can_delete_messages


def is_user_admin(chat, user_id):
    return chat.get_member(user_id).status == 'administrator' or chat.get_member(
        user_id).status == 'creator' or user_id == OWNER_ID


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
        if is_user_admin(update.effective_chat, user_id):
            func(bot, update, *args, **kwargs)
        else:
            update.effective_message.reply_text("Who dis non-admin telling me what to do?")

    return is_admin


def user_not_admin(func):
    @wraps(func)
    def is_not_admin(bot, update, *args, **kwargs):
        user_id = update.effective_message.from_user.id
        if not is_user_admin(update.effective_chat, user_id):
            func(bot, update, *args, **kwargs)

    return is_not_admin


# match * (bold) (don't escape if in url)
# match _ (italics) (don't escape if in url)
# match ` (code)
# match []() (markdown link)
# else, escape *, _, `, and [
MATCH_MD = r'\*(.*?)\*|' \
           r'_(.*?)_|' \
           r'`(.*?)`|' \
           r'(?<!\\)(\[.*?\])(\(.*?\))|' \
           r'(?P<esc>[\*_`\[])'


def _selective_escape(to_parse):
    """
    Escape all invalid markdown

    :param to_parse: text to escape
    :return: valid markdown string
    """
    offset = 0  # offset to be used as adding a \ character causes the string to shift
    for e in re.finditer(MATCH_MD, to_parse):
        if e.group('esc'):
            ent_start = e.start()
            to_parse = to_parse[:ent_start + offset] + '\\' + to_parse[ent_start + offset:]
            offset += 1
    return to_parse


def markdown_parser(txt, entities=None, offset=0):
    """
    Parse a string, escaping all invalid markdown entities.

    Escapes URL's so as to avoid URL mangling.
    Re-adds any telegram code entities obtained from the entities object.

    :param txt: text to parse
    :param entities: dict of message entities in text
    :param offset: message offset - command and notename length
    :return: valid markdown string
    """
    if not entities:
        entities = {}

    # regex to find []() links
    pattern = re.compile(r'(?<!\\)\[.*?\]\((.*?)\)')
    prev = 0
    res = ""
    # for each message entity, check start pos
    for ent, ent_text in entities.items():
        start = ent.offset + offset
        end = ent.length + start
        # URL handling
        if ent.type == "url":
            # if a markdown link starts at the same point as an entity URL link, don't escape it
            if any(match.start(1) == start for match in re.finditer(pattern, txt)):
                continue
            # else, check the escapes between the prev and last and forcefully escape the url to avoid mangling
            else:
                res += _selective_escape(txt[prev:start] or "") + escape_markdown(ent_text)
        # code handling
        elif ent.type == "code":
            res += _selective_escape(txt[prev:start]) + '`' + ent_text + '`'
        # anything else
        else:
            continue
        prev = end

    res += _selective_escape(txt[prev:])  # add the rest of the text
    return res
