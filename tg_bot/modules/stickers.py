import hashlib
import os
import math
import requests
import urllib.request as urllib

from io import BytesIO
from PIL import Image

from typing import Optional, List
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram import TelegramError
from telegram import Update, Bot
from telegram.ext import CommandHandler, run_async
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher

from tg_bot.modules.disable import DisableAbleCommandHandler

@run_async
def stickerid(bot: Bot, update: Update):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        update.effective_message.reply_text("Sticker ID:\n```" +
                                            escape_markdown(msg.reply_to_message.sticker.file_id) + "```",
                                            parse_mode=ParseMode.MARKDOWN)
    else:
        update.effective_message.reply_text("Please reply to a sticker to get its ID.")


@run_async
def getsticker(bot: Bot, update: Update):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    if msg.reply_to_message and msg.reply_to_message.sticker:
        file_id = msg.reply_to_message.sticker.file_id
        newFile = bot.get_file(file_id)
        newFile.download('sticker.png')
        bot.send_document(chat_id, document=open('sticker.png', 'rb'))
        os.remove("sticker.png")
    else:
        update.effective_message.reply_text("Please reply to a sticker for me to upload its PNG.")


@run_async
def kang(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    user = update.effective_user
    hash = hashlib.sha1(bytearray(user.id)).hexdigest()
    packname = "a" + hash[:20] + "_by_"+bot.username
    kangsticker = "kangsticker.png"
    if msg.reply_to_message:
        if msg.reply_to_message.sticker:
            file_id = msg.reply_to_message.sticker.file_id
        elif msg.reply_to_message.photo:
            file_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            file_id = msg.reply_to_message.document.file_id
        kang_file = bot.get_file(file_id)
        kang_file.download('kangsticker.png')
        if args:
            sticker_emoji = str(args[0])
        elif msg.reply_to_message.sticker and msg.reply_to_message.sticker.emoji:
            sticker_emoji = msg.reply_to_message.sticker.emoji
        else:
            sticker_emoji = "🤔"
        try:
            im = Image.open(kangsticker)
            maxsize = (512, 512)
            if (im.width and im.height) < 512:
                size1 = im.width
                size2 = im.height
                if im.width > im.height:
                    scale = 512/size1
                    size1new = 512
                    size2new = size2 * scale
                else:
                    scale = 512/size2
                    size1new = size1 * scale
                    size2new = 512
                size1new = math.floor(size1new)
                size2new = math.floor(size2new)
                sizenew = (size1new, size2new)
                im = im.resize(sizenew)
            else:
                im.thumbnail(maxsize)
            if not msg.reply_to_message.sticker:
                im.save(kangsticker, "PNG")
            bot.add_sticker_to_set(user_id=user.id, name=packname,
                                    png_sticker=open('kangsticker.png', 'rb'), emojis=sticker_emoji)
            msg.reply_text("Sticker successfully added to [pack](t.me/addstickers/%s)" % packname + "\n"
                            "Emoji is:" + " " + sticker_emoji, parse_mode=ParseMode.MARKDOWN)
        except OSError as e:
            msg.reply_text("I can only kang images m8.")
            print(e)
            return
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                makepack_internal(msg, user, open('kangsticker.png', 'rb'), sticker_emoji, bot)
            elif e.message == "Sticker_png_dimensions":
                im.save(kangsticker, "PNG")
                bot.add_sticker_to_set(user_id=user.id, name=packname,
                                        png_sticker=open('kangsticker.png', 'rb'), emojis=sticker_emoji)
                msg.reply_text("Sticker successfully added to [pack](t.me/addstickers/%s)" % packname + "\n"
                            "Emoji is:" + " " + sticker_emoji, parse_mode=ParseMode.MARKDOWN)
            elif e.message == "Invalid sticker emojis":
                msg.reply_text("Invalid emoji(s).")
            elif e.message == "Stickers_too_much":
                msg.reply_text("Max packsize reached. Press F to pay respecc.")
            print(e)
    elif args:
        try:
            try:
                urlemoji = msg.text.split(" ")
                png_sticker = urlemoji[1] 
                sticker_emoji = urlemoji[2]
            except IndexError:
                sticker_emoji = "🤔"
            urllib.urlretrieve(png_sticker, kangsticker)
            im = Image.open(kangsticker)
            maxsize = (512, 512)
            if (im.width and im.height) < 512:
                size1 = im.width
                size2 = im.height
                if im.width > im.height:
                    scale = 512/size1
                    size1new = 512
                    size2new = size2 * scale
                else:
                    scale = 512/size2
                    size1new = size1 * scale
                    size2new = 512
                size1new = math.floor(size1new)
                size2new = math.floor(size2new)
                sizenew = (size1new, size2new)
                im = im.resize(sizenew)
            else:
                im.thumbnail(maxsize)
            im.save(kangsticker, "PNG")
            msg.reply_photo(photo=open('kangsticker.png', 'rb'))
            bot.add_sticker_to_set(user_id=user.id, name=packname,
                                    png_sticker=open('kangsticker.png', 'rb'), emojis=sticker_emoji)
            msg.reply_text("Sticker successfully added to [pack](t.me/addstickers/%s)" % packname + "\n"
                            "Emoji is:" + " " + sticker_emoji, parse_mode=ParseMode.MARKDOWN)
        except OSError as e:
            msg.reply_text("I can only kang images m8.")
            print(e)
            return
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                makepack_internal(msg, user, open('kangsticker.png', 'rb'), sticker_emoji, bot)
            elif e.message == "Sticker_png_dimensions":
                msg.reply_text("Could not resize image to the correct dimensions.")
            elif e.message == "Invalid sticker emojis":
                msg.reply_text("Invalid emoji(s).")
            print(e)
    else:
        msg.reply_text("Please reply to a sticker, or image to kang it!" + "\n"
                        "Oh, by the way. Your pack can be found [here](t.me/addstickers/%s)" % packname, parse_mode=ParseMode.MARKDOWN)
    if os.path.isfile("kangsticker.png"):
        im.close()
        os.remove("kangsticker.png")

def makepack_internal(msg, user, png_sticker, emoji, bot):
    name = user.first_name
    name = name[:50]
    hash = hashlib.sha1(bytearray(user.id)).hexdigest()
    packname = f"a{hash[:20]}_by_{bot.username}"
    try:
        success = bot.create_new_sticker_set(user.id, packname, name + "'s kang pack",
                                             png_sticker=png_sticker,
                                             emojis=emoji)
    except TelegramError as e:
        print(e)
        if e.message == "Sticker set name is already occupied":
            msg.reply_text("Your pack can be found [here](t.me/addstickers/%s)" % packname,
                           parse_mode=ParseMode.MARKDOWN)
        elif e.message == "Peer_id_invalid":
            msg.reply_text("Contact me in PM first.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                text="Start", url=f"t.me/{bot.username}")]]))
        return

    if success:
        msg.reply_text("Sticker pack successfully created. Get it [here](t.me/addstickers/%s)" % packname,
                       parse_mode=ParseMode.MARKDOWN)
    else:
        msg.reply_text("Failed to create sticker pack. Possibly due to blek mejik.")

__help__ = """
- /stickerid: reply to a sticker to me to tell you its file ID.
- /getsticker: reply to a sticker to me to upload its raw PNG file.
- /kang: reply to a sticker to add it to your pack.
"""

__mod_name__ = "Stickers"
STICKERID_HANDLER = DisableAbleCommandHandler("stickerid", stickerid)
GETSTICKER_HANDLER = DisableAbleCommandHandler("getsticker", getsticker)
KANG_HANDLER = DisableAbleCommandHandler("kang", kang, pass_args=True, admin_ok=True)

dispatcher.add_handler(STICKERID_HANDLER)
dispatcher.add_handler(GETSTICKER_HANDLER)
dispatcher.add_handler(KANG_HANDLER)