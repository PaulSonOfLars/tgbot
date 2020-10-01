import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User, ParseMode
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, RegexHandler, run_async, Filters
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.helper_funcs.chat_status import user_not_admin, user_admin
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import reporting_sql as sql

REPORT_GROUP = 5


@run_async
@user_admin
def report_setting(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    if chat.type == chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_user_setting(chat.id, True)
                msg.reply_text(
                    "Reporting acceso! Verrai notificati ogni volta che qualcuno riporta qualcosa."
                )

            elif args[0] in ("no", "off"):
                sql.set_user_setting(chat.id, False)
                msg.reply_text("Reporting spento. Non verrai notificato.")
        else:
            msg.reply_text(
                "Le tue impostazioni attuali per il modulo Reporting sono: `{}`".format(
                    sql.user_should_report(chat.id)
                ),
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_chat_setting(chat.id, True)
                msg.reply_text(
                    "Reporting acceso! Tutti gli admin che hanno abilitato il reporting verranno notificati ogni voltra che un utente usa il comando /reporting "
                    "o @admin"
                )

            elif args[0] in ("no", "off"):
                sql.set_chat_setting(chat.id, False)
                msg.reply_text("Reporting spento. Nessun admin verrà notificato.")
        else:
            msg.reply_text(
                "La chat è attualmente impostata: `{}`".format(
                    sql.chat_should_report(chat.id)
                ),
                parse_mode=ParseMode.MARKDOWN,
            )


@run_async
@user_not_admin
@loggable
def report(bot: Bot, update: Update) -> str:
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    if chat and message.reply_to_message and sql.chat_should_report(chat.id):
        reported_user = message.reply_to_message.from_user  # type: Optional[User]
        chat_name = chat.title or chat.first or chat.username
        admin_list = chat.get_administrators()

        if chat.username and chat.type == Chat.SUPERGROUP:
            msg = (
                "<b>{}:</b>"
                "\n<b>Reported user:</b> {} (<code>{}</code>)"
                "\n<b>Reported by:</b> {} (<code>{}</code>)".format(
                    html.escape(chat.title),
                    mention_html(reported_user.id, reported_user.first_name),
                    reported_user.id,
                    mention_html(user.id, user.first_name),
                    user.id,
                )
            )
            link = (
                "\n<b>Link:</b> "
                '<a href="http://telegram.me/{}/{}">qui</a>'.format(
                    chat.username, message.message_id
                )
            )

            should_forward = False

        else:
            msg = '{} sta chiamando gli admin in "{}"!'.format(
                mention_html(user.id, user.first_name), html.escape(chat_name)
            )
            link = ""
            should_forward = True

        for admin in admin_list:
            if admin.user.is_bot:  # can't message bots
                continue

            if sql.user_should_report(admin.user.id):
                try:
                    bot.send_message(
                        admin.user.id, msg + link, parse_mode=ParseMode.HTML
                    )

                    if should_forward:
                        message.reply_to_message.forward(admin.user.id)

                        if (
                                len(message.text.split()) > 1
                        ):  # If user is giving a reason, send his message too
                            message.forward(admin.user.id)

                except Unauthorized:
                    pass
                except BadRequest as excp:  # TODO: cleanup exceptions
                    LOGGER.exception("Exception while reporting user")
        return msg

    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "Questa chat è configurata per inviare report utente agli amministratori, tramite /report e @admin: `{}`".format(
        sql.chat_should_report(chat_id)
    )


def __user_settings__(user_id):
    return "Riceverei i report per queste chat: `{}`.\nAttiva/disattiva i reports in PM.".format(
        sql.user_should_report(user_id)
    )


__mod_name__ = "Reporting"

__help__ = """
  - /report <reason>: rispondi a un messaggio per segnalarlo agli amministratori.
  - @admin: rispondi a un messaggio per segnalarlo agli amministratori.
NOTA: nessuno di questi verrà attivato se utilizzato dagli amministratori

*Admin only:*
  - /reports <on/off>: modifica l'impostazione del report o visualizza lo stato corrente.
    - Se fatto in pm, alterna il tuo stato.
    - Se in chat, attiva lo stato della chat.
"""

REPORT_HANDLER = CommandHandler("report", report, filters=Filters.group)
SETTING_HANDLER = CommandHandler("reports", report_setting, pass_args=True)
ADMIN_REPORT_HANDLER = RegexHandler("(?i)@admin(s)?", report)

dispatcher.add_handler(REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(ADMIN_REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(SETTING_HANDLER)
