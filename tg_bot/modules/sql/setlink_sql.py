import threading

from sqlalchemy import Column, String, UnicodeText, func, distinct

from tg_bot.modules.sql import SESSION, BASE


class Links(BASE):
    __tablename__ = "chat_links"
    chat_id = Column(String(14), primary_key=True)
    chat_links = Column(UnicodeText, default="")

    def __init__(self, chat_id):
        self.chat_id = chat_id

    def __repr__(self):
        return "<Chat {} links: {}>".format(self.chat_id, self.chat_links)


Links.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()


def set_link(chat_id, links_text):
    with INSERTION_LOCK:
        chat_links = SESSION.query(Links).get(str(chat_id))
        if not chat_links:
            chat_links = Links(str(chat_id))
        chat_links.chat_links = links_text

        SESSION.add(chat_links)
        SESSION.commit()


def get_link(chat_id):
    chat_links = SESSION.query(Links).get(str(chat_id))
    ret = ""
    if chat_links:
        ret = chat_links.chat_links

    SESSION.close()
    return ret


def num_chats():
    try:
        return SESSION.query(func.count(distinct(Links.chat_id))).scalar()
    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat = SESSION.query(Links).get(str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)
        SESSION.commit()
