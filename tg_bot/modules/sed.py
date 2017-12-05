import re

import telegram
from telegram.ext import RegexHandler, run_async

from tg_bot import dispatcher

DELIMITERS = ("/", ":", "|", "_")


def separate_sed(s):
    if len(s) > 4 and s[1] in DELIMITERS and s.count(s[1]) >= 3:
        delim = s[1]
        start = counter = 2
        while counter < len(s):
            if s[counter] == "\\":
                counter += 1

            elif s[counter] == delim:
                replace = s[start:counter]
                counter += 1
                start = counter
                break
            counter += 1

        else:
            return None

        while counter-1 < len(s):
            if s[counter] == "\\" and s[counter+1] == delim:
                s = s[:counter] + s[counter + 1:]

            elif s[counter] == delim:
                replace_with = s[start:counter]
                counter += 1
                break

            counter += 1
        else:
            return None

        flags = ""
        if counter < len(s):
            flags = s[counter:]
        return replace, replace_with, flags


@run_async
def sed(bot, update):
    r = separate_sed(update.effective_message.text)
    if r and update.effective_message.reply_to_message:
        r, rw, f = r
        if "I" in f or "i" in f:
            t = re.sub(r, rw, update.effective_message.reply_to_message.text, flags=re.I).strip()
        else:
            t = re.sub(r, rw, update.effective_message.reply_to_message.text).strip()

        # empty string errors -_-
        if len(t) >= telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text("The result of the sed command was too long for \
                                                 telegram!")
        elif t:
            update.effective_message.reply_to_message.reply_text(t)


__help__ = """
 - s/<text1>/<text2>/<flag>: Reply to a message with this to perform a sed operation on that message, replacing all \
occurrences of 'text1' with 'text2'. Flags are optional, and currently include 'i' for ignore case, or nothing. \
Delimiters include '/', '_' and ':'. Text grouping is supported. The resulting message cannot be larger than \
{}
""".format(telegram.MAX_MESSAGE_LENGTH)

SED_HANDLER = RegexHandler(r's([{}]).*?\1.*?\1'.format("".join(DELIMITERS)), sed)

dispatcher.add_handler(SED_HANDLER)
