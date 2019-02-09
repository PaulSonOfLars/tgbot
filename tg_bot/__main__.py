import datetime
import importlib
import re
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import Unauthorized, BadRequest, TimedOut, NetworkError, ChatMigrated, TelegramError
from telegram.ext import CommandHandler, Filters, MessageHandler, CallbackQueryHandler
from telegram.ext.dispatcher import run_async, DispatcherHandlerStop, Dispatcher
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher, updater, TOKEN, WEBHOOK, OWNER_ID, DONATION_LINK, CERT_PATH, PORT, URL, LOGGER, \
    ALLOW_EXCL, DEVBRANCH
# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from tg_bot.modules import ALL_MODULES
from tg_bot.modules.helper_funcs.chat_status import is_user_admin
from tg_bot.modules.helper_funcs.misc import paginate_modules

import tg_bot.modules.sql.users_sql as sql

PM_START_TEXT = """
Hallo {}, mein Name ist *{}*!\n
Ich bin einer der Gruppen Verwaltungs Bot der Frankfurter Pokémon Go Community.
Alle Details zum Datenschutz von mir findest du [hier](https://www.cloud-ffm.eu/klikdiklak/datenschutz.html)

mit dem Befehl /dsgvo löschst du alle Informationen zu deiner Person aus der Datenbank dieses Bots!
_Insofern dies nicht entgegen des öffentlichen Interesse wirkt, siehe _ [Datenschutz](https://www.cloud-ffm.eu/klikdiklak/datenschutz.html)_._

Eine Liste meiner Befehle findest du hier /help
"""

HELP_STRINGS = """
Ich bin modularisiert aufgebaut, und kann *effektiv* nur von den Admins der Frankfurter Pokémon Go Community\
 verwendet werden, oder von meinem [Besitzer](https://t.me/Finte25).\n\nFür Hilfestellung zu einem speziellen Modul, klicke\
 unten einfach auf den entsprechenden Knopf!

*Haupt Befehle:*
 - /start   : startet den Bot
 - /help.   : sendet diese Nachricht
 - /settings:
   - Via PM    : sendet dir die Einstellungen für alle Module.
   - Via Gruppe: wird dich in einen privaten chat weiterleiten.

{}
*Verfügbare Module:*
""".format("" if not ALLOW_EXCL else "\nAlle Befehle können mit / oder ! benutzt werden\n")

DONATE_STRING = """Heya, glad to hear you want to donate!
But there is not donationen needed - I made this for free for the community"""

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []

CHAT_SETTINGS = {}
USER_SETTINGS = {}

GDPR = []

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("tg_bot.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if not imported_module.__mod_name__.lower() in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__gdpr__"):
        GDPR.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(chat_id=chat_id,
                                text=text,
                                parse_mode=ParseMode.MARKDOWN,
                                reply_markup=keyboard,
                                disable_web_page_preview=True)


@run_async
def test(bot: Bot, update: Update):
    # pprint(eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


@run_async
def start(bot: Bot, update: Update, args: List[str]):
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            first_name = update.effective_user.first_name
            update.effective_message.reply_text(
                PM_START_TEXT.format(escape_markdown(first_name), escape_markdown(bot.first_name), OWNER_ID),
                parse_mode=ParseMode.MARKDOWN)
    else:
        update.effective_message.reply_text("Ich bin bereits aktiv?")


# for test purposes
def error_callback(bot, update, error):
    try:
        raise error
    except Unauthorized:
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        pass
        # handle slow connection problems
    except NetworkError:
        pass
        # handle other connection problems
    except ChatMigrated as err:
        pass
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


@run_async
def help_button(bot: Bot, update: Update):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)
    try:
        if mod_match:
            module = mod_match.group(1)
            text = "Hier ist die Hilfestellung für das *{}* Modul:\n".format(HELPABLE[module].__mod_name__) \
                   + HELPABLE[module].__help__
            query.message.reply_text(text=text,
                                     disable_web_page_preview=True,
                                     parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(
                                         [[InlineKeyboardButton(text="Zurück", callback_data="help_back")]]))

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.reply_text(HELP_STRINGS,
                                     disable_web_page_preview=True,
                                     parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(
                                         paginate_modules(curr_page - 1, HELPABLE, "help")))

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.reply_text(HELP_STRINGS,
                                     disable_web_page_preview=True,
                                     parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(
                                         paginate_modules(next_page + 1, HELPABLE, "help")))

        elif back_match:
            query.message.reply_text(text=HELP_STRINGS,
                                     disable_web_page_preview=True,
                                     parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help")))

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        query.message.delete()
    except BadRequest as excp:
        if excp.message == "Message is not modified":
            pass
        elif excp.message == "Query_id_invalid":
            pass
        elif excp.message == "Message can't be deleted":
            pass
        else:
            LOGGER.exception("Exception in help buttons. %s", str(query.data))


@run_async
def get_help(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:

        update.effective_message.reply_text("Kontaktiere mich per PM um eine Liste der möglichen Befehle zu erhalten",
                                            reply_markup=InlineKeyboardMarkup(
                                                [[InlineKeyboardButton(text="Help",
                                                                       url="t.me/{}?start=help".format(
                                                                           bot.username))]]))
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = "Hier ist die Hilfestellung für das *{}* Modul:\n".format(HELPABLE[module].__mod_name__) \
               + HELPABLE[module].__help__
        send_help(chat.id, text, InlineKeyboardMarkup([[InlineKeyboardButton(text="Back", callback_data="help_back")]]))

    else:
        send_help(chat.id, HELP_STRINGS)


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id)) for mod in USER_SETTINGS.values())
            dispatcher.bot.send_message(user_id, "Hier sind deine momentanen Einstellungen:" + "\n\n" + settings,
                                        parse_mode=ParseMode.MARKDOWN)

        else:
            dispatcher.bot.send_message(user_id, "Es scheint als sind keine benutzerspezifischen Einstellungen vorhanden :'(",
                                        parse_mode=ParseMode.MARKDOWN)

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(user_id,
                                        text="Which module would you like to check {}'s settings for?".format(
                                            chat_name),
                                        reply_markup=InlineKeyboardMarkup(
                                            paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)))
        else:
            dispatcher.bot.send_message(user_id, "Es scheint als sind keine Chat Einstellungen vorhanden :'(\nSende das "
                                                 "in einer Gruppe in der du Admin bist um ihre aktuellen Einstellungen herauszufinden!",
                                        parse_mode=ParseMode.MARKDOWN)

@run_async
def settings_button(bot: Bot, update: Update):
    query = update.callback_query
    user = update.effective_user
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(escape_markdown(chat.title),
                                                                                     CHAT_SETTINGS[
                                                                                         module].__mod_name__) + \
                   CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.reply_text(text=text,
                                     parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(
                                         [[InlineKeyboardButton(text="Back",
                                                                callback_data="stngs_back({})".format(chat_id))]]))

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text("Hi there! There are quite a few settings for {} - go ahead and pick what "
                                     "you're interested in.".format(chat.title),
                                     reply_markup=InlineKeyboardMarkup(
                                         paginate_modules(curr_page - 1, CHAT_SETTINGS, "stngs",
                                                          chat=chat_id)))

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text("Hi there! There are quite a few settings for {} - go ahead and pick what "
                                     "you're interested in.".format(chat.title),
                                     reply_markup=InlineKeyboardMarkup(
                                         paginate_modules(next_page + 1, CHAT_SETTINGS, "stngs",
                                                          chat=chat_id)))

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            query.message.reply_text(text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                                          "you're interested in.".format(escape_markdown(chat.title)),
                                     parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(paginate_modules(0, CHAT_SETTINGS, "stngs",
                                                                                        chat=chat_id)))

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        query.message.delete()
    except BadRequest as excp:
        if excp.message == "Message is not modified":
            pass
        elif excp.message == "Query_id_invalid":
            pass
        elif excp.message == "Message can't be deleted":
            pass
        else:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


@run_async
def get_settings(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = msg.text.split(None, 1)

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Klicke hier um deine, sowie die Einstellungen dieses Chats zu erhalten."
            msg.reply_text(text,
                           reply_markup=InlineKeyboardMarkup(
                               [[InlineKeyboardButton(text="Settings",
                                                      url="t.me/{}?start=stngs_{}".format(
                                                          bot.username, chat.id))]]))
        else:
            text = "Klicke hier um deine Einstellungen zu prüfen"

    else:
        send_settings(chat.id, user.id, True)


@run_async
def donate(bot: Bot, update: Update):
    user = update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]

    if chat.type == "private":
        update.effective_message.reply_text(DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

        if OWNER_ID != 254318997 and DONATION_LINK:
            update.effective_message.reply_text("You can also donate to the person currently running me "
                                                "[here]({})".format(DONATION_LINK),
                                                parse_mode=ParseMode.MARKDOWN)

    else:
        try:
            bot.send_message(user.id, DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

            update.effective_message.reply_text("I've PM'ed you about donating to my creator!")
        except Unauthorized:
            update.effective_message.reply_text("Contact me in PM first to get donation information.")


def migrate_chats(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop




@run_async
def add_channel(bot, update):
    if (update.effective_chat.type == "channel"):
        channel_id = update.effective_chat.id
        channel_name = dispatcher.bot.getChat(channel_id).title
        try:
            retval = sql.add_channel(str(channel_id), str(channel_name))
        except Exception as e:
            print(e)
            pass



def status_messages(bot: Bot, update: Update):
    """Echo the user message."""
    print("status_message recieved")
    print(update)

def main():
    start_handler = CommandHandler("start", start, pass_args=True)
    help_handler = CommandHandler("help", get_help)
    help_callback_handler = CallbackQueryHandler(help_button, pattern=r"help_")
    settings_handler = CommandHandler("settings", get_settings)
    settings_callback_handler = CallbackQueryHandler(settings_button, pattern=r"stngs_")
    #donate_handler = CommandHandler("donate", donate)
    migrate_handler = MessageHandler(Filters.status_update.migrate, migrate_chats)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    #dispatcher.add_handler(donate_handler)


    # add antiflood processor
    Dispatcher.process_update = process_update

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="127.0.0.1",
                              port=PORT,
                              url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN,
                                    certificate=open(CERT_PATH, 'rb'))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)

    else:
        LOGGER.info("Using long polling.")
        updater.start_polling(timeout=15, read_latency=4, allowed_updates=[])

    updater.idle()


CHATS_CNT = {}
CHATS_TIME = {}


def process_update(self, update):
    add_channel(self, update)
    
#    print(msg)

    # An error happened while polling
    if isinstance(update, TelegramError):
        try:
            self.dispatch_error(None, update)
        except Exception:
            self.logger.exception('An uncaught error was raised while handling the error')
        return

    now = datetime.datetime.utcnow()
    cnt = CHATS_CNT.get(update.effective_chat.id, 0)

    t = CHATS_TIME.get(update.effective_chat.id, datetime.datetime(1970, 1, 1))
    if t and now > t + datetime.timedelta(0, 1):
        CHATS_TIME[update.effective_chat.id] = now
        cnt = 0
    else:
        cnt += 1

    if cnt > 10:
        return

    CHATS_CNT[update.effective_chat.id] = cnt
    for group in self.groups:
        try:
            for handler in (x for x in self.handlers[group] if x.check_update(update)):
                handler.handle_update(update, self)
                break

        # Stop processing with any other handler.
        except DispatcherHandlerStop:
            self.logger.debug('Stopping further handlers due to DispatcherHandlerStop')
            break

        # Dispatch any error.
        except TelegramError as te:
            self.logger.warning('A TelegramError was raised while processing the Update')

            try:
                self.dispatch_error(update, te)
            except DispatcherHandlerStop:
                self.logger.debug('Error handler stopped further handlers')
                break
            except Exception:
                self.logger.exception('An uncaught error was raised while handling the error')

        # Errors should not stop the thread.
        except Exception:
            self.logger.exception('An uncaught error was raised while processing the update')


if __name__ == '__main__':
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    main()
