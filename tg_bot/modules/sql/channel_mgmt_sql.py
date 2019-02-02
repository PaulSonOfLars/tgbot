import threading

from sqlalchemy import Column, Integer, UnicodeText, String, ForeignKey, UniqueConstraint, func

from tg_bot import dispatcher
from tg_bot.modules.sql import BASE, SESSION

class Channels(BASE):
    __tablename__ = "channels"
    chat_id = Column(String(14), primary_key=True)
    chat_name = Column(UnicodeText, nullable=False)

    def __init__(self, chat_id, chat_name):
        self.chat_id = str(chat_id)
        self.chat_name = chat_name

    def __repr__(self):
        return "<Chat {} ({})>".format(self.chat_name, self.chat_id)


Channels.__table__.create(checkfirst=True)


def add_channel(chat_id, chat_name):
    with INSERTION_LOCK:
        channel_id = SESSION.query(Channels).get(chat_id)
        if not channel_id:
            channel_id = UserInfo(chat_id, chat_name)

        SESSION.add(channel_id)
        SESSION.commit()