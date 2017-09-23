from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async

import tg_bot.modules.sql.locks_sql as sql
from tg_bot import dispatcher
from tg_bot.modules.helper_funcs import can_delete, is_user_admin, bot_can_delete, user_admin
from tg_bot.modules.sql import users_sql

LOCK_TYPES = ["sticker", "audio", "voice", "document", "video", "contact", "photo"]

RESTRICTION_TYPES = ['messages', 'media', 'other', 'previews']

REST_GROUP = 1


def locktypes(bot, update):
    update.effective_message.reply_text("\n - ".join(["Locks: "] + LOCK_TYPES + RESTRICTION_TYPES))


@user_admin
@bot_can_delete
def lock(bot, update, args):
    chat = update.effective_chat
    message = update.effective_message
    if can_delete(chat, bot.id):
        if len(args) >= 1:
            if args[0] in LOCK_TYPES:
                sql.update_lock(chat.id, args[0], locked=True)
                message.reply_text("Locked {} for everyone!".format(args[0]))

            elif args[0] in RESTRICTION_TYPES:
                sql.update_restriction(chat.id, args[0], locked=True)
                message.reply_text("locked {}".format(args[0]))
                members = users_sql.get_chat_members(chat.id)
                if args[0] == "messages":
                    for mem in members:
                        bot.restrict_chat_member(chat.id, mem.user,
                                                 can_send_messages=True)
                elif args[0] == "media":
                    for mem in members:
                        bot.restrict_chat_member(chat.id, mem.user,
                                                 can_send_messages=True,
                                                 can_send_media_messages=True)
                elif args[0] == "other":
                    for mem in members:
                        bot.restrict_chat_member(chat.id, mem.user,
                                                 can_send_messages=True,
                                                 can_send_media_messages=True,
                                                 can_send_other_messages=True)
                elif args[0] == "previews":
                    for mem in members:
                        bot.restrict_chat_member(chat.id, mem.user,
                                                 can_send_messages=True,
                                                 can_send_media_messages=True,
                                                 can_add_web_page_previews=True)

    else:
        message.reply_text("I'm not an administrator, or haven't got delete rights.")


@user_admin
def unlock(bot, update, args):
    chat = update.effective_chat
    message = update.effective_message
    if is_user_admin(chat, message.from_user.id):
        if len(args) >= 1:
            if args[0] in LOCK_TYPES:
                sql.update_lock(chat.id, args[0], locked=False)
                message.reply_text("Unlocked {} for everyone!".format(args[0]))

            elif args[0] in RESTRICTION_TYPES:
                sql.update_restriction(chat.id, args[0], locked=False)
                members = users_sql.get_chat_members(chat.id)
                if args[0] == "messages":
                    for mem in members:
                        bot.restrict_chat_member(chat.id, mem.user,
                                                 can_send_messages=False,
                                                 can_send_media_messages=False,
                                                 can_send_other_messages=False)
                elif args[0] == "media":
                    for mem in members:
                        bot.restrict_chat_member(chat.id, mem.user,
                                                 can_send_messages=True,
                                                 can_send_media_messages=False)
                elif args[0] == "other":
                    for mem in members:
                        bot.restrict_chat_member(chat.id, mem.user,
                                                 can_send_messages=True,
                                                 can_send_media_messages=True,
                                                 can_send_other_messages=False)
                elif args[0] == "previews":
                    for mem in members:
                        bot.restrict_chat_member(chat.id, mem.user,
                                                 can_send_messages=True,
                                                 can_send_media_messages=True,
                                                 can_add_web_page_previews=False)

            else:
                message.reply_text("What are you trying to unlock...? Try /locktypes for the list of locks")

        else:
            bot.sendMessage(chat.id, "What are you trying to unlock...?")


@run_async
def del_sticker(bot, update):
    chat = update.effective_chat
    if sql.is_locked(chat.id, "sticker") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
def del_audio(bot, update):
    chat = update.effective_chat
    if sql.is_locked(chat.id, "audio") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
def del_voice(bot, update):
    chat = update.effective_chat
    if sql.is_locked(chat.id, "voice") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
def del_document(bot, update):
    chat = update.effective_chat
    if sql.is_locked(chat.id, "document") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
def del_video(bot, update):
    chat = update.effective_chat
    if sql.is_locked(chat.id, "video") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
def del_contact(bot, update):
    chat = update.effective_chat
    if sql.is_locked(chat.id, "contact") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
def del_photo(bot, update):
    chat = update.effective_chat
    if sql.is_locked(chat.id, "photo") and can_delete(chat, bot.id):
        update.effective_message.delete()


@run_async
def rest_msg(bot, update):
    msg = update.effective_message
    chat = update.effective_chat
    if sql.is_restr_locked(chat.id, "messages") and can_delete(chat, bot.id) and not is_user_admin(chat,
                                                                                                   msg.from_user.id):
        msg.delete()
        bot.restrict_chat_member(chat.id, msg.from_user.id,
                                 can_send_messages=False,
                                 can_send_media_messages=False,
                                 can_send_other_messages=False)


@run_async
def rest_media(bot, update):
    msg = update.effective_message
    chat = update.effective_chat
    if sql.is_restr_locked(chat.id, "media") and can_delete(chat, bot.id) and not is_user_admin(chat, msg.from_user.id):
        msg.delete()
        bot.restrict_chat_member(chat.id, msg.from_user.id,
                                 can_send_messages=True,
                                 can_send_media_messages=False,
                                 can_send_other_messages=False)


@run_async
def rest_other(bot, update):
    msg = update.effective_message
    chat = update.effective_chat
    if sql.is_restr_locked(chat.id, "other") and can_delete(chat, bot.id) and not is_user_admin(chat, msg.from_user.id):
        msg.delete()
        bot.restrict_chat_member(chat.id, msg.from_user.id,
                                 can_send_messages=True,
                                 can_send_media_messages=True,
                                 can_send_other_messages=False)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = """
 - /locktypes: a list of possible locktypes
 - /lock <type>: lock items of a certain type (not available in private)
 - /unlock <type>: unlock items of a certain type (not available in private)
"""

MESSAGES = Filters.text | Filters.contact | Filters.location | Filters.venue
MEDIA = Filters.audio | Filters.document | Filters.video | Filters.voice | Filters.photo
OTHER = Filters.game | Filters.sticker  # NOTE: GIFS too

LOCKTYPES_HANDLER = CommandHandler("locktypes", locktypes)
LOCK_HANDLER = CommandHandler("lock", lock, pass_args=True, filters=~Filters.private)
UNLOCK_HANDLER = CommandHandler("unlock", unlock, pass_args=True, filters=~Filters.private)

REST_MSG_HANDLER = MessageHandler(MESSAGES, rest_msg)
REST_MEDIA_HANDLER = MessageHandler(MEDIA, rest_media)
REST_OTHERS_HANDLER = MessageHandler(OTHER, rest_other)

STICKER_HANDLER = MessageHandler(Filters.sticker, del_sticker)
AUDIO_HANDLER = MessageHandler(Filters.audio, del_audio)
VOICE_HANDLER = MessageHandler(Filters.voice, del_voice)
DOCUMENT_HANDLER = MessageHandler(Filters.document, del_document)
VIDEO_HANDLER = MessageHandler(Filters.video, del_video)
CONTACT_HANDLER = MessageHandler(Filters.contact, del_contact)
PHOTO_HANDLER = MessageHandler(Filters.photo, del_photo)  # TODO: gif detection -> mime_type?

dispatcher.add_handler(LOCK_HANDLER)
dispatcher.add_handler(UNLOCK_HANDLER)
dispatcher.add_handler(LOCKTYPES_HANDLER)

dispatcher.add_handler(REST_MSG_HANDLER, REST_GROUP)
dispatcher.add_handler(REST_MEDIA_HANDLER, REST_GROUP)
dispatcher.add_handler(REST_OTHERS_HANDLER, REST_GROUP)

dispatcher.add_handler(STICKER_HANDLER)
dispatcher.add_handler(AUDIO_HANDLER)
dispatcher.add_handler(VOICE_HANDLER)
dispatcher.add_handler(DOCUMENT_HANDLER)
dispatcher.add_handler(VIDEO_HANDLER)
dispatcher.add_handler(CONTACT_HANDLER)
dispatcher.add_handler(PHOTO_HANDLER)
