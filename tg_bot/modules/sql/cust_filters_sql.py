import threading

from sqlalchemy import Column, String, UnicodeText, Boolean

from tg_bot.modules.sql import BASE, SESSION


class CustomFilters(BASE):
    __tablename__ = "cust_filters"
    chat_id = Column(String(14), primary_key=True)
    keyword = Column(UnicodeText, primary_key=True, nullable=False)
    reply = Column(UnicodeText, nullable=False)
    is_sticker = Column(Boolean, nullable=False, default=False)

    def __init__(self, chat_id, keyword, reply, is_sticker=False):
        self.chat_id = str(chat_id)  # ensure string
        self.keyword = keyword
        self.reply = reply
        self.is_sticker = is_sticker

    def __repr__(self):
        return "<Permissions for %s>" % self.chat_id


CustomFilters.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.Lock()


def get_all_filters():
    return SESSION.query(CustomFilters).all()


def add_filter(chat_id, keyword, reply, is_sticker=False):
    with INSERTION_LOCK:
        res = CustomFilters(chat_id, keyword, reply, is_sticker)
        SESSION.merge(res)  # merge to avoid duplicate key issues
        SESSION.commit()


def remove_filter(chat_id, keyword):
    with INSERTION_LOCK:
        res = SESSION.query(CustomFilters).get((str(chat_id), keyword))
        if res:
            SESSION.delete(res)
            SESSION.commit()


def get_chat_filters(chat_id):
    return SESSION.query(CustomFilters).filter(CustomFilters.chat_id == str(chat_id)).all()
