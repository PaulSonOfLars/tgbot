from functools import wraps
from typing import Optional

from tg_bot.modules.helper_funcs.misc import is_module_loaded

FILENAME = __name__.rsplit(".", 1)[-1]

if is_module_loaded(FILENAME):
    from telegram import Bot, Update, ParseMode, Message, Chat
    from telegram.error import BadRequest
    from telegram.ext import CommandHandler, run_async
    from telegram.utils.helpers import escape_markdown

    from tg_bot import dispatcher, LOGGER
    from tg_bot.modules.helper_funcs.chat_status import user_admin
    from tg_bot.modules.sql import log_channel_sql as sql


    def loggable(func):
        @wraps(func)
        def log_action(bot: Bot, update: Update, *args, **kwargs):
            result = func(bot, update, *args, **kwargs)

            if result:
                log_chat = sql.get_chat_log_group(update.effective_chat.id)
                if log_chat:
                    send_log(bot, log_chat, result)
            elif result == "":
                pass
            else:
                LOGGER.warning("%s was set as loggable, but had no return statement.", func)

            return result

        return log_action


    def send_log(bot: Bot, log_chat: str, result: str):
        try:
            bot.send_message(log_chat, result, parse_mode=ParseMode.MARKDOWN)
        except BadRequest as excp:
            LOGGER.warning(excp.message)
            LOGGER.warning(result)
            LOGGER.exception("Could not parse")

            bot.send_message(log_chat, result + "\n\nMarkdown disabled due to error.")


    @run_async
    @user_admin
    def logging(bot: Bot, update: Update):
        message = update.effective_message  # type: Optional[Message]
        chat = update.effective_chat  # type: Optional[Chat]

        log_channel = sql.get_chat_log_group(chat.id)
        if log_channel:
            log_channel_info = bot.get_chat(log_channel)
            message.reply_text(
                "This group has all it's logs sent to: {} (`{}`)".format(escape_markdown(log_channel_info.title),
                                                                         log_channel),
                parse_mode=ParseMode.MARKDOWN)

        else:
            message.reply_text("No log channel has been set for this group!")


    @run_async
    @user_admin
    def setlog(bot: Bot, update: Update):
        message = update.effective_message  # type: Optional[Message]
        chat = update.effective_chat  # type: Optional[Chat]
        if chat.type == chat.CHANNEL:
            message.reply_text("Now, forward the /setlog to the group you want to tie this channel to!")

        elif message.forward_from_chat:
            sql.set_chat_log_channel(chat.id, message.forward_from_chat.id)
            bot.send_message(message.forward_from_chat.id,
                             "This channel has been set as the log channel for {}.".format(
                                 chat.title or chat.first_name))
            message.delete()
            bot.send_message(chat.id, "Successfully set log channel!")

        else:
            message.reply_text("The steps to set a log channel are:\n"
                               " - add bot to the desired channel\n"
                               " - send /setlog to the channel\n"
                               " - forward the /setlog to the group\n")


    @run_async
    @user_admin
    def unsetlog(bot: Bot, update: Update):
        message = update.effective_message  # type: Optional[Message]
        chat = update.effective_chat  # type: Optional[Chat]

        log_channel = sql.stop_chat_logging(chat.id)
        if log_channel:
            bot.send_message(log_channel, "Channel has been unlinked from {}".format(chat.title))
            message.reply_text("Log channel has been un-set.")

        else:
            message.reply_text("No log channel has been set yet!")


    def __stats__():
        return "{} log channels set.".format(sql.num_logchannels())


    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)


    def __chat_settings__(chat_id, user_id):
        log_channel = sql.get_chat_log_group(chat_id)
        if log_channel:
            log_channel_info = dispatcher.bot.get_chat(log_channel)
            return "This group has all it's logs sent to: {} (`{}`)".format(escape_markdown(log_channel_info.title),
                                                                            log_channel)
        return "No log channel is set for this group!"


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

    dispatcher.add_handler(LOG_HANDLER)
    dispatcher.add_handler(SET_LOG_HANDLER)
    dispatcher.add_handler(UNSET_LOG_HANDLER)

else:
    # run anyway if module not loaded
    def loggable(func):
        return func
