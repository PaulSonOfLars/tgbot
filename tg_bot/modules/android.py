import re
import html
from requests import get
from bs4 import BeautifulSoup
from telegram import Message, Update, Bot, User, Chat, ParseMode, InlineKeyboardMarkup
from telegram.ext import run_async
from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot import dispatcher, updater
from tg_bot.modules.disable import DisableAbleCommandHandler

GITHUB = 'https://github.com'
DEVICES_DATA = 'https://raw.githubusercontent.com/androidtrackers/certified-android-devices/master/devices.json'

@run_async
def magisk(bot, update):
    url = 'https://raw.githubusercontent.com/topjohnwu/magisk_files/'
    releases = ""
    for type, path  in {"Stable":"master/stable", "Beta":"master/beta", "Canary":"canary/release"}.items():
        data = get(url + path + '.json').json()
        releases += f'{type}: [ZIP v{data["magisk"]["version"]}]({data["magisk"]["link"]}) | ' \
                    f'[APP v{data["app"]["version"]}]({data["app"]["link"]}) | ' \
                    f'[Uninstaller]({data["uninstaller"]["link"]})\n'
                        

    update.message.reply_text("*Latest Magisk Releases:*\n{}".format(releases),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

@run_async
def device(bot, update, args):
    if len(args) == 0:
        update.effective_message.reply_text("No codename provided, write a codename for fetching informations.")
        return
    device = " ".join(args)
    found = [
        i for i in get(DEVICES_DATA).json()
        if i["device"] == device or i["model"] == device
    ]
    if found:
        reply = f'Search results for {device}:\n\n'
        for item in found:
            brand = item['brand']
            name = item['name']
            codename = item['device']
            model = item['model']
            reply += f'<b>{brand} {name}</b>\n' \
                f'Model: <code>{model}</code>\n' \
                f'Codename: <code>{codename}</code>\n\n'                
    else:
        reply = f"Couldn't find info about {device}!\n"
    update.message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        
        
def twrp(bot, update, args):
    if len(args) == 0:
        update.effective_message.reply_text("No codename provided, write a codename for fetching informations.")
        return
    device = " ".join(args)
    url = get(f'https://eu.dl.twrp.me/{device}/')
    if url.status_code == 404:
        reply = f"Couldn't find twrp downloads for {device}!\n"
        return
    reply = f'*Latest Official TWRP for {device}*\n'            
    db = get(DEVICES_DATA).json()
    newdevice = device.strip('lte') if device.startswith('beyond') else device
    for dev in db:
        if (dev['device'] == newdevice) or (dev['model'] == newdevice):
            brand = dev['brand']
            name = dev['name']
            reply += f'*{brand} - {name}*\n'
            break
    page = BeautifulSoup(url.content, 'lxml')
    date = page.find("em").text.strip()
    reply += f'*Updated:* {date}\n'
    trs = page.find('table').find_all('tr')
    row = 2 if trs[0].find('a').text.endswith('tar') else 1
    for i in range(row):
        download = trs[i].find('a')
        dl_link = f"https://eu.dl.twrp.me{download['href']}"
        dl_file = download.text
        size = trs[i].find("span", {"class": "filesize"}).text
        reply += f'[{dl_file}]({dl_link}) - {size}\n'

    update.message.reply_text("{}".format(reply),
                               parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

__help__ = """
Android related commands:

 - /magisk - gets the latest magisk release for Stable/Beta/Canary
 - /device <codename> - gets android device basic info from its codename
 - /twrp <codename> -  gets latest twrp for the android device using the codename
 
"""

__mod_name__ = "Android"

MAGISK_HANDLER = DisableAbleCommandHandler("magisk", magisk)
DEVICE_HANDLER = DisableAbleCommandHandler("device", device, pass_args=True)
TWRP_HANDLER = DisableAbleCommandHandler("twrp", twrp, pass_args=True)

dispatcher.add_handler(MAGISK_HANDLER)
dispatcher.add_handler(DEVICE_HANDLER)
dispatcher.add_handler(TWRP_HANDLER)
