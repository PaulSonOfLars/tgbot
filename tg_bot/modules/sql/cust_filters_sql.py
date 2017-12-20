import collections
import threading

from sqlalchemy import Column, String, UnicodeText, Boolean

from tg_bot.modules.sql import BASE, SESSION


class CustomFilters(BASE):
    __tablename__ = "cust_filters"
    chat_id = Column(String(14), primary_key=True)
    keyword = Column(UnicodeText, primary_key=True, nullable=False)
    reply = Column(UnicodeText, nullable=False)
    is_sticker = Column(Boolean, nullable=False, default=False)
    is_document = Column(Boolean, nullable=False, default=False)

    def __init__(self, chat_id, keyword, reply, is_sticker=False, is_document=False):
        self.chat_id = str(chat_id)  # ensure string
        self.keyword = keyword
        self.reply = reply
        self.is_sticker = is_sticker
        self.is_document = is_document

    def __repr__(self):
        return "<Permissions for %s>" % self.chat_id

    def __eq__(self, other):
        return bool(isinstance(other, CustomFilters)
                    and self.chat_id == other.chat_id
                    and self.keyword == other.keyword)


CustomFilters.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.Lock()

FILTER_KEYSTORE = collections.defaultdict(list)


def get_all_filters():
    return SESSION.query(CustomFilters).all()


def add_filter(chat_id, keyword, reply, is_sticker=False, is_document=False):
    with INSERTION_LOCK:
        filt = CustomFilters(str(chat_id), keyword, reply, is_sticker, is_document)

        if filt in FILTER_KEYSTORE[filt.chat_id]:  # if there already is a filter on that kw, remove it
            FILTER_KEYSTORE[filt.chat_id].remove(filt)

        FILTER_KEYSTORE[filt.chat_id].append(filt)
        SESSION.merge(filt)  # merge to avoid duplicate key issues
        SESSION.commit()


def remove_filter(chat_id, keyword):
    with INSERTION_LOCK:
        filt = SESSION.query(CustomFilters).get((str(chat_id), keyword))
        if filt:
            FILTER_KEYSTORE[filt.chat_id].remove(filt)
            SESSION.delete(filt)
            SESSION.commit()
            return True
        return False


def get_chat_filters(chat_id):
    return FILTER_KEYSTORE[str(chat_id)]


def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat_filters = SESSION.query(CustomFilters).filter(CustomFilters.chat_id == str(old_chat_id)).all()
        for filt in chat_filters:
            filt.chat_id = str(new_chat_id)
        SESSION.commit()


def load_keystore():
    with INSERTION_LOCK:
        all_filters = SESSION.query(CustomFilters).all()
        for filt in all_filters:
            FILTER_KEYSTORE[filt.chat_id].append(filt)
        SESSION.close()
        print("{} total filters added to {} chats.".format(len(all_filters), len(FILTER_KEYSTORE)))


load_keystore()
