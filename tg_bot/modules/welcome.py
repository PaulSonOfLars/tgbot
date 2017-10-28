from telegram import ParseMode
from telegram.ext import MessageHandler, Filters, CommandHandler, run_async

import tg_bot.modules.sql.welcome_sql as sql
from tg_bot import dispatcher
from tg_bot.modules.helper_funcs import user_admin


@run_async
def new_member(bot, update):
    chat = update.effective_chat
    should_welc, cust_welcome, _ = sql.get_preference(chat.id)
    if should_welc:
        new_mem = update.effective_message.new_chat_members
        for member in new_mem:
            # Don't welcome yourself
            if not member.id == bot.id:
                if cust_welcome:
                    fullname = "{} {}".format(member.first_name, member.last_name) \
                        if member.last_name \
                        else member.first_name
                    count = chat.get_members_count()
                    res = cust_welcome.format(first=member.first_name,
                                              last=member.last_name or member.first_name,
                                              fullname=fullname, username=member.username or member.first_name,
                                              count=count)
                else:
                    res = "Hey {}, how are you?".format(member.first_name)
                update.effective_message.reply_text(res)


@run_async
def left_member(bot, update):
    chat = update.effective_chat
    should_welc, _, cust_leave = sql.get_preference(chat.id)
    if should_welc:
        left_mem = update.effective_message.left_chat_member
        if left_mem:
            if cust_leave:
                fullname = "{} {}".format(left_mem.first_name, left_mem.last_name) \
                    if left_mem.last_name \
                    else left_mem.first_name
                count = chat.get_members_count()
                res = cust_leave.format(first=left_mem.first_name,
                                        last=left_mem.last_name or left_mem.first_name,
                                        fullname=fullname, username=left_mem.username or left_mem.first_name,
                                        count=count)
            else:
                res = "Nice knowing ya!"
            update.effective_message.reply_text(res)


@run_async
@user_admin
def change_preference(bot, update, args):
    chat = update.effective_chat
    if len(args) >= 1:
        if args[0].lower() == "on" or args[0].lower() == "yes":
            sql.set_preference(str(chat.id), True)
            update.effective_message.reply_text("I'll be polite!")

        elif args[0].lower() == "off" or args[0].lower() == "no":
            sql.set_preference(str(chat.id), False)
            update.effective_message.reply_text("I'm sulking, not saying hello anymore.")

        else:
            # idek what you're writing, say yes or no
            update.effective_message.reply_text("I understand 'on/yes' or 'off/no' only!")


@run_async
@user_admin
def set_welcome(bot, update):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    raw_text = msg.text
    args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
    if len(args) == 2:
        sql.set_custom_welcome(chat_id, args[1])
        update.effective_message.reply_text("Successfully set custom welcome message!")


@run_async
@user_admin
def reset_welcome(bot, update):
    chat_id = update.effective_chat.id
    sql.set_custom_welcome(chat_id, "")
    update.effective_message.reply_text("Successfully reset welcome message to default!")


@run_async
@user_admin
def set_leave(bot, update):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    raw_text = msg.text
    args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
    if len(args) == 2:
        sql.set_custom_leave(chat_id, args[1])
        update.effective_message.reply_text("Successfully set custom leave message!")


@run_async
@user_admin
def reset_leave(bot, update):
    chat_id = update.effective_chat.id
    sql.set_custom_leave(chat_id, "")
    update.effective_message.reply_text("Successfully reset leave message to default!")


WELC_HELP_TXT = "Your group's welcome/leave messages can be personalised in multiple ways. If you want the messages " \
                "to be individually generated, like the default welcome message is, you can use *these* variables:\n" \
                " - `{first}`: this represents the new user's *first* name\n" \
                " - `{last}`: this represents the new user's *last* name. Defaults to first name if user has no " \
                "last name.\n" \
                " - `{fullname}`: this represents the new user's *full* name. Defaults to first name if user has no " \
                "last name.\n" \
                " - `{username}`: this represents the new user's *username*. Defaults to a mention of the user's " \
                "first name.\n" \
                " - `{count}`: this represents the new user's *member number*.\n\n" \
                "Each variable MUST be surrounded by {} to be replaced."


@run_async
@user_admin
def welcome_help(bot, update):
    update.effective_message.reply_text(WELC_HELP_TXT, parse_mode=ParseMode.MARKDOWN)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = """
 - /welcome <on/off>: enable/disable welcome and goodbye messages
 - /setwelcome <sometext>: set a custom welcome message.
 - /setleave <sometext>: set a custom leaving message.
 - /resetwelcome: reset to the default welcome message.
 - /resetleave: reset to the default leaving message.
 - /welcomehelp: view formatting information for custom welcome messages.
"""

NEW_MEM_HANDLER = MessageHandler(Filters.status_update.new_chat_members, new_member)
LEFT_MEM_HANDLER = MessageHandler(Filters.status_update.left_chat_member, left_member)
PREF_HANDLER = CommandHandler("welcome", change_preference, pass_args=True)
SET_WELCOME = CommandHandler("setwelcome", set_welcome)
SET_LEAVE = CommandHandler("setleave", set_leave)
RESET_WELCOME = CommandHandler("resetwelcome", reset_welcome)
RESET_LEAVE = CommandHandler("resetleave", reset_leave)
WELCOME_HELP = CommandHandler("welcomehelp", welcome_help)

dispatcher.add_handler(NEW_MEM_HANDLER)
dispatcher.add_handler(LEFT_MEM_HANDLER)
dispatcher.add_handler(PREF_HANDLER)
dispatcher.add_handler(SET_WELCOME)
dispatcher.add_handler(SET_LEAVE)
dispatcher.add_handler(RESET_WELCOME)
dispatcher.add_handler(RESET_LEAVE)
dispatcher.add_handler(WELCOME_HELP)
