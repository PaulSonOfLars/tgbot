from telegram.ext import CommandHandler, MessageHandler

from tg_bot import sql, dispatcher
from tg_bot.custom_filters import HashFilter


def get(bot, update, args):
    chat_id = update.effective_chat.id
    if len(args) >= 1:
        notename = args[0]

        note = sql.get_note(chat_id, notename)
        if note:
            update.effective_message.reply_text(note.value)
            return
        else:
            update.effective_message.reply_text("This doesn't exist")
    else:
        update.effective_message.reply_text("Get rekt")


def hash_get(bot, update):
    message = update.effective_message.text
    fst_word = message.split()[0]
    no_hash = fst_word[1:]
    get(bot, update, [no_hash])


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
        print(note_data.text)
        sql.add_note_to_db(chat_id, notename, note_data.text)
        update.effective_message.reply_text("yas! added replied message " + notename)

    else:
        update.effective_message.reply_text("Dude, theres no note")


def clear(bot, update, args):
    chat_id = update.effective_chat.id
    notename = args[0]

    sql.rm_note(chat_id, notename)
    update.effective_message.reply_text("Successfully removed note")

get_handler = CommandHandler("get", get, pass_args=True)
save_handler = CommandHandler("save", save)
delete_handler = CommandHandler("clear", clear, pass_args=True)
hash_get_handler = MessageHandler(HashFilter, hash_get)

dispatcher.add_handler(get_handler)
dispatcher.add_handler(save_handler)
dispatcher.add_handler(delete_handler)
dispatcher.add_handler(hash_get_handler)


