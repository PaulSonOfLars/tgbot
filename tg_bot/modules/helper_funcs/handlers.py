import telegram.ext as tg
from telegram import Update


class CustomCommandHandler(tg.CommandHandler):
    def check_update(self, update):
        if (isinstance(update, Update)
                and (update.message or update.edited_message and self.allow_edited)):
            message = update.message or update.edited_message

            if message.text and len(message.text) > 1 and any(message.text.startswith(start) for start in ('/', '!')):
                command = message.text[1:].split(None, 1)[0].split('@')
                command.append(message.bot.username)  # in case the command was send without a username
                if self.filters is None:
                    res = True
                elif isinstance(self.filters, list):
                    res = any(func(message) for func in self.filters)
                else:
                    res = self.filters(message)

                return res and (command[0].lower() in self.command
                                and command[1].lower() == message.bot.username.lower())
            else:
                return False

        else:
            return False


class CustomRegexHandler(tg.RegexHandler):
    def __init__(self, pattern, callback, friendly="", **kwargs):
        super().__init__(pattern, callback, **kwargs)
