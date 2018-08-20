from PyLyrics import *
from telegram import Update, Bot
from telegram.ext import run_async

from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot import dispatcher

from requests import get

LYRICSINFO = "\n[Full Lyrics](http://lyrics.wikia.com/wiki/%s:%s)"

@run_async
def lyrics(Bot, update: Update, user, args):
    message = update.effective_message
    text = message.text[len('/lyrics '):]
    song = " ".join(args).split("- ")
    reply_text = f'Looks up for lyrics'
    
    if len(song) == 2:
        while song[1].startswith(" "):
            song[1] = song[1][1:]
        while song[0].startswith(" "):
            song[0] = song[0][1:]
        while song[1].endswith(" "):
            song[1] = song[1][:-1]
        while song[0].endswith(" "):
            song[0] = song[0][:-1]
        try:
            lyrics = "\n".join(PyLyrics.getLyrics(
                song[0], song[1]).split("\n")[:20])
        except ValueError as e:
            return core.message("❌ Song %s not found :(" % song[1], failed=True)
        else:
            lyricstext = LYRICSINFO % (song[0].replace(
                " ", "_"), song[1].replace(" ", "_"))
            return core.message(lyrics + lyricstext, parse_mode="MARKDOWN")
    else:
        return core.message("Invalid syntax!", failed=True)


__help__ = """
 - /lyrics <keyword> Find your favourite songs' lyrics
"""

__mod_name__ = "Lyrics"

lyrics_handle = DisableAbleCommandHandler("lyrics", lyrics)

dispatcher.add_handler(lyrics_handle)