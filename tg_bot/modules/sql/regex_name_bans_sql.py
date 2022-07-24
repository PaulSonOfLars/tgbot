import threading

from sqlalchemy import Column, BigInteger, UnicodeText

from tg_bot.modules.sql import SESSION, BASE


class RegexNameBan(BASE):
    __tablename__ = "name_regex_ban"
    id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger)
    regex_to_ban = Column(UnicodeText)

    def __init__(self, chat_id, regex_to_ban):
        self.chat_id = chat_id
        self.regex_to_ban = regex_to_ban

    def __repr__(self):
        return "<Ban regex %s> " % self.regex_to_ban,

class RegexNameGlobalBan(BASE):
    __tablename__ = "global_name_regex_ban"
    id = Column(BigInteger, primary_key=True)
    regex_to_ban = Column(UnicodeText)

    def __init__(self, regex_to_ban):
        self.regex_to_ban = regex_to_ban

    def __repr__(self):
        return "<Name global regex ban regex_to_ban %s>" % self.regex_to_ban


RegexNameBan.__table__.create(checkfirst=True)
RegexNameGlobalBan.__table__.create(checkfirst=True)

REGEX_BAN_INSERTION_LOCK = threading.RLock()
REGEX_GLOBAL_BAN_INSERTION_LOCK = threading.RLock()


def add_regex_bans(chat_id, regex_to_ban):
    with REGEX_BAN_INSERTION_LOCK:
        regex_bans = RegexNameBan(chat_id, regex_to_ban)
        SESSION.merge(regex_bans)
        SESSION.commit()


def get_regex_bans(chat_id):
    regex_bans = SESSION.query(RegexNameBan).filter(RegexNameBan.chat_id == chat_id).all()
    SESSION.close()
    if regex_bans:
        return regex_bans
    return []


def is_regex_ban_exists(chat_id, regex_to_ban):
    is_exists = SESSION.query(RegexNameBan).filter(RegexNameBan.chat_id == chat_id,
                                                 RegexNameBan.regex_to_ban == regex_to_ban).first() is not None
    SESSION.close()
    return is_exists


def delete_regex_ban(chat_id, regex_to_ban):
    with REGEX_BAN_INSERTION_LOCK:
        regex_ban = SESSION.query(RegexNameBan).filter(RegexNameBan.chat_id == chat_id, 
                                                       RegexNameBan.regex_to_ban == regex_to_ban).first()
        if regex_ban:
            SESSION.delete(regex_ban)
            SESSION.commit()
            return True
        SESSION.close()
    return False


def add_regex_global_bans(regex_to_ban):
    with REGEX_GLOBAL_BAN_INSERTION_LOCK:
        regex_bans = RegexNameGlobalBan(regex_to_ban)
        SESSION.merge(regex_bans)
        SESSION.commit()


def get_regex_global_bans():
    regex_global_bans = SESSION.query(RegexNameGlobalBan).all()
    SESSION.close()
    if regex_global_bans:
        return regex_global_bans
    return []


# def is_global_regex_ban_exists(regex_global_ban):
#     is_exists = SESSION.query(RegexNameGlobalBan).filter(RegexNameGlobalBan.regex_to_ban == regex_global_ban).first() is not None
#     SESSION.close()
#     return is_exists


def delete_regex_global_ban(regex_global_ban):
    with REGEX_GLOBAL_BAN_INSERTION_LOCK:
        regex_global_ban = SESSION.query(RegexNameGlobalBan).filter(RegexNameGlobalBan.regex_to_ban == regex_global_ban).first()
        if regex_global_ban:
            SESSION.delete(regex_global_ban)
            SESSION.commit()
            return True
        SESSION.close()
    return False


def migrate_chat(old_chat_id, new_chat_id):
    with REGEX_BAN_INSERTION_LOCK:
        regex_bans = SESSION.query(RegexNameBan).filter(RegexNameBan.chat_id == old_chat_id)
        for regex_ban in regex_bans:
            regex_ban.chat_id = str(new_chat_id)
        SESSION.commit()
