from telegram.ext import CommandHandler, MessageHandler
from telegram.ext.dispatcher import run_async

from tg_bot import dispatcher
from tg_bot.custom_filters import HashFilter
import tg_bot.modules.sql.notes_sql as sql


def get(update, notename):
    chat_id = update.effective_chat.id
    note = sql.get_note(chat_id, notename)
    if note:
        update.effective_message.reply_text(note.value)
        return
    else:
        update.effective_message.reply_text("This note doesn't exist")


@run_async
def cmd_get(bot, update, args):
    if len(args) >= 1:
        notename = args[0]
        get(update, notename)
    else:
        update.effective_message.reply_text("Get rekt")


@run_async
def hash_get(bot, update):
    message = update.effective_message.text
    fst_word = message.split()[0]
    no_hash = fst_word[1:]
    get(update, no_hash)


def save(bot, update):
    chat_id = update.effective_chat.id
    text = update.effective_message.text
    args = text.split(None, 2)  # use python's maxsplit to separate Cmd, note_name, and data

    if len(args) >= 3:
        notename = args[1]
        note_data = args[2]

        sql.add_note_to_db(chat_id, notename, note_data)
        update.effective_message.reply_text("yas! added " + notename)

    elif update.effective_message.reply_to_message and len(args) >= 2:
        notename = args[1]
        note_data = update.effective_message.reply_to_message
        sql.add_note_to_db(chat_id, notename, note_data.text)
        update.effective_message.reply_text("yas! added replied message " + notename)

    else:
        update.effective_message.reply_text("Dude, theres no note")


def clear(bot, update, args):
    chat_id = update.effective_chat.id
    notename = args[0]

    sql.rm_note(chat_id, notename)
    update.effective_message.reply_text("Successfully removed note")

# TODO: list all notes (and beware max_size limits)

GET_HANDLER = CommandHandler("get", cmd_get, pass_args=True)
SAVE_HANDLER = CommandHandler("save", save)
DELETE_HANDLER = CommandHandler("clear", clear, pass_args=True)
HASH_GET_HANDLER = MessageHandler(HashFilter, hash_get)

dispatcher.add_handler(GET_HANDLER)
dispatcher.add_handler(SAVE_HANDLER)
dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(HASH_GET_HANDLER)
