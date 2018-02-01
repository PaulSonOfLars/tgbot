import threading

from sqlalchemy import Column, Integer, UnicodeText

from tg_bot.modules.sql import SESSION, BASE


class UserInfo(BASE):
    __tablename__ = "userinfo"
    user_id = Column(Integer, primary_key=True)
    info = Column(UnicodeText)

    def __init__(self, user_id, info):
        self.user_id = user_id
        self.info = info

    def __repr__(self):
        return "<User info %d>" % self.user_id


class UserBio(BASE):
    __tablename__ = "userbio"
    user_id = Column(Integer, primary_key=True)
    bio = Column(UnicodeText)

    def __init__(self, user_id, bio):
        self.user_id = user_id
        self.bio = bio

    def __repr__(self):
        return "<User info %d>" % self.user_id


UserInfo.__table__.create(checkfirst=True)
UserBio.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()


def get_user_me_info(user_id):
    userinfo = SESSION.query(UserInfo).get(user_id)
    SESSION.close()
    if userinfo:
        return userinfo.info
    return None


def set_user_me_info(user_id, info):
    with INSERTION_LOCK:
        userinfo = SESSION.query(UserInfo).get(user_id)
        if userinfo:
            userinfo.info = info
        else:
            userinfo = UserInfo(user_id, info)
        SESSION.add(userinfo)
        SESSION.commit()


def get_user_bio(user_id):
    userbio = SESSION.query(UserBio).get(user_id)
    SESSION.close()
    if userbio:
        return userbio.bio
    return None


def set_user_bio(user_id, bio):
    with INSERTION_LOCK:
        userbio = SESSION.query(UserBio).get(user_id)
        if userbio:
            userbio.bio = bio
        else:
            userbio = UserBio(user_id, bio)

        SESSION.add(userbio)
        SESSION.commit()
