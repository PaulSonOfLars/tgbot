import threading

from sqlalchemy import Column, String

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


def set_chat_log_channel(chat_id, log_channel):
    with LOGS_INSERTION_LOCK:
        res = SESSION.query(GroupLogs).get(str(chat_id))
        if res:
            res.log_channel = log_channel
        else:
            res = GroupLogs(chat_id, log_channel)
            SESSION.add(res)

        SESSION.commit()


def get_chat_log_group(chat_id):
    try:
        res = SESSION.query(GroupLogs).get(str(chat_id))
        if res:
            return res.log_channel
        return None
    finally:
        SESSION.close()


def stop_chat_logging(chat_id):
    with LOGS_INSERTION_LOCK:
        res = SESSION.query(GroupLogs).get(str(chat_id))
        if res:
            log_channel = res.log_channel
            SESSION.delete(res)
            SESSION.commit()
            return log_channel
