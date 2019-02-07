# New chat added -> setup permissions
import threading
import time
from sqlalchemy import Column, String, Boolean, Integer

from tg_bot.modules.sql import SESSION, BASE



class iLikes(BASE):
    __tablename__ = "ilikes"
    chat_id = Column(String(14), primary_key=True)
    msg_id = Column(String(14), nullable=False)
    found = Column(Integer, nullable=False)
    thanks = Column(Integer, nullable=False)
    notfound = Column(Integer, nullable=False)
    timestamp = Column(String(14), nullable=False)

    def __init__(self, chat_id, msg_id):
        self.chat_id = str(chat_id)
        self.msg_id = str(msg_id)

        self.found = 0
        self.thanks = 0
        self.notfound = 0
        self.timestamp = str(time.time())

    def __repr__(self):
        return "<iLikes for %s>" % self.chat_id



class iLikes_Clicks(BASE):
    __tablename__ = "ilikes_clicks"
    ilikes_id = Column(String(14), primary_key=True)
    user_id = Column(String(14), nullable=False)
    found = Column(Integer, nullable=False)
    thanks = Column(Integer, nullable=False)
    notfound = Column(Integer, nullable=False)

    def __init__(self, ilikes_id, user_id, found, thanks, notfound):
        self.ilikes_id = str(ilikes_id)
        self.user_id = str(user_id)

        self.found = str(found)
        self.thanks = str(thanks)
        self.notfound = str(notfound)

    def __repr__(self):
        return "<iLikes Clicks for %s>" % self.chat_id




iLikes.__table__.create(checkfirst=True)
iLikes_Clicks.__table__.create(checkfirst=True)



PERM_LOCK = threading.RLock()
RESTR_LOCK = threading.RLock()

INSERTION_LOCK = threading.RLock()



def add_iLike(chat_id, msg_id):
    with INSERTION_LOCK:
        ilikes_id = SESSION.query(iLikes).filter(iLikes.chat_id == str(chat_id),
	                                             iLikes.msg_id == str(msg_id),).all()
        if not ilikes_id:
            ilikes_id = iLikes(chat_id, msg_id)
            SESSION.add(ilikes_id)
            SESSION.commit()
            return True
        else:
            return False



