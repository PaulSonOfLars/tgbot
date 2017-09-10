import threading

from sqlalchemy import Column, String, UnicodeText

from tg_bot.modules.sql import BASE, SESSION


class CustomFilters(BASE):
    __tablename__ = "cust_filters"
    chat_id = Column(String(14), primary_key=True)
    keyword = Column(UnicodeText, primary_key=True, nullable=False)
    reply = Column(UnicodeText, nullable=False)

    def __init__(self, chat_id, keyword, reply):
        self.chat_id = str(chat_id)  # ensure string
        self.keyword = keyword
        self.reply = reply

    def __repr__(self):
        return "<Permissions for %s>" % self.chat_id

CustomFilters.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.Lock()


def get_all_filters():
    return SESSION.query(CustomFilters).all()


def add_filter(chat_id, keyword, reply):
    INSERTION_LOCK.acquire()

    res = CustomFilters(chat_id, keyword, reply)
    SESSION.add(res)
    SESSION.commit()
    INSERTION_LOCK.release()


def remove_filter(chat_id, keyword):
    INSERTION_LOCK.acquire()
    res = SESSION.query(CustomFilters).get((str(chat_id), keyword))
    if res:
        SESSION.delete(res)
        SESSION.commit()
    INSERTION_LOCK.release()


def get_chat_filters(chat_id):
    return SESSION.query(CustomFilters).filter(CustomFilters.chat_id == str(chat_id)).all()
