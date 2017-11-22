import re

from telegram.ext import MessageHandler, RegexHandler, run_async

from tg_bot import dispatcher

delims = ("/", ":", "|", "_")


def separate_sed(s):
    if len(s) > 4 and s.startswith(s) and s[1] in delims and s.count(s[1]) >= 3:
        d = s[1]
        start = counter = 2

        while counter < len(s):
            if s[counter] == "\\":
                counter += 1

            elif s[counter] == d:
                replace = s[start:counter]
                counter += 1
                start = counter
                break
            counter += 1

        else:
            return None

        while counter < len(s):
            if s[counter] == "\\":
                counter += 1

            elif s[counter] == d:
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
    if r:
        r, rw, f = r
        if "I" in f or "i" in f:
            t = re.sub(r, rw, update.effective_message.reply_to_message.text, flags=re.I).strip()
        else:
            t = re.sub(r, rw, update.effective_message.reply_to_message.text).strip()

        # empty string errors -_-
        if t:
            update.effective_message.reply_text(t)


SED_HANDLER = RegexHandler('s(/.*?/.*?/|:.*?:.*?:|_.*?_.*?_)', sed)

dispatcher.add_handler(SED_HANDLER)
