from telegram import MAX_MESSAGE_LENGTH, ParseMode
from telegram.ext import CommandHandler, RegexHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown

import tg_bot.modules.sql.notes_sql as sql
from tg_bot import dispatcher
from tg_bot.config import Development as Config
from tg_bot.modules.helper_funcs import markdown_parser, user_admin


# Do not async
def get(bot, update, notename, show_none=True):
    chat_id = update.effective_chat.id
    note = sql.get_note(chat_id, notename)
    if note:
        if note.is_reply:
            bot.forward_message(chat_id=chat_id, from_chat_id=Config.MESSAGE_DUMP or chat_id, message_id=note.value)
        else:
            update.effective_message.reply_text(note.value, parse_mode=ParseMode.MARKDOWN,
                                                disable_web_page_preview=True)
        return
    elif show_none:
        update.effective_message.reply_text("This note doesn't exist")


@run_async
def cmd_get(bot, update, args):
    if len(args) >= 1:
        notename = args[0]
        get(bot, update, notename, show_none=True)
    else:
        update.effective_message.reply_text("Get rekt")


@run_async
def hash_get(bot, update):
    message = update.effective_message.text
    fst_word = message.split()[0]
    no_hash = fst_word[1:]
    get(bot, update, no_hash, show_none=False)


@run_async
@user_admin
def save_replied(bot, update):
    chat_id = update.effective_chat.id
    text = update.effective_message.text
    args = text.split(None, 3)  # use python's maxsplit to separate Cmd, note_name, and data
    if len(args) == 3 and args[1] == "from":
        notename = args[2]
    elif len(args) >= 2:
        notename = args[1]
    else:
        update.effective_message.reply_text("You need to give me a notename to save this message!")
        return

    msg = update.effective_message.reply_to_message

    if Config.MESSAGE_DUMP:
        msg = bot.forward_message(chat_id=Config.MESSAGE_DUMP, from_chat_id=chat_id, message_id=msg.message_id)

    sql.add_note_to_db(chat_id, notename, msg.message_id, is_reply=True)
    update.effective_message.reply_text("yas! added replied message " + notename)


@run_async
@user_admin
def save(bot, update):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    raw_text = msg.text
    args = raw_text.split(None, 2)  # use python's maxsplit to separate Cmd, note_name, and data

    if len(args) >= 3:
        notename = args[1]
        txt = args[2]

        # Ensure backticks arent removed by telegram
        counter = len(txt) - len(raw_text)  # set correct offset relative to command + notename

        sql.add_note_to_db(chat_id, notename,
                           markdown_parser(txt, entities=msg.parse_entities(), offset=counter),
                           is_reply=False)
        update.effective_message.reply_text("yas! added " + notename)

    else:
        update.effective_message.reply_text("Dude, theres no note")


def clear(bot, update, args):
    chat_id = update.effective_chat.id
    if len(args) >= 1:
        notename = args[0]

        if sql.rm_note(chat_id, notename):
            update.effective_message.reply_text("Successfully removed note")
        else:
            update.effective_message.reply_text("That's not a note in my database!")


def list_notes(bot, update):
    chat_id = update.effective_chat.id
    note_list = sql.get_all_chat_notes(chat_id)

    msg = "*Notes in chat:*\n"
    for note in note_list:
        note_name = escape_markdown(" - {}\n".format(note.name))
        if len(msg) + len(note_name) > MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            msg = ""
        msg += note_name

    if msg == "*Notes in chat:*\n":
        update.effective_message.reply_text("No notes in this chat!")

    elif len(msg) != 0:
        update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = """
 - /get  <notename>: get the note with this notename
 - #<notename>: same as /get
 - /save <notename> <notedata>: saves notedata as a note with name notename
 - /save <notename>: save the replied message as a note with name notename
 - /notes or /saved: list all saved notes in this chat
 - /clear <notename>: clear note with this name
"""

GET_HANDLER = CommandHandler("get", cmd_get, pass_args=True)
HASH_GET_HANDLER = RegexHandler(r"^#([^\s])+", hash_get)

SAVE_HANDLER = CommandHandler("save", save, filters=~Filters.reply)
REPL_SAVE_HANDLER = CommandHandler("save", save_replied, filters=Filters.reply)
DELETE_HANDLER = CommandHandler("clear", clear, pass_args=True)

LIST_HANDLER = CommandHandler("notes", list_notes)
LIST_HANDLER2 = CommandHandler("saved", list_notes)

dispatcher.add_handler(GET_HANDLER)
dispatcher.add_handler(SAVE_HANDLER)
dispatcher.add_handler(REPL_SAVE_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(LIST_HANDLER2)
dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(HASH_GET_HANDLER)
