import threading

from sqlalchemy import func, distinct, Column, String, UnicodeText

from tg_bot.modules.sql import SESSION, BASE


class BlackListFilters(BASE):
    __tablename__ = "blacklist"
    chat_id = Column(String(14), primary_key=True)
    trigger = Column(UnicodeText, primary_key=True, nullable=False)

    def __init__(self, chat_id, trigger):
        self.chat_id = str(chat_id)  # ensure string
        self.trigger = trigger

    def __repr__(self):
        return "<Permissions for %s>" % self.chat_id

    def __eq__(self, other):
        return bool(isinstance(other, BlackListFilters)
                    and self.chat_id == other.chat_id
                    and self.trigger == other.trigger)


BlackListFilters.__table__.create(checkfirst=True)

BLACKLIST_FILTER_INSERTION_LOCK = threading.RLock()


def add_to_blacklist(chat_id, trigger):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        blacklist_filt = BlackListFilters(str(chat_id), trigger)

        SESSION.merge(blacklist_filt)  # merge to avoid duplicate key issues
        SESSION.commit()


def rm_from_blacklist(chat_id, trigger):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        blacklist_filt = SESSION.query(BlackListFilters).get((str(chat_id), trigger))
        if blacklist_filt:
            SESSION.delete(blacklist_filt)
            SESSION.commit()
            return True
        SESSION.close()
        return False


def get_chat_blacklist(chat_id):
    try:
        return SESSION.query(BlackListFilters).filter(BlackListFilters.chat_id == str(chat_id)).all()
    finally:
        SESSION.close()


def num_blacklist_filters():
    try:
        return SESSION.query(BlackListFilters).count()
    finally:
        SESSION.close()


def num_blacklist_chat_filters(chat_id):
    try:
        return SESSION.query(BlackListFilters.chat_id).filter(BlackListFilters.chat_id == str(chat_id)).count()
    finally:
        SESSION.close()


def num_blacklist_filter_chats():
    try:
        return SESSION.query(func.count(distinct(BlackListFilters.chat_id))).scalar()
    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        chat_filters = SESSION.query(BlackListFilters).filter(BlackListFilters.chat_id == str(old_chat_id)).all()
        for filt in chat_filters:
            filt.chat_id = str(new_chat_id)
        SESSION.commit()
