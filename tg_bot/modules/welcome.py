from telegram.ext import MessageHandler, Filters

from tg_bot import dispatcher


def new_member(bot, update):
    new_mem = update.effective_message.new_chat_members
    print(new_mem)
    for member in new_mem:
        update.effective_message.reply_text("My man {}, how are you?".format(member.username))


def left_member(bot, update):
    left_mem = update.effective_message.left_chat_member
    print(left_mem)
    if left_mem:
        update.effective_message.reply_text("Nice knowing ya!")


NEW_MEM_HANDLER = MessageHandler(Filters.status_update.new_chat_members, new_member)
LEFT_MEM_HANDLER = MessageHandler(Filters.status_update.left_chat_member, left_member)

dispatcher.add_handler(NEW_MEM_HANDLER)
dispatcher.add_handler(LEFT_MEM_HANDLER)
