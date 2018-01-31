from typing import List

from telegram import Message, MessageEntity
from telegram.error import BadRequest

from tg_bot.modules.users import get_user_id


def extract_user(message: Message, args: List[str]):
    prev_message = message.reply_to_message

    user_id = None

    if message.entities and message.parse_entities([MessageEntity.TEXT_MENTION]):
        entities = message.parse_entities([MessageEntity.TEXT_MENTION])
        for ent in entities:
            user_id = ent.user.id

    elif len(args) >= 1 and args[0][0] == '@':
        user = args[0]
        user_id = get_user_id(user)
        if not user_id:
            message.reply_text("I don't have that user in my db. You'll be able to interact with them if "
                               "you reply to that person's message instead, or forward one of that user's messages.")
            return
        else:
            user_id = user_id

    elif len(args) >= 1 and args[0].isdigit():
        user_id = int(args[0])

    elif prev_message:
        user_id = prev_message.from_user.id

    else:
        return None

    try:
        message.chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User_id_invalid":
            message.reply_text("I don't seem to have interacted with this user before - please forward a message from "
                               "them to give me control! (like a voodoo doll, I need a piece of them to be able "
                               "to execute certain commands...)")
            return

    return user_id


def extract_text(message):
    return message.text or message.caption or (message.sticker.emoji if message.sticker else None)
