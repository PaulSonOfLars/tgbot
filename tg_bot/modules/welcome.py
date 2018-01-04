import telegram
from telegram import ParseMode
from telegram.ext import MessageHandler, Filters, CommandHandler, run_async
from telegram.utils.helpers import escape_markdown

import tg_bot.modules.sql.welcome_sql as sql
from tg_bot import dispatcher, OWNER_ID
from tg_bot.modules.helper_funcs import user_admin, markdown_parser, escape_invalid_curly_brackets

VALID_WELCOME_FORMATTERS = ['first', 'last', 'fullname', 'username', 'id', 'count', 'chatname']


@run_async
def new_member(bot, update):
    chat = update.effective_chat
    if update.effective_user.id == OWNER_ID:
        update.effective_message.reply_text("Master is in the houseeee, let's get this party started!")
        return

    should_welc, cust_welcome, _ = sql.get_preference(chat.id)
    if should_welc:
        new_members = update.effective_message.new_chat_members
        for new_mem in new_members:
            # Don't welcome yourself
            if not new_mem.id == bot.id:
                if cust_welcome:
                    if new_mem.last_name:
                        fullname = "{} {}".format(new_mem.first_name, new_mem.last_name)
                    else:
                        fullname = new_mem.first_name
                    count = chat.get_members_count()
                    if new_mem.username:
                        username = "@" + escape_markdown(new_mem.username)
                    else:
                        username = "[{}](tg://user?id={})".format(new_mem.first_name, new_mem.id)

                    valid_format = escape_invalid_curly_brackets(cust_welcome, VALID_WELCOME_FORMATTERS)
                    res = valid_format.format(first=new_mem.first_name,
                                              last=new_mem.last_name or new_mem.first_name,
                                              fullname=fullname, username=username,
                                              count=count, chatname=chat.title, id=new_mem.id)
                else:
                    res = sql.DEFAULT_WELCOME.format(first=new_mem.first_name)
                try:
                    update.effective_message.reply_text(markdown_parser(res), parse_mode=ParseMode.MARKDOWN)
                except IndexError:

                    update.effective_message.reply_text(markdown_parser(
                        sql.DEFAULT_WELCOME.format(first=new_mem.first_name) +
                        "\nNote: the current welcome message is invalid. Please update."),
                        parse_mode=ParseMode.MARKDOWN)
                except KeyError:
                    update.effective_message.reply_text(markdown_parser(
                        sql.DEFAULT_WELCOME.format(first=new_mem.first_name) +
                        "\nNote: the current welcome message is invalid. Please update."),
                        parse_mode=ParseMode.MARKDOWN)


@run_async
def left_member(bot, update):
    chat = update.effective_chat
    should_welc, _, cust_leave = sql.get_preference(chat.id)
    if should_welc:
        left_mem = update.effective_message.left_chat_member
        if left_mem:
            if left_mem.id == bot.id:
                bot.send_message(OWNER_ID, "I've just been kicked from {}.".format(chat.title
                                                                                   or chat.first_name
                                                                                   or chat.id))
                return
            if cust_leave:
                if left_mem.last_name:
                    fullname = "{} {}".format(left_mem.first_name, left_mem.last_name)
                else:
                    fullname = left_mem.first_name
                count = chat.get_members_count()
                if left_mem.username:
                    username = "@" + escape_markdown(left_mem.username)
                else:
                    username = "[{}](tg://user?id={})".format(left_mem.first_name, left_mem.id)

                valid_format = escape_invalid_curly_brackets(cust_leave, VALID_WELCOME_FORMATTERS)
                res = valid_format.format(first=left_mem.first_name,
                                          last=left_mem.last_name or left_mem.first_name,
                                          fullname=fullname, username=username,
                                          count=count, chatname=chat.title, id=left_mem.id)
            else:
                res = sql.DEFAULT_LEAVE

            try:
                update.effective_message.reply_text(markdown_parser(res), parse_mode=ParseMode.MARKDOWN)
            except IndexError:
                update.effective_message.reply_text(markdown_parser(
                    sql.DEFAULT_LEAVE + "\nNote: the current leave message is invalid. Please update."),
                    parse_mode=ParseMode.MARKDOWN)
            except KeyError:
                update.effective_message.reply_text(markdown_parser(
                    sql.DEFAULT_LEAVE + "\nNote: the current leave message is invalid. Please update."),
                    parse_mode=ParseMode.MARKDOWN)


@run_async
@user_admin
def welcome(bot, update, args):
    chat = update.effective_chat
    # if no args, show current replies.
    if len(args) == 0:
        pref, welcome_m, leave_m = sql.get_preference(chat.id)
        reply_setting = "This chat has it's welcome setting set to: {}.".format(pref)
        reply_welcome = "This chat has it's welcome setting set to: {}, the welcome message is:\n{}, and the leave \
            message is too long to display.".format(pref, welcome_m)
        reply_both = "This chat has it's welcome setting set to: {}, the welcome message is:\n'{}', and the leave \
            message is:'{}'.".format(pref, welcome_m, leave_m)

        if len(reply_both) < telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(reply_both)
        elif len(reply_welcome) < telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(reply_welcome)
        else:
            update.effective_message.reply_text(reply_setting)

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_preference(str(chat.id), True)
            update.effective_message.reply_text("I'll be polite!")

        elif args[0].lower() in ("off", "no"):
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
        txt = args[1]
        offset = len(txt) - len(raw_text)  # set correct offset relative to command
        markdown_welcome_message = markdown_parser(txt, entities=msg.parse_entities(), offset=offset)

        sql.set_custom_welcome(chat_id, markdown_welcome_message)
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
        txt = args[1]
        offset = len(txt) - len(raw_text)  # set correct offset relative to command
        markdown_leave_message = markdown_parser(txt, entities=msg.parse_entities(), offset=offset)

        sql.set_custom_leave(chat_id, markdown_leave_message)
        update.effective_message.reply_text("Successfully set custom leave message!")


@run_async
@user_admin
def reset_leave(bot, update):
    chat_id = update.effective_chat.id
    sql.set_custom_leave(chat_id, "")
    update.effective_message.reply_text("Successfully reset leave message to default!")


WELC_HELP_TXT = "Your group's welcome/leave messages can be personalised in multiple ways. If you want the messages " \
                "to be individually generated, like the default welcome message is, you can use *these* variables:\n" \
                " - `{first}`: this represents the user's *first* name\n" \
                " - `{last}`: this represents the user's *last* name. Defaults to first name if user has no " \
                "last name.\n" \
                " - `{fullname}`: this represents the user's *full* name. Defaults to first name if user has no " \
                "last name.\n" \
                " - `{username}`: this represents the user's *username*. Defaults to a mention of the user's " \
                "first name.\n" \
                " - `{id}`: this represents the user's *id*\n" \
                " - `{count}`: this represents the user's *member number*.\n" \
                " - `{chatname}`: this represents the *current chat name*.\n" \
                "\nEach variable MUST be surrounded by {} to be replaced." \
                "\nWelcome messages also support markdown, so you can make any elements bold/italic/code/links."


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
PREF_HANDLER = CommandHandler("welcome", welcome, pass_args=True, filters=Filters.group)
SET_WELCOME = CommandHandler("setwelcome", set_welcome, filters=Filters.group)
SET_LEAVE = CommandHandler("setleave", set_leave, filters=Filters.group)
RESET_WELCOME = CommandHandler("resetwelcome", reset_welcome, filters=Filters.group)
RESET_LEAVE = CommandHandler("resetleave", reset_leave, filters=Filters.group)
WELCOME_HELP = CommandHandler("welcomehelp", welcome_help)

dispatcher.add_handler(NEW_MEM_HANDLER)
dispatcher.add_handler(LEFT_MEM_HANDLER)
dispatcher.add_handler(PREF_HANDLER)
dispatcher.add_handler(SET_WELCOME)
dispatcher.add_handler(SET_LEAVE)
dispatcher.add_handler(RESET_WELCOME)
dispatcher.add_handler(RESET_LEAVE)
dispatcher.add_handler(WELCOME_HELP)
