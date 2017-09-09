from telegram.ext import MessageHandler, Filters, CommandHandler

import tg_bot.modules.sql.welcome_sql as sql
from tg_bot import dispatcher


def new_member(bot, update):
    chat = update.effective_chat
    if sql.get_preference(chat.id):
        new_mem = update.effective_message.new_chat_members
        for member in new_mem:
            # Don't welcome yourself
            if not member.id == bot.id:
                update.effective_message.reply_text("My man {}, how are you?".format(member.first_name))


def left_member(bot, update):
    chat = update.effective_chat
    if sql.get_preference(chat.id):
        left_mem = update.effective_message.left_chat_member
        if left_mem:
            update.effective_message.reply_text("Nice knowing ya!")


def change_preference(bot, update, args):
    chat = update.effective_chat
    if len(args) >= 1:
        if args[0].lower() == "yes":
            sql.set_preference(str(chat.id), True)
            update.effective_message.reply_text("I'll be polite!")

        elif args[0].lower() == "no":
            sql.set_preference(str(chat.id), False)
            update.effective_message.reply_text("I'm sulking, not saying hello anymore.")

        else:
            # idek what youre writing, say yes or no
            update.effective_message.reply_text("I understand 'yes' or 'no' only!")

__help__ = """
 - /welcome <yes/no>: enable/disable welcome and goodbye messages
"""

# TODO: /setwelcome command

NEW_MEM_HANDLER = MessageHandler(Filters.status_update.new_chat_members, new_member)
LEFT_MEM_HANDLER = MessageHandler(Filters.status_update.left_chat_member, left_member)
PREF_HANDLER = CommandHandler("welcome", change_preference, pass_args=True)

dispatcher.add_handler(NEW_MEM_HANDLER)
dispatcher.add_handler(LEFT_MEM_HANDLER)
dispatcher.add_handler(PREF_HANDLER)
