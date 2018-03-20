import re
from io import BytesIO
from typing import Optional, List

from telegram import MAX_MESSAGE_LENGTH, ParseMode, InlineKeyboardMarkup
from telegram import Message, Update, Bot
from telegram.error import BadRequest
from telegram.ext import CommandHandler, RegexHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown

import tg_bot.modules.sql.notes_sql as sql
from tg_bot import dispatcher, MESSAGE_DUMP, LOGGER
from tg_bot.modules.helper_funcs.chat_status import user_admin
from tg_bot.modules.helper_funcs.extraction import extract_text
from tg_bot.modules.helper_funcs.misc import build_keyboard
from tg_bot.modules.helper_funcs.string_handling import button_markdown_parser, markdown_parser

FILE_MATCHER = re.compile(r"^###file_id(!photo)?###:(.*?)(?:\s|$)")


# Do not async
def get(bot, update, notename, show_none=True):
    chat_id = update.effective_chat.id
    note = sql.get_note(chat_id, notename)
    message = update.effective_message  # type: Optional[Message]

    if note:
        # If not is replying to a message, reply to that message (unless its an error)
        if message.reply_to_message:
            reply_text = message.reply_to_message.reply_text
        else:
            reply_text = message.reply_text

        if note.is_reply:
            if MESSAGE_DUMP:
                try:
                    bot.forward_message(chat_id=chat_id, from_chat_id=MESSAGE_DUMP, message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        message.reply_text("This message seems to have been lost - I'll remove it "
                                           "from your notes list.")
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
            else:
                try:
                    bot.forward_message(chat_id=chat_id, from_chat_id=chat_id, message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        message.reply_text("Looks like the original sender of this note has deleted "
                                           "their message - sorry! Get your bot admin to start using a "
                                           "message dump to avoid this. I'll remove this note from "
                                           "your saved notes.")
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
        else:
            keyb = []
            if note.has_buttons:
                buttons = sql.get_buttons(chat_id, notename)
                keyb = build_keyboard(buttons)

            keyboard = InlineKeyboardMarkup(keyb)
            try:
                reply_text(note.value, parse_mode=ParseMode.MARKDOWN,
                           disable_web_page_preview=True,
                           reply_markup=keyboard)
            except BadRequest as excp:
                if excp.message == "Entity_mention_user_invalid":
                    message.reply_text("Looks like you tried to mention someone I've never seen before. If you really "
                                       "want to mention them, forward one of their messages to me, and I'll be able "
                                       "to tag them!")
                elif FILE_MATCHER.match(note.value):
                    message.reply_text("This note was an incorrectly imported file from another bot - I can't use "
                                       "it. If you really need it, you'll have to save it again. In "
                                       "the meantime, I'll remove it from your notes list.")
                    sql.rm_note(chat_id, notename)
                else:
                    message.reply_text("This note could not be sent, as it is incorrectly formatted. Ask in "
                                       "@MarieSupport if you can't figure out why!")
                    LOGGER.exception("Could not parse message #%s in chat %s", notename, str(chat_id))
                    LOGGER.warning("Message was: %s", str(note.value))
        return
    elif show_none:
        message.reply_text("This note doesn't exist")


@run_async
def cmd_get(bot: Bot, update: Update, args: List[str]):
    if len(args) >= 1:
        notename = args[0]
        get(bot, update, notename, show_none=True)
    else:
        update.effective_message.reply_text("Get rekt")


@run_async
def hash_get(bot: Bot, update: Update):
    message = update.effective_message.text
    fst_word = message.split()[0]
    no_hash = fst_word[1:]
    get(bot, update, no_hash, show_none=False)


@run_async
@user_admin
def save_replied(bot: Bot, update: Update):
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

    msg = update.effective_message.reply_to_message  # type: Optional[Message]

    if msg.from_user.is_bot:
        text = extract_text(msg)
        if text:
            sql.add_note_to_db(chat_id, notename, markdown_parser(text), is_reply=False)
            update.effective_message.reply_text("Seems like you're trying to save a message from a bot. Unfortunately, "
                                                "bots can't forward bot messages, so I can't save the exact message. "
                                                "\nI'll save all the text I can, but if you want more, you'll have to "
                                                "forward the message yourself, and then save it.")
        else:
            update.effective_message.reply_text("Bots are kinda handicapped by telegram, making it hard for bots to "
                                                "interract with other bots, so I can't save this message "
                                                "like I usually would - do you mind forwarding it and "
                                                "then saving that new message? Thanks!")
        return

    if MESSAGE_DUMP:
        msg = bot.forward_message(chat_id=MESSAGE_DUMP, from_chat_id=chat_id, message_id=msg.message_id)

    sql.add_note_to_db(chat_id, notename, msg.message_id, is_reply=True)
    update.effective_message.reply_text("Yas! Added replied message {}".format(notename))


@run_async
@user_admin
def save(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    args = raw_text.split(None, 2)  # use python's maxsplit to separate Cmd, note_name, and data

    if len(args) >= 3:
        note_name = args[1]
        note = args[2]

        offset = len(note) - len(raw_text)  # set correct offset relative to command + notename
        markdown_note, buttons = button_markdown_parser(note, entities=msg.parse_entities(), offset=offset)

        note_data = markdown_note.strip()
        if not note_data:
            msg.reply_text("You can't save an empty message! If you added a button, you MUST "
                           "have some text in the message too.")
            return

        sql.add_note_to_db(chat_id, note_name, note_data, is_reply=False, buttons=buttons)

        msg.reply_text(
            "Yas! Added {note_name}.\nGet it with /get {note_name}, or #{note_name}".format(note_name=note_name))

    else:
        msg.reply_text("Dude, there's no note")


@run_async
@user_admin
def clear(bot: Bot, update: Update, args: List[str]):
    chat_id = update.effective_chat.id
    if len(args) >= 1:
        notename = args[0]

        if sql.rm_note(chat_id, notename):
            update.effective_message.reply_text("Successfully removed note.")
        else:
            update.effective_message.reply_text("That's not a note in my database!")


@run_async
def list_notes(bot: Bot, update: Update):
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


def __import_data__(chat_id, data):
    failures = []
    for notename, notedata in data.get('extra', {}).items():
        match = FILE_MATCHER.match(notedata)

        if match:
            failures.append(notename)
            notedata = notedata[match.end():].strip()
            if notedata:
                sql.add_note_to_db(chat_id, notename[1:], notedata)
        else:
            sql.add_note_to_db(chat_id, notename[1:], notedata)

    if failures:
        with BytesIO(str.encode("\n".join(failures))) as output:
            output.name = "failed_imports.txt"
            dispatcher.bot.send_document(chat_id, document=output, filename="failed_imports.txt",
                                         caption="These files/photos failed to import due to originating "
                                                 "from another bot. This is a telegram API restriction - each bot sees "
                                                 "files with a different file_id, to avoid one bot accessing another's "
                                                 "files. Sorry for the inconvenience!")


def __stats__():
    return "{} notes, across {} chats.".format(sql.num_notes(), sql.num_chats())


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    notes = sql.get_all_chat_notes(chat_id)
    return "There are `{}` notes in this chat.".format(len(notes))


__help__ = """
 - /get  <notename>: get the note with this notename
 - #<notename>: same as /get
 - /notes or /saved: list all saved notes in this chat

*Admin only:*
 - /save <notename> <notedata>: saves notedata as a note with name notename
A button can be added to a note by using standard markdown link syntax - the link should just be prepended with a \
`buttonurl:` section, as such: `[somelink](buttonurl:example.com)`. Check /markdownhelp for more info.
 - /save <notename>: save the replied message as a note with name notename
 - /clear <notename>: clear note with this name
"""

__mod_name__ = "Notes"

GET_HANDLER = CommandHandler("get", cmd_get, pass_args=True)
HASH_GET_HANDLER = RegexHandler(r"^#[^\s]+", hash_get)

SAVE_HANDLER = CommandHandler("save", save, filters=~Filters.reply)
REPL_SAVE_HANDLER = CommandHandler("save", save_replied, filters=Filters.reply)
DELETE_HANDLER = CommandHandler("clear", clear, pass_args=True)

LIST_HANDLER = CommandHandler(["notes", "saved"], list_notes)

dispatcher.add_handler(GET_HANDLER)
dispatcher.add_handler(SAVE_HANDLER)
dispatcher.add_handler(REPL_SAVE_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(HASH_GET_HANDLER)
