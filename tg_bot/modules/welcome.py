import html
import time
from typing import Optional, List

import requests as req
from telegram import Message, Chat, Update, Bot, User
from telegram import ParseMode, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import MessageHandler, Filters, CommandHandler, run_async
from telegram.utils.helpers import mention_markdown, mention_html, escape_markdown

import tg_bot.modules.sql.welcome_sql as sql
from tg_bot import dispatcher, OWNER_ID, LOGGER
from tg_bot.modules.helper_funcs.chat_status import user_admin
from tg_bot.modules.helper_funcs.misc import build_keyboard, revert_buttons
from tg_bot.modules.helper_funcs.msg_types import get_welcome_type
from tg_bot.modules.helper_funcs.string_handling import (
    markdown_parser,
    escape_invalid_curly_brackets,
)
from tg_bot.modules.log_channel import loggable
from tg_bot import BAN_STICKER

VALID_WELCOME_FORMATTERS = [
    "first",
    "last",
    "fullname",
    "username",
    "id",
    "count",
    "chatname",
    "mention",
]

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video,
}


# do not async
def send(update, message, keyboard, backup_message):
    try:
        msg = update.effective_message.reply_text(
            message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
        )
    except IndexError:
        msg = update.effective_message.reply_text(
            markdown_parser(
                backup_message + "\nNota: Il messaggio corrente è "
                                 "invalido a causa di problemi di markdown. Potrebbe essere a causa del "
                                 "nome dell'utente."
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
    except KeyError:
        msg = update.effective_message.reply_text(
            markdown_parser(
                backup_message + "\nNote: the current message is "
                                 "invalid due to an issue with some misplaced "
                                 "curly brackets. Please update"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
    except BadRequest as excp:
        if excp.message == "Button_url_invalid":
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message
                    + "\nNota: Il messaggio corrente ha un url non valido "
                      "in uno dei bottoni. Per favore, aggiornarlo."
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        elif excp.message == "Unsupported url protocol":
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message + "\nNota: il messaggio corrente ha bottoni che "
                                     "usano un protocollo per gli url non supportato da "
                                     "Telegram. Per favore, aggiornarlo."
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        elif excp.message == "Wrong url host":
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message
                    + "\nNota: il messaggio corrente ha degli url difettosi. "
                      "Per favore, aggiornarlo.."
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
            LOGGER.warning(message)
            LOGGER.warning(keyboard)
            LOGGER.exception("Impossibile parsarlo! Ci sono degli url non validi.")
        else:
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message
                    + "\nNota: un errore si è verificato quando ho provato  "
                      "a inviare il messaggio customizzato. Per favore, risolvere l'errore."
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
            LOGGER.exception()

    return msg


def cas_banned(userid):
    # Query cas
    try:  # Just in case the CAS api endpoint goes down
        response = req.get("https://combot.org/api/cas/check?user_id=" + str(userid))
        response = response.json()
        # if true the user should be banned
        if response["ok"] == True:
            return True  # The user should be banned
        else:
            return False  # The user should not be banned
    except Exception as e:
        LOGGER.warning(e)
        return False


@run_async
def new_member(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    new_members = update.effective_message.new_chat_members
    message = update.effective_message

    should_welc, cust_welcome, welc_type = sql.get_welc_pref(chat.id)
    if should_welc:
        sent = None
        for new_mem in new_members:
            # Check if the username is defined
            if new_mem.username:
                # Check if the user is cas-banned
                if not cas_banned(new_mem.id):
                    # Give the owner a special welcome
                    if new_mem.id == OWNER_ID:
                        update.effective_message.reply_text(
                            "Salve capo!"
                        )
                        continue

                    # Don't welcome yourself
                    elif new_mem.id == bot.id:
                        continue

                    else:
                        # Muting new users
                        bot.restrict_chat_member(
                            chat.id, new_mem.id, can_send_messages=False
                        )

                        # If welcome message is media, send with appropriate function
                        if (
                                welc_type != sql.Types.TEXT
                                and welc_type != sql.Types.BUTTON_TEXT
                        ):
                            ENUM_FUNC_MAP[welc_type](chat.id, cust_welcome)
                            return
                        # else, move on
                        first_name = (
                                new_mem.first_name or "PersonWithNoName"
                        )  # edge case of empty name - occurs for some bugs.

                        if cust_welcome:
                            if new_mem.last_name:
                                fullname = "{} {}".format(first_name, new_mem.last_name)
                            else:
                                fullname = first_name
                            count = chat.get_members_count()
                            mention = mention_markdown(new_mem.id, first_name)
                            if new_mem.username:
                                username = "@" + escape_markdown(new_mem.username)
                            else:
                                username = mention

                            valid_format = escape_invalid_curly_brackets(
                                cust_welcome, VALID_WELCOME_FORMATTERS
                            )
                            res = valid_format.format(
                                first=escape_markdown(first_name),
                                last=escape_markdown(new_mem.last_name or first_name),
                                fullname=escape_markdown(fullname),
                                username=username,
                                mention=mention,
                                count=count,
                                chatname=escape_markdown(chat.title),
                                id=new_mem.id,
                            )
                            buttons = sql.get_welc_buttons(chat.id)
                            keyb = build_keyboard(buttons)
                        else:
                            res = sql.DEFAULT_WELCOME.format(first=first_name)
                            keyb = []

                        keyboard = InlineKeyboardMarkup(keyb)

                        sent = send(
                            update,
                            res,
                            keyboard,
                            sql.DEFAULT_WELCOME.format(first=first_name),
                        )  # type: Optional[Message]

                else:
                    # BEGINNING THE BAN
                    log = (
                        "<b>CAS BAN:</b>" "\n#CASBAN" "\n<b>User:</b> {}".format(new_mem.id)
                    )

                    reason = "Ban via CAS api query"

                    if reason:
                        log += "\n<b>Motivo:</b> {}".format(reason)

                    user_id = new_mem.id
                    try:
                        chat.kick_member(user_id)
                        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer electus sticker
                        message.reply_text("BANNATO VIA SISTEMA AUTOMATICO CAS!")
                        return log

                    except BadRequest as excp:
                        if excp.message == "Reply message not found":
                            # Do not reply
                            message.reply_text("BANNATO!", quote=False)
                            return log
                        else:
                            LOGGER.warning(update)
                            LOGGER.exception(
                                "ERROR in CAS banning user %s in chat %s (%s) due to %s",
                                user_id,
                                chat.title,
                                chat.id,
                                excp.message,
                            )
                            message.reply_text(
                                "Diamine, non riesco a bannare questo utente."
                            )
            else:
                # Kicking the user because of the username
                user_id = new_mem.id
                chat.kick_member(user_id, until_date=time.time() + 300)
                bot.send_sticker(chat.id, BAN_STICKER)  # banhammer electus sticker
                message.reply_text("L'utente non ha uno username, quindi è stato rimosso.")

        prev_welc = sql.get_clean_pref(chat.id)
        if prev_welc:
            try:
                bot.delete_message(chat.id, prev_welc)
            except BadRequest as excp:
                pass

            if sent:
                sql.set_clean_welcome(chat.id, sent.message_id)


@run_async
def left_member(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    should_goodbye, cust_goodbye, goodbye_type = sql.get_gdbye_pref(chat.id)
    if should_goodbye:
        left_mem = update.effective_message.left_chat_member
        if left_mem:
            # Ignore bot being kicked
            if left_mem.id == bot.id:
                return

            # Give the owner a special goodbye
            if left_mem.id == OWNER_ID:
                update.effective_message.reply_text("RIP Master")
                return

            # if media goodbye, use appropriate function for it
            if goodbye_type != sql.Types.TEXT and goodbye_type != sql.Types.BUTTON_TEXT:
                ENUM_FUNC_MAP[goodbye_type](chat.id, cust_goodbye)
                return

            first_name = (
                    left_mem.first_name or "PersonWithNoName"
            )  # edge case of empty name - occurs for some bugs.
            if cust_goodbye:
                if left_mem.last_name:
                    fullname = "{} {}".format(first_name, left_mem.last_name)
                else:
                    fullname = first_name
                count = chat.get_members_count()
                mention = mention_markdown(left_mem.id, first_name)
                if left_mem.username:
                    username = "@" + escape_markdown(left_mem.username)
                else:
                    username = mention

                valid_format = escape_invalid_curly_brackets(
                    cust_goodbye, VALID_WELCOME_FORMATTERS
                )
                res = valid_format.format(
                    first=escape_markdown(first_name),
                    last=escape_markdown(left_mem.last_name or first_name),
                    fullname=escape_markdown(fullname),
                    username=username,
                    mention=mention,
                    count=count,
                    chatname=escape_markdown(chat.title),
                    id=left_mem.id,
                )
                buttons = sql.get_gdbye_buttons(chat.id)
                keyb = build_keyboard(buttons)

            else:
                res = sql.DEFAULT_GOODBYE
                keyb = []

            keyboard = InlineKeyboardMarkup(keyb)

            send(update, res, keyboard, sql.DEFAULT_GOODBYE)


@run_async
@user_admin
def welcome(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    # if no args, show current replies.
    if len(args) == 0 or args[0].lower() == "noformat":
        noformat = args and args[0].lower() == "noformat"
        pref, welcome_m, welcome_type = sql.get_welc_pref(chat.id)
        update.effective_message.reply_text(
            "Il messaggio di benvenuto personalizzato è impostato a: `{}`.\n*Il messaggio di benvenuto "
            "(senza le variabili in {{}}) è:*".format(pref),
            parse_mode=ParseMode.MARKDOWN,
        )

        if welcome_type == sql.Types.BUTTON_TEXT:
            buttons = sql.get_welc_buttons(chat.id)
            if noformat:
                welcome_m += revert_buttons(buttons)
                update.effective_message.reply_text(welcome_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                send(update, welcome_m, keyboard, sql.DEFAULT_WELCOME)

        else:
            if noformat:
                ENUM_FUNC_MAP[welcome_type](chat.id, welcome_m)

            else:
                ENUM_FUNC_MAP[welcome_type](
                    chat.id, welcome_m, parse_mode=ParseMode.MARKDOWN
                )

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_welc_preference(str(chat.id), True)
            update.effective_message.reply_text("Farò il bravo!")

        elif args[0].lower() in ("off", "no"):
            sql.set_welc_preference(str(chat.id), False)
            update.effective_message.reply_text("Mi sono offeso, non saluterò più!")

        else:
            # idek what you're writing, say yes or no
            update.effective_message.reply_text("Capisco solo 'no/yes' o 'off/on'!")


@run_async
@user_admin
def goodbye(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]

    if len(args) == 0 or args[0] == "noformat":
        noformat = args and args[0] == "noformat"
        pref, goodbye_m, goodbye_type = sql.get_gdbye_pref(chat.id)
        update.effective_message.reply_text(
            "Il messaggio di goodbye è impostato a: `{}`.\n*Il messaggio "
            "(senza le variabili in {{}}) è:*".format(pref),
            parse_mode=ParseMode.MARKDOWN,
        )

        if goodbye_type == sql.Types.BUTTON_TEXT:
            buttons = sql.get_gdbye_buttons(chat.id)
            if noformat:
                goodbye_m += revert_buttons(buttons)
                update.effective_message.reply_text(goodbye_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                send(update, goodbye_m, keyboard, sql.DEFAULT_GOODBYE)

        else:
            if noformat:
                ENUM_FUNC_MAP[goodbye_type](chat.id, goodbye_m)

            else:
                ENUM_FUNC_MAP[goodbye_type](
                    chat.id, goodbye_m, parse_mode=ParseMode.MARKDOWN
                )

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_gdbye_preference(str(chat.id), True)
            update.effective_message.reply_text(
                "Mi dispiacerà quando le persone se ne andranno!"
            )

        elif args[0].lower() in ("off", "no"):
            sql.set_gdbye_preference(str(chat.id), False)
            update.effective_message.reply_text("Quando un utente uscirà dal gruppo non intraprenderò nessuna azione!")

        else:
            # idek what you're writing, say yes or no
            update.effective_message.reply_text("Capisco solo 'no/yes' o 'off/on'!")


@run_async
@user_admin
@loggable
def set_welcome(bot: Bot, update: Update) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        msg.reply_text("Non hai specificato come devo rispondere!")
        return ""

    sql.set_custom_welcome(chat.id, content or text, data_type, buttons)
    msg.reply_text("Ho impostato correttamente il messaggio di benvenuto!")

    return (
        "<b>{}:</b>"
        "\n#SET_WELCOME"
        "\n<b>Admin:</b> {}"
        "\nSet the welcome message.".format(
            html.escape(chat.title), mention_html(user.id, user.first_name)
        )
    )


@run_async
@user_admin
@loggable
def reset_welcome(bot: Bot, update: Update) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    sql.set_custom_welcome(chat.id, sql.DEFAULT_WELCOME, sql.Types.TEXT)
    update.effective_message.reply_text(
        "Ho resettato il messaggio di benvenuto a quello di defualt!"
    )
    return (
        "<b>{}:</b>"
        "\n#RESET_WELCOME"
        "\n<b>Admin:</b> {}"
        "\nReset the welcome message to default.".format(
            html.escape(chat.title), mention_html(user.id, user.first_name)
        )
    )


@run_async
@user_admin
@loggable
def set_goodbye(bot: Bot, update: Update) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        msg.reply_text("Non hai specificato come devo rispondere!")
        return ""

    sql.set_custom_gdbye(chat.id, content or text, data_type, buttons)
    msg.reply_text("Ho impostato con successo il messaggio di goodbye!")
    return (
        "<b>{}:</b>"
        "\n#SET_GOODBYE"
        "\n<b>Admin:</b> {}"
        "\nSet the goodbye message.".format(
            html.escape(chat.title), mention_html(user.id, user.first_name)
        )
    )


@run_async
@user_admin
@loggable
def reset_goodbye(bot: Bot, update: Update) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    sql.set_custom_gdbye(chat.id, sql.DEFAULT_GOODBYE, sql.Types.TEXT)
    update.effective_message.reply_text(
        "Ho ripristinato con successo il messaggio di goodbye!"
    )
    return (
        "<b>{}:</b>"
        "\n#RESET_GOODBYE"
        "\n<b>Admin:</b> {}"
        "\nReset the goodbye message.".format(
            html.escape(chat.title), mention_html(user.id, user.first_name)
        )
    )


@run_async
@user_admin
@loggable
def clean_welcome(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    if not args:
        clean_pref = sql.get_clean_pref(chat.id)
        if clean_pref:
            update.effective_message.reply_text(
                "Dovrei eliminare i messaggi di benvenuto fino a due giorni."
            )
        else:
            update.effective_message.reply_text(
                "Al momento non posso eliminare i vecchi messaggi di benvenuto!"
            )
        return ""

    if args[0].lower() in ("on", "yes"):
        sql.set_clean_welcome(str(chat.id), True)
        update.effective_message.reply_text(
            "Proverò a cancellare i vecchi messaggi di benvenuto!"
        )
        return (
            "<b>{}:</b>"
            "\n#CLEAN_WELCOME"
            "\n<b>Admin:</b> {}"
            "\nHas toggled clean welcomes to <code>ON</code>.".format(
                html.escape(chat.title), mention_html(user.id, user.first_name)
            )
        )
    elif args[0].lower() in ("off", "no"):
        sql.set_clean_welcome(str(chat.id), False)
        update.effective_message.reply_text(
            "Non posso cancellare i vecchi messaggi di benvenuto."
        )
        return (
            "<b>{}:</b>"
            "\n#CLEAN_WELCOME"
            "\n<b>Admin:</b> {}"
            "\nHas toggled clean welcomes to <code>OFF</code>.".format(
                html.escape(chat.title), mention_html(user.id, user.first_name)
            )
        )
    else:
        # idek what you're writing, say yes or no
        update.effective_message.reply_text("Capisco solo 'on/yes' o 'off/no'!")
        return ""


WELC_HELP_TXT = (
    "Your group's welcome/goodbye messages can be personalised in multiple ways. If you want the messages"
    " to be individually generated, like the default welcome message is, you can use *these* variables:\n"
    " - `{{first}}`: this represents the user's *first* name\n"
    " - `{{last}}`: this represents the user's *last* name. Defaults to *first name* if user has no "
    "last name.\n"
    " - `{{fullname}}`: this represents the user's *full* name. Defaults to *first name* if user has no "
    "last name.\n"
    " - `{{username}}`: this represents the user's *username*. Defaults to a *mention* of the user's "
    "first name if has no username.\n"
    " - `{{mention}}`: this simply *mentions* a user - tagging them with their first name.\n"
    " - `{{id}}`: this represents the user's *id*\n"
    " - `{{count}}`: this represents the user's *member number*.\n"
    " - `{{chatname}}`: this represents the *current chat name*.\n"
    "\nEach variable MUST be surrounded by `{{}}` to be replaced.\n"
    "Welcome messages also support markdown, so you can make any elements bold/italic/code/links. "
    "Buttons are also supported, so you can make your welcomes look awesome with some nice intro "
    "buttons.\n"
    "To create a button linking to your rules, use this: `[Rules](buttonurl://t.me/{}?start=group_id)`. "
    "Simply replace `group_id` with your group's id, which can be obtained via /id, and you're good to "
    "go. Note that group ids are usually preceded by a `-` sign; this is required, so please don't "
    "remove it.\n"
    "If you're feeling fun, you can even set images/gifs/videos/voice messages as the welcome message by "
    "replying to the desired media, and calling /setwelcome.".format(
        dispatcher.bot.username
    )
)


@run_async
@user_admin
def welcome_help(bot: Bot, update: Update):
    update.effective_message.reply_text(WELC_HELP_TXT, parse_mode=ParseMode.MARKDOWN)


# TODO: get welcome data from group butler snap
# def __import_data__(chat_id, data):
#     welcome = data.get('info', {}).get('rules')
#     welcome = welcome.replace('$username', '{username}')
#     welcome = welcome.replace('$name', '{fullname}')
#     welcome = welcome.replace('$id', '{id}')
#     welcome = welcome.replace('$title', '{chatname}')
#     welcome = welcome.replace('$surname', '{lastname}')
#     welcome = welcome.replace('$rules', '{rules}')
#     sql.set_custom_welcome(chat_id, welcome, sql.Types.TEXT)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    welcome_pref, _, _ = sql.get_welc_pref(chat_id)
    goodbye_pref, _, _ = sql.get_gdbye_pref(chat_id)
    return (
        "Questa chat ha la sua preferenza di benvenuto su `{}`.\n"
        "Le preferenze di goodbye sono `{}`.".format(welcome_pref, goodbye_pref)
    )


__help__ = """
{}

*Admin only:*
 - /welcome <on/off>: enable/disable welcome messages.
 - /welcome: shows current welcome settings.
 - /welcome noformat: shows current welcome settings, without the formatting - useful to recycle your welcome messages!
 - /goodbye -> same usage and args as /welcome.
 - /setwelcome <sometext>: set a custom welcome message. If used replying to media, uses that media.
 - /setgoodbye <sometext>: set a custom goodbye message. If used replying to media, uses that media.
 - /resetwelcome: reset to the default welcome message.
 - /resetgoodbye: reset to the default goodbye message.
 - /cleanwelcome <on/off>: On new member, try to delete the previous welcome message to avoid spamming the chat.

 - /welcomehelp: view more formatting information for custom welcome/goodbye messages.
""".format(
    WELC_HELP_TXT
)

__mod_name__ = "Welcomes/Goodbyes"

NEW_MEM_HANDLER = MessageHandler(Filters.status_update.new_chat_members, new_member)
LEFT_MEM_HANDLER = MessageHandler(Filters.status_update.left_chat_member, left_member)
WELC_PREF_HANDLER = CommandHandler(
    "welcome", welcome, pass_args=True, filters=Filters.group
)
GOODBYE_PREF_HANDLER = CommandHandler(
    "goodbye", goodbye, pass_args=True, filters=Filters.group
)
SET_WELCOME = CommandHandler("setwelcome", set_welcome, filters=Filters.group)
SET_GOODBYE = CommandHandler("setgoodbye", set_goodbye, filters=Filters.group)
RESET_WELCOME = CommandHandler("resetwelcome", reset_welcome, filters=Filters.group)
RESET_GOODBYE = CommandHandler("resetgoodbye", reset_goodbye, filters=Filters.group)
CLEAN_WELCOME = CommandHandler(
    "cleanwelcome", clean_welcome, pass_args=True, filters=Filters.group
)
WELCOME_HELP = CommandHandler("welcomehelp", welcome_help)

dispatcher.add_handler(NEW_MEM_HANDLER)
dispatcher.add_handler(LEFT_MEM_HANDLER)
dispatcher.add_handler(WELC_PREF_HANDLER)
dispatcher.add_handler(GOODBYE_PREF_HANDLER)
dispatcher.add_handler(SET_WELCOME)
dispatcher.add_handler(SET_GOODBYE)
dispatcher.add_handler(RESET_WELCOME)
dispatcher.add_handler(RESET_GOODBYE)
dispatcher.add_handler(CLEAN_WELCOME)
dispatcher.add_handler(WELCOME_HELP)
