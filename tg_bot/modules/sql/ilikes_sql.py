# New chat added -> setup permissions
import threading
import time
from sqlalchemy import Column, String, Boolean, Integer

from tg_bot.modules.sql import SESSION, BASE



class iLikes(BASE):
    __tablename__ = "ilikes"
    ilikes_id = Column(String(100), primary_key=True)
    found = Column(Integer, nullable=False)
    thanks = Column(Integer, nullable=False)
    notfound = Column(Integer, nullable=False)
    timestamp = Column(String(50), nullable=False)

    def __init__(self, ilikes_id):
        self.ilikes_id = str(ilikes_id)
        self.found = 0
        self.thanks = 0
        self.notfound = 0
        self.timestamp = str(time.time())

    def __repr__(self):
        return "<iLikes for %s>" % self.chat_id



class iLikes_Clicks(BASE):
    __tablename__ = "ilikes_clicks"
    ilikes_click_id = Column(String(100), primary_key=True)
    found = Column(Integer, nullable=False)
    thanks = Column(Integer, nullable=False)
    notfound = Column(Integer, nullable=False)

    def __init__(self, ilikes_click_id, found, thanks, notfound):
        self.ilikes_click_id = str(ilikes_click_id)
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
        new_ilikes_id = str(chat_id)+str(msg_id)
        ilikes_id = SESSION.query(iLikes).get(str(new_ilikes_id))
        if not ilikes_id:
            ilikes_id = iLikes(new_ilikes_id)
            SESSION.add(ilikes_id)
            SESSION.commit()
            return True
        else:
            return False


def add_iLike_Click(chat_id, msg_id, user_id, key):
    with INSERTION_LOCK:
        new_ilikes_id = str(chat_id)+str(msg_id)+str(user_id)
        ilikes_id = SESSION.query(iLikes_Clicks).get(str(new_ilikes_id))
        state = 1
        if not ilikes_id:
            if ( str(key) == "thanks_key1"):
                ilikes_id = iLikes_Clicks(new_ilikes_id, 1, 0, 0)
            if ( str(key) == "thanks_key2"):
                ilikes_id = iLikes_Clicks(new_ilikes_id, 0, 1, 0)
            if ( str(key) == "thanks_key3"):
                ilikes_id = iLikes_Clicks(new_ilikes_id, 0, 0, 1)
            SESSION.add(ilikes_id)
            SESSION.commit()
            return True
        else:
            old_found = ilikes_id.found
            old_thanks = ilikes_id.thanks
            old_notfound = ilikes_id.notfound

            print(old_found)
            print(old_thanks)
            print(old_notfound)
            print(key)


            if ( str(key) == "thanks_key1"):
                found = 1
                if old_found == 1:
                    found = 0
                ilikes_id = iLikes_Clicks(new_ilikes_id, found, old_thanks, old_notfound)
            if ( str(key) == "thanks_key2"):
                thanks = 1
                if old_thanks == 1:
                    thanks = 0
                ilikes_id = iLikes_Clicks(new_ilikes_id, old_found, thanks, old_notfound)
            if ( str(key) == "thanks_key3"):
                notfound = 1
                if old_notfound == 1:
                    notfound = 0
                ilikes_id = iLikes_Clicks(new_ilikes_id, old_found, old_thanks, notfound)


            return True



