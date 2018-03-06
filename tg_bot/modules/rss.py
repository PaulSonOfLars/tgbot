import html

from telegram import ParseMode, constants
from telegram.ext import CommandHandler

from tg_bot import dispatcher, SUDO_USERS, updater
from tg_bot.modules.sql import rss_sql as sql
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin

from feedparser import parse


def show_url(bot, update, args):
    tg_chat_id = str(update.effective_chat.id)

    if len(args) >= 1:
        # there is an actual link written

        tg_feed_link = args[0]
        link_processed = parse(tg_feed_link)

        if 'title' in link_processed.feed:
            feed_title = link_processed.feed.title
        else:
            feed_title = "Unknown"

        if 'description' in link_processed.feed:
            feed_description = link_processed.feed.description
        else:
            feed_description = "Unknown"

        if 'link' in link_processed.feed:
            feed_link = link_processed.feed.link
        else:
            feed_link = "Unknown"

        if 'title' in link_processed.entries[0]:
            entry_title = link_processed.entries[0].title
        else:
            entry_title = "Unknown"

        if 'description' in link_processed.entries[0]:
            entry_description = link_processed.entries[0].description
        else:
            entry_description = "Unknown"

        if 'link' in link_processed.entries[0]:
            entry_link = link_processed.entries[0].link
        else:
            entry_link = "Unknown"

        final_message = "feed title: <b>{}</b> " \
                        "\n\nfeed description: {}" \
                        "\n\nfeed link: {}"\
                        "\n\nentry title: <b>{}</b>"\
                        "\n\nentry description: {}"\
                        "\n\nentry link: {}".format(html.escape(feed_title),
                                                    html.escape(feed_description),
                                                    html.escape(feed_link),
                                                    html.escape(entry_title),
                                                    html.escape(entry_description),
                                                    html.escape(entry_link))

        bot.send_message(chat_id=tg_chat_id, text=final_message, parse_mode=ParseMode.HTML)
    else:
        # there's nothing written or it's too less text to be an actual link
        update.effective_message.reply_text("URL missing")


def list_urls(bot, update):
    # gather telegram chat ID (might be the same as user ID if message is sent to the bot via PM)
    tg_chat_id = str(update.effective_chat.id)

    # gather link data from DB based on who sent the message and from where
    user_data = sql.get_urls(tg_chat_id)

    # this loops gets every link from the DB based on the filter above and appends it to the list
    links_list = [row.feed_link for row in user_data]

    # this neatly arranges the links from links_list to be properly sent by the bot
    final_content = "\n\n".join(links_list)

    # check if the length of the message is too long to be posted in 1 chat bubble
    if len(final_content) == 0:
        bot.send_message(chat_id=tg_chat_id, text="This chat is not subscribed to any links")
    elif len(final_content) <= constants.MAX_MESSAGE_LENGTH:
        bot.send_message(chat_id=tg_chat_id, text="This chat is subscribed to the following links\n" + final_content)
    else:
        bot.send_message(chat_id=tg_chat_id, parse_mode=ParseMode.HTML,
                         text="<b>Warning:</b> The message is too long to be sent")


@user_admin
def add_url(bot, update, args):
    # check if there is anything written as argument (will give out of range if there's no argument)
    if len(args) >= 1:
        # gather telegram chat data
        chat = update.effective_chat

        # gather telegram chat ID (might be the same as user ID if message is sent to the bot via PM)
        tg_chat_id = str(update.effective_chat.id)

        # gather the feed link from the command sent by the user
        tg_feed_link = args[0]

        # pass the link to be processed by feedparser
        link_processed = parse(tg_feed_link)

        # check if link is a valid RSS Feed link
        if link_processed.bozo == 1:
            # it's not a valid RSS Feed link
            update.effective_message.reply_text("This link is not an RSS Feed link")
        else:
            # the RSS Feed link is valid

            tg_old_entry_link = link_processed.entries[0].link

            # gather the row which contains exactly that telegram user ID, group ID and link for later comparison
            row = sql.check_url_availability(tg_chat_id, tg_feed_link)

            # check if there's an entry already added to DB by the same user in the same group with the same link
            if row:
                # there is already a link added to the DB
                update.effective_message.reply_text("This URL has already been added")
            else:
                # there is no link added, so we'll add it now

                # prepare the action for the DB push
                sql.add_url(tg_chat_id, tg_feed_link, tg_old_entry_link)

                update.effective_message.reply_text("Added URL to subscription")
    else:
        # there's nothing written or it's too less text to be an actual link
        update.effective_message.reply_text("URL missing")


@user_admin
def remove_url(bot, update, args):
    # check if there is anything written as argument (will give out of range if there's no argument)
    if len(args) >= 1:
        # there is an actual link written

        # gather telegram chat ID (might be the same as user ID if message is sent to the bot via PM)
        tg_chat_id = str(update.effective_chat.id)

        # gather the feed link from the command sent by the user
        tg_feed_link = args[0]

        # pass the link to be processed by feedparser
        link_processed = parse(tg_feed_link)

        # check if link is a valid RSS Feed link
        if link_processed.bozo == 1:
            # it's not a valid RSS Feed link
            update.effective_message.reply_text("This link is not an RSS Feed link")
        else:
            # the RSS Feed link is valid

            # gather all duplicates (if possible) for the same TG User ID, TG Chat ID and link
            user_data = sql.check_url_availability(tg_chat_id, tg_feed_link)

            # check if it finds the link in the database
            if user_data:
                # there is an link in the DB

                sql.remove_url(tg_chat_id, tg_feed_link)

                update.effective_message.reply_text("Removed URL from subscription")
            else:
                update.effective_message.reply_text("You haven't subscribed to this URL yet")
    else:
        # there's nothing written or it's too less text to be an actual link
        update.effective_message.reply_text("URL missing")


def rss_update(bot, job):
    # get all of the DB data
    user_data = sql.get_all()

    # this loop checks for every row in the DB
    for row in user_data:
        # get row ID from DB
        row_id = row.id

        # get telegram chat ID from DB
        tg_chat_id = row.chat_id

        # get RSS link from DB
        tg_feed_link = row.feed_link

        # process the feed from DB
        feed_processed = parse(tg_feed_link)

        # get the last update's entry from the DB
        tg_old_entry_link = row.old_entry_link

        # define empty list of entry links for when there's new updates to a RSS link
        new_entry_links = []

        # define empty list of entry titles for when there's new updates to a RSS link
        new_entry_titles = []

        # this loop checks for every entry from the RSS Feed link from the DB row
        for entry in feed_processed.entries:
            # check if there are any new updates to the RSS Feed from the old entry
            if entry.link != tg_old_entry_link:
                # there is a new entry, so it's link is added to the new_entry_links list for later usage
                new_entry_links.append(entry.link)

                # there is a new entry, so it's title is added to the new_entry_titles list for later usage
                new_entry_titles.append(entry.title)
            else:
                break

        # check if there's any new entries queued from the last check
        if new_entry_links:
            sql.update_url(row_id, new_entry_links)
        else:
            pass

        if len(new_entry_links) < 5:
            # this loop sends every new update to each user from each group based on the DB entries
            for link, title in zip(reversed(new_entry_links), reversed(new_entry_titles)):
                # make the final message with the layout: "<rss_feed_title> <rss_feed_link>"
                final_message = "<b>{}</b>\n\n{}".format(html.escape(title), html.escape(link))

                # check if the length of the message is too long to be posted in 1 chat bubble
                if len(final_message) <= constants.MAX_MESSAGE_LENGTH:
                    bot.send_message(chat_id=tg_chat_id, text=final_message, parse_mode=ParseMode.HTML)
                else:
                    bot.send_message(chat_id=tg_chat_id, text="<b>Warning:</b> The message is too long to be sent",
                                     parse_mode=ParseMode.HTML)
        else:
            for link, title in zip(reversed(new_entry_links[-5:]), reversed(new_entry_titles[-5:])):
                # make the final message with the layout: "<rss_feed_title> <rss_feed_link>"
                final_message = "<b>{}</b>\n\n{}".format(html.escape(title), html.escape(link))

                # check if the length of the message is too long to be posted in 1 chat bubble
                if len(final_message) <= constants.MAX_MESSAGE_LENGTH:
                    bot.send_message(chat_id=tg_chat_id, text=final_message, parse_mode=ParseMode.HTML)
                else:
                    bot.send_message(chat_id=tg_chat_id, text="<b>Warning:</b> The message is too long to be sent",
                                     parse_mode=ParseMode.HTML)

            bot.send_message(chat_id=tg_chat_id, parse_mode=ParseMode.HTML,
                             text="<b>Warning: </b>{} occurrences have been left out to prevent spam"
                             .format(str(len(new_entry_links)-5)))


def rss_set(bot, job):
    # get all of the DB data
    user_data = sql.get_all()

    # this loop checks for every row in the DB
    for row in user_data:
        # get row ID
        row_id = row.id

        # get RSS link from DB
        tg_feed_link = row.feed_link

        # process the feed from DB
        feed_processed = parse(tg_feed_link)

        # get the last update's entry from the DB
        tg_old_entry_link = row.old_entry_link

        # define empty list of entry links for when there's new updates to a RSS link
        new_entry_links = []

        # define empty list of entry titles for when there's new updates to a RSS link
        new_entry_titles = []

        # this loop checks for every entry from the RSS Feed link from the DB row
        for entry in feed_processed.entries:
            # check if there are any new updates to the RSS Feed from the old entry
            if entry.link != tg_old_entry_link:
                # there is a new entry, so it's link is added to the new_entry_links list for later usage
                new_entry_links.append(entry.link)

                # there is a new entry, so it's title is added to the new_entry_titles list for later usage
                new_entry_titles.append(entry.title)
            else:
                pass

        # check if there's any new entries queued from the last check
        if new_entry_links:
            sql.update_url(row_id, new_entry_links)
        else:
            pass


__help__ = """
 - /addrss <link>: add an RSS link to the subscriptions.
 - /removerss <link>: removes the RSS link from the subscriptions.
 - /rss <link>: shows the link's data and the last entry, for testing purposes.
 - /listrss: shows the list of rss feeds that the chat is currently subscribed to.

NOTE: In groups, only admins can add/remove RSS links to the group's subscription
"""

__mod_name__ = "RSS Feed"

job = updater.job_queue

job_rss_set = job.run_once(rss_set, 5)
job_rss_update = job.run_repeating(rss_update, interval=60, first=60)
job_rss_set.enabled = True
job_rss_update.enabled = True

SHOW_URL_HANDLER = CommandHandler("rss", show_url, pass_args=True)
ADD_URL_HANDLER = CommandHandler("addrss", add_url, pass_args=True)
REMOVE_URL_HANDLER = CommandHandler("removerss", remove_url, pass_args=True)
LIST_URLS_HANDLER = CommandHandler("listrss", list_urls)

dispatcher.add_handler(SHOW_URL_HANDLER)
dispatcher.add_handler(ADD_URL_HANDLER)
dispatcher.add_handler(REMOVE_URL_HANDLER)
dispatcher.add_handler(LIST_URLS_HANDLER)
