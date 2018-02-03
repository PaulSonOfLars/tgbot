import re
import sre_constants

import telegram
from telegram import Update, Bot
from telegram.ext import RegexHandler, run_async

from tg_bot import dispatcher

DELIMITERS = ("/", ":", "|", "_")


def separate_sed(sed_string):
    if len(sed_string) >= 3 and sed_string[1] in DELIMITERS and sed_string.count(sed_string[1]) >= 2:
        delim = sed_string[1]
        start = counter = 2
        while counter < len(sed_string):
            if sed_string[counter] == "\\":
                counter += 1

            elif sed_string[counter] == delim:
                replace = sed_string[start:counter]
                counter += 1
                start = counter
                break

            counter += 1

        else:
            return None

        while counter < len(sed_string):
            if sed_string[counter] == "\\" and counter + 1 < len(sed_string) and sed_string[counter + 1] == delim:
                sed_string = sed_string[:counter] + sed_string[counter + 1:]

            elif sed_string[counter] == delim:
                replace_with = sed_string[start:counter]
                counter += 1
                break

            counter += 1
        else:
            return replace, sed_string[start:], ""

        flags = ""
        if counter < len(sed_string):
            flags = sed_string[counter:]
        return replace, replace_with, flags.lower()


@run_async
def sed(bot: Bot, update: Update):
    sed_result = separate_sed(update.effective_message.text)
    if sed_result and update.effective_message.reply_to_message:
        if update.effective_message.reply_to_message.text:
            to_fix = update.effective_message.reply_to_message.text
        elif update.effective_message.reply_to_message.caption:
            to_fix = update.effective_message.reply_to_message.caption
        else:
            return

        repl, repl_with, flags = sed_result
        try:
            if 'i' in flags and 'g' in flags:
                text = re.sub(repl, repl_with, to_fix, flags=re.I).strip()
            elif 'i' in flags:
                text = re.sub(repl, repl_with, to_fix, count=1, flags=re.I).strip()
            elif 'g' in flags:
                text = re.sub(repl, repl_with, to_fix).strip()
            else:
                text = re.sub(repl, repl_with, to_fix, count=1).strip()
        except sre_constants.error:
            update.effective_message.reply_text("Do you even sed? Apparently not.")
            return

        # empty string errors -_-
        if len(text) >= telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text("The result of the sed command was too long for \
                                                 telegram!")
        elif text:
            update.effective_message.reply_to_message.reply_text(text)


__help__ = """
 - s/<text1>/<text2>(/<flag>): Reply to a message with this to perform a sed operation on that message, replacing all \
occurrences of 'text1' with 'text2'. Flags are optional, and currently include 'i' for ignore case, 'g' for global, \
or nothing. Delimiters include '/', '\_', '|' and ':'. Text grouping is supported. The resulting message cannot be \
larger than {}
""".format(telegram.MAX_MESSAGE_LENGTH)

__name__ = "Sed/Regex"


SED_HANDLER = RegexHandler(r's([{}]).*?\1.*'.format("".join(DELIMITERS)), sed)

dispatcher.add_handler(SED_HANDLER)
