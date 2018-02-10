from sqlalchemy import Column, String,UnicodeText 
from tg_bot.modules.sql import SESSION, BASE


class Restrict(BASE):
    __tablename__ = "restrict"
    chat_id = Column(String(14), primary_key=True)
    name = Column(UnicodeText, primary_key=True)


Restrict.__table__.create(checkfirst=True)
RESTRICT_INSERTION_LOCK = threading.RLock()

def restrict_to_db(chat_id, restrict_name):
     with RESTRICT_INSERTION_LOCK:
        restricted = SESSION.query(Restrict).get((str(chat_id), restrict_name))
        if restricted:
            SESSION.delete(restricted)
        restriction = Restrict(str(chat_id), restrict_name)

        SESSION.add(restriction)
        SESSION.commit()

def unrestrict_to_db(chat_id, unrestrict_name):
    with RESTRICT_INSERTION_LOCK:
        restrict = SESSION.query(Restrict).get((str(chat_id), unrestrict_name))
        if unrestrict:
            SESSION.delete(unrestrict)
            SESSION.commit()
            return True
        else:
            SESSION.close()
            return False

def check_if_restricted(chat_id, cmd_to_restrict):
    x = SESSION.query(Restrict).get((str(chat_id), cmd_to_restrict))
    try:
        return x
    finally:
        SESSION.close()
