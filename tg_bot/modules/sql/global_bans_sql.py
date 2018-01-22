import threading

from sqlalchemy import Column, UnicodeText, Integer

from tg_bot.modules.sql import BASE, SESSION


class GloballyBannedUsers(BASE):
    __tablename__ = "gbans"
    user_id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    reason = Column(UnicodeText)

    def __init__(self, user_id, name, reason=None):
        self.user_id = user_id
        self.name = name
        self.reason = reason

    def __repr__(self):
        return "<GBanned User {} ({})>".format(self.name, self.user_id)

    def to_dict(self):
        return {"user_id": self.user_id,
                "name": self.name,
                "reason": self.reason}


GloballyBannedUsers.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()


def gban_user(user_id, name, reason=None):
    with INSERTION_LOCK:
        user = SESSION.query(GloballyBannedUsers).get(user_id)
        if not user:
            user = GloballyBannedUsers(user_id, name, reason)

        SESSION.merge(user)
        SESSION.commit()


def ungban_user(user_id):
    with INSERTION_LOCK:
        user = SESSION.query(GloballyBannedUsers).get(user_id)
        if user:
            SESSION.delete(user)

        SESSION.commit()


def get_gban_list():
    try:
        return [x.to_dict() for x in SESSION.query(GloballyBannedUsers).all()]
    finally:
        SESSION.close()
