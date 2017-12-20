import re
from functools import wraps

from telegram import MAX_MESSAGE_LENGTH, MessageEntity
from telegram.ext import BaseFilter
from telegram.utils.helpers import escape_markdown

from tg_bot import OWNER_ID, SUDO_USERS
from tg_bot.modules.users import get_user_id


def can_delete(chat, bot_id):
    return chat.get_member(bot_id).can_delete_messages


def is_user_admin(chat, user_id, member=None):
    if not member:
        member = chat.get_member(user_id)
    return member.status == 'administrator' or member.status == 'creator' or member.user.id == OWNER_ID


def is_bot_admin(chat, bot_id):
    bot_member = chat.get_member(bot_id)
    return bot_member.status == 'administrator' or bot_member.status == 'creator'


def is_user_in_chat(chat, user_id):
    member = chat.get_member(user_id)
    return member.status != 'left' and member.status != 'kicked'


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
            update.effective_message.reply_text("I'm not admin!")

    return is_admin


def user_admin(func):
    @wraps(func)
    def is_admin(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        if is_user_admin(update.effective_chat, user_id):
            func(bot, update, *args, **kwargs)
        else:
            update.effective_message.reply_text("Who dis non-admin telling me what to do?")

    return is_admin


def user_admin_no_reply(func):
    @wraps(func)
    def is_admin(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        if is_user_admin(update.effective_chat, user_id):
            func(bot, update, *args, **kwargs)

    return is_admin


def user_not_admin(func):
    @wraps(func)
    def is_not_admin(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        if not is_user_admin(update.effective_chat, user_id):
            func(bot, update, *args, **kwargs)

    return is_not_admin


def extract_user(message, args):
    prev_message = message.reply_to_message

    if message.entities and message.parse_entities([MessageEntity.TEXT_MENTION]):
        entities = message.parse_entities([MessageEntity.TEXT_MENTION])
        for ent in entities:
            return ent.user.id

    elif len(args) >= 1 and args[0][0] == '@':
        user = args[0]
        user_id = get_user_id(user)
        if not user_id:
            message.reply_text("I don't have that user in my db. You'll be able to interact with them if "
                               "you reply to that person's message instead.")
            return None
        else:
            return user_id

    elif len(args) >= 1 and args[0].isdigit():
        return int(args[0])

    elif prev_message:
        return prev_message.from_user.id

    else:
        return None


def extract_text(message):
    return message.text or message.caption or (message.sticker.emoji if message.sticker else None)


# match * (bold) (don't escape if in url)
# match _ (italics) (don't escape if in url)
# match ` (code)
# match []() (markdown link)
# else, escape *, _, `, and [
MATCH_MD = re.compile(r'\*(.*?)\*|'
                      r'_(.*?)_|'
                      r'`(.*?)`|'
                      r'(?<!\\)(\[.*?\])(\(.*?\))|'
                      r'(?P<esc>[*_`\[])')


def _selective_escape(to_parse):
    """
    Escape all invalid markdown

    :param to_parse: text to escape
    :return: valid markdown string
    """
    offset = 0  # offset to be used as adding a \ character causes the string to shift
    for match in MATCH_MD.finditer(to_parse):
        if match.group('esc'):
            ent_start = match.start()
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
            if any(match.start(1) <= start and end <= match.end(1) for match in pattern.finditer(txt)):
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


def split_message(msg):
    if len(msg) < MAX_MESSAGE_LENGTH:
        return [msg]
    else:
        lines = msg.splitlines()
        small_msg = ""
        result = []
        for line in lines:
            if len(small_msg) + len(line) + 1 < MAX_MESSAGE_LENGTH:
                small_msg += line + "\n"
            else:
                result.append(small_msg)
                small_msg = line + "\n"
        else:
            # Else statement at the end of the for loop, so append the leftover string.
            result.append(small_msg)

        return result


class _Sudoers(BaseFilter):
    def filter(self, message):
        return bool(message.from_user and message.from_user.id in SUDO_USERS)


sudo_filter = _Sudoers()
