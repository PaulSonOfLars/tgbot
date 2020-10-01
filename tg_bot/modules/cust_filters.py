import re
from typing import Optional

import telegram
from telegram import ParseMode, InlineKeyboardMarkup, Message, Chat
from telegram import Update, Bot
from telegram.error import BadRequest
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    DispatcherHandlerStop,
    run_async,
)
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import user_admin
from tg_bot.modules.helper_funcs.extraction import extract_text
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import build_keyboard
from tg_bot.modules.helper_funcs.string_handling import (
    split_quotes,
    button_markdown_parser,
)
from tg_bot.modules.sql import cust_filters_sql as sql

HANDLER_GROUP = 10
BASIC_FILTER_STRING = "*Filtri in questa chat:*\n"


@run_async
def list_handlers(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    all_handlers = sql.get_chat_triggers(chat.id)

    if not all_handlers:
        update.effective_message.reply_text("Nessun filtro attivo!")
        return

    filter_list = BASIC_FILTER_STRING
    for keyword in all_handlers:
        entry = " - {}\n".format(escape_markdown(keyword))
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(
                filter_list, parse_mode=telegram.ParseMode.MARKDOWN
            )
            filter_list = entry
        else:
            filter_list += entry

    if not filter_list == BASIC_FILTER_STRING:
        update.effective_message.reply_text(
            filter_list, parse_mode=telegram.ParseMode.MARKDOWN
        )


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
@user_admin
def filters(bot: Bot, update: Update):
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
    # set trigger -> lower, so as to avoid adding duplicate filters with different cases
    keyword = extracted[0].lower()

    is_sticker = False
    is_document = False
    is_image = False
    is_voice = False
    is_audio = False
    is_video = False
    buttons = []

    # determine what the contents of the filter are - text, image, sticker, etc
    if len(extracted) >= 2:
        offset = len(extracted[1]) - len(
            msg.text
        )  # set correct offset relative to command + notename
        content, buttons = button_markdown_parser(
            extracted[1], entities=msg.parse_entities(), offset=offset
        )
        content = content.strip()
        if not content:
            msg.reply_text(
                "Non c'è un messaggio di nota - Non puoi avere solo bottoni, hai bisogno di accompagnarli con un messaggio!"
            )
            return

    elif msg.reply_to_message and msg.reply_to_message.sticker:
        content = msg.reply_to_message.sticker.file_id
        is_sticker = True

    elif msg.reply_to_message and msg.reply_to_message.document:
        content = msg.reply_to_message.document.file_id
        is_document = True

    elif msg.reply_to_message and msg.reply_to_message.photo:
        content = msg.reply_to_message.photo[-1].file_id  # last elem = best quality
        is_image = True

    elif msg.reply_to_message and msg.reply_to_message.audio:
        content = msg.reply_to_message.audio.file_id
        is_audio = True

    elif msg.reply_to_message and msg.reply_to_message.voice:
        content = msg.reply_to_message.voice.file_id
        is_voice = True

    elif msg.reply_to_message and msg.reply_to_message.video:
        content = msg.reply_to_message.video.file_id
        is_video = True

    else:
        msg.reply_text("Non hai specificato con cosa rispondere!")
        return

    # Add the filter
    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(HANDLER_GROUP, []):
        if handler.filters == (keyword, chat.id):
            dispatcher.remove_handler(handler, HANDLER_GROUP)

    sql.add_filter(
        chat.id,
        keyword,
        content,
        is_sticker,
        is_document,
        is_image,
        is_audio,
        is_voice,
        is_video,
        buttons,
    )

    msg.reply_text("Aggiunto l'handler '{}'!".format(keyword))
    raise DispatcherHandlerStop


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
@user_admin
def stop_filter(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    if len(args) < 2:
        return

    chat_filters = sql.get_chat_triggers(chat.id)

    if not chat_filters:
        update.effective_message.reply_text("Nessun filtro attivo!")
        return

    for keyword in chat_filters:
        if keyword == args[1]:
            sql.remove_filter(chat.id, args[1])
            update.effective_message.reply_text("Sì, smetterò di rispondere a questo.")
            raise DispatcherHandlerStop

    update.effective_message.reply_text(
        "Questo attualmente non è un filtro - esegui /filters per tutti i filtri attivi."
    )


@run_async
def reply_filter(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    to_match = extract_text(message)
    if not to_match:
        return

    chat_filters = sql.get_chat_triggers(chat.id)
    for keyword in chat_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            filt = sql.get_filter(chat.id, keyword)
            if filt.is_sticker:
                message.reply_sticker(filt.reply)
            elif filt.is_document:
                message.reply_document(filt.reply)
            elif filt.is_image:
                message.reply_photo(filt.reply)
            elif filt.is_audio:
                message.reply_audio(filt.reply)
            elif filt.is_voice:
                message.reply_voice(filt.reply)
            elif filt.is_video:
                message.reply_video(filt.reply)
            elif filt.has_markdown:
                buttons = sql.get_buttons(chat.id, filt.keyword)
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                try:
                    message.reply_text(
                        filt.reply,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True,
                        reply_markup=keyboard,
                    )
                except BadRequest as excp:
                    if excp.message == "Unsupported url protocol":
                        message.reply_text(
                            "Sembra che tu stia provando a usare un protocollo url non supportato. "
                            "Telegram non supporta i bottoni con alcuni procolli come per esempio: tg://."
                            "Per favore riprova oppure chiedi aiuto qui: https://t.me/python_ita."
                        )
                    elif excp.message == "Reply message not found":
                        bot.send_message(
                            chat.id,
                            filt.reply,
                            parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=True,
                            reply_markup=keyboard,
                        )
                    else:
                        message.reply_text(
                            "Questa nota non può essere inviata, è formattata in modo scorretto. "
                            "Chiedi su https://t.me/python_ita se non riesci a capire perché."
                        )
                        LOGGER.warning(
                            "Message %s could not be parsed", str(filt.reply)
                        )
                        LOGGER.exception(
                            "Could not parse filter %s in chat %s",
                            str(filt.keyword),
                            str(chat.id),
                        )

            else:
                # LEGACY - all new filters will have has_markdown set to True.
                message.reply_text(filt.reply)
            break


def __stats__():
    return "{} filtri, in {} chat.".format(sql.num_filters(), sql.num_chats())


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    cust_filters = sql.get_chat_triggers(chat_id)
    return "Ci sono `{}` filtri personalizzati.".format(len(cust_filters))


__help__ = """
 - /filters: mostra la lista di tutti i filtri attivi in questa chat.

*Solo admin:*
 - /filter <keyword> <reply message>: aggiunge un filtro a questa chat. Il bot ora risponderà ogni volta che 'keyword'\
viene menzionata. Se si risponde ad uno sticker con una parola chiave, il bot risponderà con quello sticker. NOTE: tutte le \
parole chiave sono in minuscolo. Se si vuole che la parola chiave sia una frase basta usare le virgolette. eg: /filter "hey there" How you \
doin?
 - /stop <filter keyword>: rimuove quel filtro.
"""

__mod_name__ = "Filters"

FILTER_HANDLER = CommandHandler("filter", filters)
STOP_HANDLER = CommandHandler("stop", stop_filter)
LIST_HANDLER = DisableAbleCommandHandler("filters", list_handlers, admin_ok=True)
CUST_FILTER_HANDLER = MessageHandler(CustomFilters.has_text, reply_filter)

dispatcher.add_handler(FILTER_HANDLER)
dispatcher.add_handler(STOP_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(CUST_FILTER_HANDLER, HANDLER_GROUP)
