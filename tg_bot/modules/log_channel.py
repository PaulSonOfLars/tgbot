from functools import wraps
from typing import Optional

from tg_bot.modules.helper_funcs.misc import is_module_loaded

FILENAME = __name__.rsplit(".", 1)[-1]

if is_module_loaded(FILENAME):
    from telegram import Bot, Update, ParseMode, Message, Chat, MessageEntity
    from telegram.error import BadRequest, Unauthorized
    from telegram.ext import CommandHandler, MessageHandler, run_async
    from telegram.utils.helpers import escape_markdown
    from telegram.ext import Filters

    from tg_bot import dispatcher, LOGGER
    from tg_bot.modules.helper_funcs.chat_status import user_admin
    from tg_bot.modules.sql import log_channel_sql as sql
    import requests
    import tldextract


    def loggable(func):
        @wraps(func)
        def log_action(bot: Bot, update: Update, *args, **kwargs):
            result = func(bot, update, *args, **kwargs)
            chat = update.effective_chat  # type: Optional[Chat]
            message = update.effective_message  # type: Optional[Message]
            if result:
                if chat.type == chat.SUPERGROUP and chat.username:
                    result += (
                        "\n<b>Link:</b> "
                        '<a href="http://telegram.me/{}/{}">Fai click qui</a>'.format(
                            chat.username, message.message_id
                        )
                    )
                log_chat = sql.get_chat_log_channel(chat.id)
                if log_chat:
                    send_log(bot, log_chat, chat.id, result)
            elif result == "":
                pass
            else:
                LOGGER.warning(
                    "%s è stato impostato come loggable, ma non ha nessun return abilitato.",
                    func,
                )

            return result

        return log_action


    @run_async
    def log_resource(bot: Bot, update: Update):
        entities = update.effective_message.parse_entities()
        caption_entities = update.effective_message.parse_caption_entities()
        LOGGER.info(entities)
        chat = update.effective_chat  # type: Optional[Chat]
        log_chat = sql.get_chat_log_channel(chat.id)

        url = None
        tags = []

        if log_chat:
            for descriptor, entity in entities.items():
                if descriptor["type"] == MessageEntity.HASHTAG:
                    tags.append(entity)
            if tags:
                tags.sort()

            log_entities_list(bot, chat, entities, log_chat, tags, update)

            log_entities_list(bot, chat, caption_entities, log_chat, tags, update)


    def log_entities_list(bot, chat, entities, log_chat, tags, update):
        for descriptor, entity in entities.items():
            result = (
                f"<b>Risorsa inviata da @{update.effective_user.username}:</b>\n"
            )

            to_manage = None
            if descriptor["type"] == MessageEntity.URL:
                to_manage = entity
            elif descriptor["type"] == MessageEntity.TEXT_LINK:
                to_manage = descriptor['url']
            log_for_entity(bot, chat, to_manage, log_chat, result, tags)


    def log_for_entity(bot, chat, entity, log_chat, result, tags):
        try:
            response = requests.get(entity)
            if response.status_code == requests.codes.ok:
                result += f'{entity}'
                extracted = tldextract.extract(entity)
                if f"#{extracted.domain}" not in tags:
                    tags.append(f"#{extracted.domain}")
                    tags.sort()
                if tags:
                    tags_string = " ".join(tags)
                    result += f"\n\nTags:\n{tags_string}"
                send_log(bot, log_chat, chat.id, result)
        except Exception as e:
            LOGGER.info(f"Resource {entity} is not a valid url")
            LOGGER.error(e)


    def send_log(bot: Bot, log_chat_id: str, orig_chat_id: str, result: str):
        try:
            bot.send_message(log_chat_id, result, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            if excp.message == "Chat not found":
                bot.send_message(
                    orig_chat_id,
                    "Questo logchannel è stato cancellato - disattivamento.",
                )
                sql.stop_chat_logging(orig_chat_id)
            else:
                LOGGER.warning(excp.message)
                LOGGER.warning(result)
                LOGGER.exception("Could not parse")

                bot.send_message(
                    log_chat_id,
                    result
                    + "\n\nFormattazione disattivata a causa di un errore sconosciuto.",
                )


    @run_async
    @user_admin
    def logging(bot: Bot, update: Update):
        message = update.effective_message  # type: Optional[Message]
        chat = update.effective_chat  # type: Optional[Chat]

        log_channel = sql.get_chat_log_channel(chat.id)
        if log_channel:
            log_channel_info = bot.get_chat(log_channel)
            message.reply_text(
                "Questo gruppo ha impostato questo canale come log-channel: {} (`{}`)".format(
                    escape_markdown(log_channel_info.title), log_channel
                ),
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            message.reply_text("Nessun log-channel è stato impostato per questo gruppo")


    @run_async
    @user_admin
    def setlog(bot: Bot, update: Update):
        message = update.effective_message  # type: Optional[Message]
        chat = update.effective_chat  # type: Optional[Chat]
        if chat.type == chat.CHANNEL:
            message.reply_text(
                "Ora, inoltra il /setlog al gruppo che vuoi collegare a questo canale."
            )

        elif message.forward_from_chat:
            sql.set_chat_log_channel(chat.id, message.forward_from_chat.id)
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message == "Message to delete not found":
                    pass
                else:
                    LOGGER.exception(
                        "Error deleting message in log channel. Should work anyway though."
                    )

            try:
                bot.send_message(
                    message.forward_from_chat.id,
                    "Il log-channel di questo gruppo è impostato a: {}.".format(
                        chat.title or chat.first_name
                    ),
                )
            except Unauthorized as excp:
                if excp.message == "Forbidden: bot is not a member of the channel chat":
                    bot.send_message(chat.id, "log-channel impostato correttamente!")
                else:
                    LOGGER.exception("ERROR in setting the log channel.")

            bot.send_message(chat.id, "log-channel impostato correttamente!")

        else:
            message.reply_text(
                "Segui i seguenti passi per creare il log-channel:\n"
                " - aggiungi il bot al canale di log\n"
                " - invia /setlog nel canale\n"
                " - inoltra /setlog al gruppo che vuoi loggare\n"
            )


    @run_async
    @user_admin
    def unsetlog(bot: Bot, update: Update):
        message = update.effective_message  # type: Optional[Message]
        chat = update.effective_chat  # type: Optional[Chat]

        log_channel = sql.stop_chat_logging(chat.id)
        if log_channel:
            bot.send_message(
                log_channel, "Questo canale è stato scollegato da {}".format(chat.title)
            )
            message.reply_text("Log channel è stato disattivato.")

        else:
            message.reply_text("Nessun log-channel è stato ancora collegato!")


    def __stats__():
        return "{} log-channel impostato.".format(sql.num_logchannels())


    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)


    def __chat_settings__(chat_id, user_id):
        log_channel = sql.get_chat_log_channel(chat_id)
        if log_channel:
            log_channel_info = dispatcher.bot.get_chat(log_channel)
            return "Questo gruppo è loggato qui: {} (`{}`)".format(
                escape_markdown(log_channel_info.title), log_channel
            )
        return "Nessun log-channel è stato impostato per il gruppo!"


    __help__ = """
*Admin only:*
- /logchannel: get log channel info
- /setlog: set the log channel.
- /unsetlog: unset the log channel.

Setting the log channel is done by:
- adding the bot to the desired channel (as an admin!)
- sending /setlog in the channel
- forwarding the /setlog to the group
"""

    __mod_name__ = "Log Channels"

    LOG_HANDLER = CommandHandler("logchannel", logging)
    SET_LOG_HANDLER = CommandHandler("setlog", setlog)
    UNSET_LOG_HANDLER = CommandHandler("unsetlog", unsetlog)

    LOG_RESOURCES_HANDLER = MessageHandler(
        (
                Filters.entity("url")
                | Filters.entity("text_link")
                | Filters.entity("hashtag")
        ),
        log_resource,
    )

    dispatcher.add_handler(LOG_HANDLER)
    dispatcher.add_handler(SET_LOG_HANDLER)
    dispatcher.add_handler(UNSET_LOG_HANDLER)
    dispatcher.add_handler(LOG_RESOURCES_HANDLER)

else:
    # run anyway if module not loaded
    def loggable(func):
        return func
