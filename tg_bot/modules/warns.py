import html
import re
from typing import Optional, List

import telegram
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    User,
    CallbackQuery,
)
from telegram import Message, Chat, Update, Bot
from telegram.error import BadRequest
from telegram.ext import (
    CommandHandler,
    run_async,
    DispatcherHandlerStop,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, BAN_STICKER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import (
    is_user_admin,
    bot_admin,
    user_admin_no_reply,
    user_admin,
    can_restrict,
)
from tg_bot.modules.helper_funcs.extraction import (
    extract_text,
    extract_user_and_text,
    extract_user,
)
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import split_message
from tg_bot.modules.helper_funcs.string_handling import split_quotes
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import warns_sql as sql

WARN_HANDLER_GROUP = 9
CURRENT_WARNING_FILTER_STRING = "<b>Attuali filtri di ammonimento in questa chat:</b>\n"


# Not async
def warn(
        user: User, chat: Chat, reason: str, message: Message, warner: User = None
) -> str:
    if is_user_admin(chat, user.id):
        message.reply_text("Gli amministratori non possono essere ammuniti.")
        return ""

    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Filtro di ammonimento automatico."

    limit, soft_warn = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # kick
            chat.unban_member(user.id)
            reply = "{} ammonimenti, {} è stato cacciato.".format(
                limit, mention_html(user.id, user.first_name)
            )

        else:  # ban
            chat.kick_member(user.id)
            reply = "{} ammonimenti, {} è stato bandito.".format(
                limit, mention_html(user.id, user.first_name)
            )

        for warn_reason in reasons:
            reply += "\n - {}".format(html.escape(warn_reason))

        message.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        keyboard = []
        log_reason = (
            "<b>{}:</b>"
            "\n#WARN_BAN"
            "\n<b>Admin:</b> {}"
            "\n<b>Utente:</b> {} (<code>{}</code>)"
            "\n<b>Ragione:</b> {}"
            "\n<b>Conteggio:</b> <code>{}/{}</code>".format(
                html.escape(chat.title),
                warner_tag,
                mention_html(user.id, user.first_name),
                user.id,
                reason,
                num_warns,
                limit,
            )
        )

    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Rimuovere ammonimento",
                        callback_data="rm_warn({})".format(user.id),
                    )
                ]
            ]
        )

        reply = "{} ha {}/{} ammonimenti... Per favore attieniti al Codice di Condotta e ricordati di rispettare sempre gli altri utenti.".format(
            mention_html(user.id, user.first_name), num_warns, limit
        )
        if reason:
            reply += "\nRagione dell'ultimo ammonimento:\n{}".format(
                html.escape(reason)
            )

        log_reason = (
            "<b>{}:</b>"
            "\n#WARN"
            "\n<b>Admin:</b> {}"
            "\n<b>Utente:</b> {} (<code>{}</code>)"
            "\n<b>Ragione:</b> {}"
            "\n<b>Conteggio:</b> <code>{}/{}</code>".format(
                html.escape(chat.title),
                warner_tag,
                mention_html(user.id, user.first_name),
                user.id,
                reason,
                num_warns,
                limit,
            )
        )

    try:
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(
                reply, reply_markup=keyboard, parse_mode=ParseMode.HTML, quote=False
            )
        else:
            raise
    return log_reason


@run_async
@user_admin_no_reply
@bot_admin
@loggable
def button(bot: Bot, update: Update) -> str:
    query = update.callback_query  # type: Optional[CallbackQuery]
    user = update.effective_user  # type: Optional[User]
    match = re.match(r"rm_warn\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat = update.effective_chat  # type: Optional[Chat]
        res = sql.remove_warn(user_id, chat.id)
        if res:
            update.effective_message.edit_text(
                "Ammonimento rimosso da {}.".format(
                    mention_html(user.id, user.first_name)
                ),
                parse_mode=ParseMode.HTML,
            )
            user_member = chat.get_member(user_id)
            return (
                "<b>{}:</b>"
                "\n#UNWARN"
                "\n<b>Admin:</b> {}"
                "\n<b>Utente:</b> {} (<code>{}</code>)".format(
                    html.escape(chat.title),
                    mention_html(user.id, user.first_name),
                    mention_html(user_member.user.id, user_member.user.first_name),
                    user_member.user.id,
                )
            )
        else:
            update.effective_message.edit_text(
                "Utente gia privo di ammonimenti.".format(
                    mention_html(user.id, user.first_name)
                ),
                parse_mode=ParseMode.HTML,
            )

    return ""


@run_async
@user_admin
@can_restrict
@loggable
def warn_user(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    warner = update.effective_user  # type: Optional[User]

    user_id, reason = extract_user_and_text(message, args)

    if user_id:
        if (
                message.reply_to_message
                and message.reply_to_message.from_user.id == user_id
        ):
            return warn(
                message.reply_to_message.from_user,
                chat,
                reason,
                message.reply_to_message,
                warner,
            )
        else:
            return warn(chat.get_member(user_id).user, chat, reason, message, warner)
    else:
        message.reply_text("Nessun utente è stato designato!")
    return ""


@run_async
@user_admin
@bot_admin
@loggable
def reset_warns(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    user_id = extract_user(message, args)

    if user_id:
        sql.reset_warns(user_id, chat.id)
        message.reply_text("Ammonimenti resettati!")
        warned = chat.get_member(user_id).user
        return (
            "<b>{}:</b>"
            "\n#RESETWARNS"
            "\n<b>Admin:</b> {}"
            "\n<b>Utente:</b> {} (<code>{}</code>)".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                mention_html(warned.id, warned.first_name),
                warned.id,
            )
        )
    else:
        message.reply_text("Nessun utente è stato designato!")
    return ""


@run_async
def warns(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user_id = extract_user(message, args) or update.effective_user.id
    result = sql.get_warns(user_id, chat.id)

    if result and result[0] != 0:
        num_warns, reasons = result
        limit, soft_warn = sql.get_warn_setting(chat.id)

        if reasons:
            text = "Questo utente ha {}/{} ammonimenti, per le seguenti ragioni:".format(
                num_warns, limit
            )
            for reason in reasons:
                text += "\n - {}".format(reason)

            msgs = split_message(text)
            for msg in msgs:
                update.effective_message.reply_text(msg)
        else:
            update.effective_message.reply_text(
                "Questo utente ha {}/{} ammonimenti ma per nessuno di essi è indicata una ragione.".format(
                    num_warns, limit
                )
            )
    else:
        update.effective_message.reply_text(
            "Questo utente non ha ricevuto alcun ammonimento."
        )


# Dispatcher handler stop - do not async
@user_admin
def add_warn_filter(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    args = msg.text.split(
        None, 1
    )  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) >= 2:
        # set trigger -> lower, so as to avoid adding duplicate filters with different cases
        keyword = extracted[0].lower()
        content = extracted[1]

    else:
        return

    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(WARN_HANDLER_GROUP, []):
        if handler.filters == (keyword, chat.id):
            dispatcher.remove_handler(handler, WARN_HANDLER_GROUP)

    sql.add_warn_filter(chat.id, keyword, content)

    update.effective_message.reply_text(
        "Aggiunto filtro di ammonimento per '{}'!".format(keyword)
    )
    raise DispatcherHandlerStop


@user_admin
def remove_warn_filter(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    args = msg.text.split(
        None, 1
    )  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) < 1:
        return

    to_remove = extracted[0]

    chat_filters = sql.get_chat_warn_triggers(chat.id)

    if not chat_filters:
        msg.reply_text("Nessun filtro di ammonimento attivo!")
        return

    for filt in chat_filters:
        if filt == to_remove:
            sql.remove_warn_filter(chat.id, to_remove)
            msg.reply_text("Filtro disattivato per questo termine.")
            raise DispatcherHandlerStop

    msg.reply_text(
        "Questo attualmente non è un filtro di ammonimento - esegui /warnlist per la lista di tutti i filtri attivi."
    )


@run_async
def list_warn_filters(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    all_handlers = sql.get_chat_warn_triggers(chat.id)

    if not all_handlers:
        update.effective_message.reply_text("Nessun filtro di ammonimento attivo!")
        return

    filter_list = CURRENT_WARNING_FILTER_STRING
    for keyword in all_handlers:
        entry = " - {}\n".format(html.escape(keyword))
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(filter_list, parse_mode=ParseMode.HTML)
            filter_list = entry
        else:
            filter_list += entry

    if not filter_list == CURRENT_WARNING_FILTER_STRING:
        update.effective_message.reply_text(filter_list, parse_mode=ParseMode.HTML)


@run_async
@loggable
def reply_filter(bot: Bot, update: Update) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]

    chat_warn_filters = sql.get_chat_warn_triggers(chat.id)
    to_match = extract_text(message)
    if not to_match:
        return ""

    for keyword in chat_warn_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            user = update.effective_user  # type: Optional[User]
            warn_filter = sql.get_warn_filter(chat.id, keyword)
            return warn(user, chat, warn_filter.reply, message)
    return ""


@run_async
@user_admin
@loggable
def set_warn_limit(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    if args:
        if args[0].isdigit():
            if int(args[0]) < 3:
                msg.reply_text("Il limite di ammonimenti minimo è 3!")
            else:
                sql.set_warn_limit(chat.id, int(args[0]))
                msg.reply_text(
                    "Aggiornato il limite di ammonimenti a {}".format(args[0])
                )
                return (
                    "<b>{}:</b>"
                    "\n#SET_WARN_LIMIT"
                    "\n<b>Admin:</b> {}"
                    "\nImpostato il limite di ammonimenti a <code>{}</code>".format(
                        html.escape(chat.title),
                        mention_html(user.id, user.first_name),
                        args[0],
                    )
                )
        else:
            msg.reply_text("Dammi un numero come argomento!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)

        msg.reply_text("Il limite di ammonimenti attuale è {}".format(limit))
    return ""


@run_async
@user_admin
def set_warn_strength(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    if args:
        if args[0].lower() in ("on", "yes"):
            sql.set_warn_strength(chat.id, False)
            msg.reply_text(
                "Troppi ammonimenti comporteranno l'espulsione permanente (ban)."
            )
            return (
                "<b>{}:</b>\n"
                "<b>Admin:</b> {}\n"
                "Ha abilitato gli ammonimenti rigidi. Gli utenti saranno banditi.".format(
                    html.escape(chat.title), mention_html(user.id, user.first_name)
                )
            )

        elif args[0].lower() in ("off", "no"):
            sql.set_warn_strength(chat.id, True)
            msg.reply_text(
                "Troppi ammonimenti comporteranno l'uscita forzata. Gli utenti potranno unirsi nuovamente."
            )
            return (
                "<b>{}:</b>\n"
                "<b>Admin:</b> {}\n"
                "Ha disabilitato gli ammonimenti rigidi. Gli utenti saranno solo momentaneamente rimossi.".format(
                    html.escape(chat.title), mention_html(user.id, user.first_name)
                )
            )

        else:
            msg.reply_text("Capisco solo on/yes/no/off!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)
        if soft_warn:
            msg.reply_text(
                "Gli ammonimenti sono impostati per *rimuovere* (kick) gli utenti quando superano il limite.",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            msg.reply_text(
                "Gli ammonimenti sono impostati per *bandire* (ban) gli utenti quando superano il limite.",
                parse_mode=ParseMode.MARKDOWN,
            )
    return ""


def __stats__():
    return (
        "{} ammonimenti complessivi, in {} chat.\n"
        "{} filtri di ammonimento, in {} chat.".format(
            sql.num_warns(),
            sql.num_warn_chats(),
            sql.num_warn_filters(),
            sql.num_warn_filter_chats(),
        )
    )


def __import_data__(chat_id, data):
    for user_id, count in data.get("warns", {}).items():
        for x in range(int(count)):
            sql.warn_user(user_id, chat_id)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    num_warn_filters = sql.num_warn_chat_filters(chat_id)
    limit, soft_warn = sql.get_warn_setting(chat_id)
    return (
        "Questa chat ha `{}` filtri di ammonimento. Ci vogliono `{}` ammonimenti "
        "prima che l'utente venga *{}*.".format(
            num_warn_filters, limit, "cacciato" if soft_warn else "bandito"
        )
    )


__help__ = """
 - /warns <userhandle>: ritorna il numero e la ragione degli ammonimenti dell'utente.
 - /warnlist: mostra la lista di tutti i filtri attuali

*Solo admin:*
 - /warn <userhandle>: ammonisce un utente. Dopo 3 ammonimenti, l'utente verrà bandito dal gruppo. Può anche essere usato tramite una risposta.
 - /resetwarn <userhandle>: resetta gli ammonimenti per un utente. Può anche essere usato tramite una risposta.
 - /addwarn <keyword> <reply message>: imposta un filtro di ammonimento per una certa parola chiave. Se si vuole che la parola chiave \
sia una frase basta includerla tra virgolette in questo modo: `/addwarn "molto arrabbiato" Questo è un utente arrabbiato`. 
 - /nowarn <keyword>: rimuove il filtro di ammonimento.
 - /warnlimit <num>: imposta il limite di ammonimenti.
 - /strongwarn <on/yes/off/no>: Se impostato su on, superare il limite di ammonimenti comporterà l'espulsione permanente (ban) \
altrimenti l'utente verrà solo buttato fuori.
"""

__mod_name__ = "Warnings"

WARN_HANDLER = CommandHandler("warn", warn_user, pass_args=True, filters=Filters.group)
RESET_WARN_HANDLER = CommandHandler(
    ["resetwarn", "resetwarns"], reset_warns, pass_args=True, filters=Filters.group
)
CALLBACK_QUERY_HANDLER = CallbackQueryHandler(button, pattern=r"rm_warn")
MYWARNS_HANDLER = DisableAbleCommandHandler(
    "warns", warns, pass_args=True, filters=Filters.group
)
ADD_WARN_HANDLER = CommandHandler("addwarn", add_warn_filter, filters=Filters.group)
RM_WARN_HANDLER = CommandHandler(
    ["nowarn", "stopwarn"], remove_warn_filter, filters=Filters.group
)
LIST_WARN_HANDLER = DisableAbleCommandHandler(
    ["warnlist", "warnfilters"], list_warn_filters, filters=Filters.group, admin_ok=True
)
WARN_FILTER_HANDLER = MessageHandler(
    CustomFilters.has_text & Filters.group, reply_filter
)
WARN_LIMIT_HANDLER = CommandHandler(
    "warnlimit", set_warn_limit, pass_args=True, filters=Filters.group
)
WARN_STRENGTH_HANDLER = CommandHandler(
    "strongwarn", set_warn_strength, pass_args=True, filters=Filters.group
)

dispatcher.add_handler(WARN_HANDLER)
dispatcher.add_handler(CALLBACK_QUERY_HANDLER)
dispatcher.add_handler(RESET_WARN_HANDLER)
dispatcher.add_handler(MYWARNS_HANDLER)
dispatcher.add_handler(ADD_WARN_HANDLER)
dispatcher.add_handler(RM_WARN_HANDLER)
dispatcher.add_handler(LIST_WARN_HANDLER)
dispatcher.add_handler(WARN_LIMIT_HANDLER)
dispatcher.add_handler(WARN_STRENGTH_HANDLER)
dispatcher.add_handler(WARN_FILTER_HANDLER, WARN_HANDLER_GROUP)
