import threading

from sqlalchemy import Column, String, func, distinct

from tg_bot.modules.sql import BASE, SESSION


class GroupLogs(BASE):
    __tablename__ = "log_channels"
    chat_id = Column(String(14), primary_key=True)
    log_channel = Column(String(14), nullable=False)

    def __init__(self, chat_id, log_channel):
        self.chat_id = str(chat_id)
        self.log_channel = str(log_channel)


GroupLogs.__table__.create(checkfirst=True)

LOGS_INSERTION_LOCK = threading.RLock()

CHANNELS = {}


def set_chat_log_channel(chat_id, log_channel):
    with LOGS_INSERTION_LOCK:
        res = SESSION.query(GroupLogs).get(str(chat_id))
        if res:
            res.log_channel = log_channel
        else:
            res = GroupLogs(chat_id, log_channel)
            SESSION.add(res)

        CHANNELS[str(chat_id)] = log_channel
        SESSION.commit()


def get_chat_log_channel(chat_id):
    return CHANNELS.get(str(chat_id))


def stop_chat_logging(chat_id):
    with LOGS_INSERTION_LOCK:
        res = SESSION.query(GroupLogs).get(str(chat_id))
        if res:
            if str(chat_id) in CHANNELS:
                del CHANNELS[str(chat_id)]

            log_channel = res.log_channel
            SESSION.delete(res)
            SESSION.commit()
            return log_channel


def num_logchannels():
    try:
        return SESSION.query(func.count(distinct(GroupLogs.chat_id))).scalar()
    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with LOGS_INSERTION_LOCK:
        chat = SESSION.query(GroupLogs).get(str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)
            SESSION.add(chat)
            if str(old_chat_id) in CHANNELS:
                CHANNELS[str(new_chat_id)] = CHANNELS.get(str(old_chat_id))

        SESSION.commit()


def __load_log_channels():
    global CHANNELS
    try:
        all_chats = SESSION.query(GroupLogs).all()
        CHANNELS = {chat.chat_id: chat.log_channel for chat in all_chats}
    finally:
        SESSION.close()


__load_log_channels()
