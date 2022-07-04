import threading

from sqlalchemy import Column, BigInteger, UnicodeText

from tg_bot.modules.sql import SESSION, BASE


class ChannelBan(BASE):
    __tablename__ = "channel_ban"
    id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger)
    channel_to_ban = Column(UnicodeText)

    def __init__(self, chat_id, channel_to_ban):
        self.chat_id = chat_id
        self.channel_to_ban = channel_to_ban

    def __repr__(self):
        return "<Channel ban chat_id %d>" % self.chat_id


class ChannelGlobalBan(BASE):
    __tablename__ = "global_channel_ban"
    id = Column(BigInteger, primary_key=True)
    channel_to_ban = Column(UnicodeText)

    def __init__(self, channel_to_ban):
        self.channel_to_ban = channel_to_ban

    def __repr__(self):
        return "<Channel ban channel_to_ban %d>" % self.channel_to_ban


ChannelBan.__table__.create(checkfirst=True)
ChannelGlobalBan.__table__.create(checkfirst=True)

CHANNEL_BAN_INSERTION_LOCK = threading.RLock()
CHANNEL_GLOBAL_BAN_INSERTION_LOCK = threading.RLock()


def add_channel_bans(chat_id, channel_to_ban):
    with CHANNEL_BAN_INSERTION_LOCK:
        channel_bans = ChannelBan(chat_id, channel_to_ban)
        SESSION.merge(channel_bans)
        SESSION.commit()


def get_channel_bans(chat_id):
    channel_bans = SESSION.query(ChannelBan).filter(ChannelBan.chat_id == chat_id).all()
    SESSION.close()
    if channel_bans:
        return channel_bans
    return None


def is_channel_ban_exists(chat_id, channel_name):
    is_exists = SESSION.query(ChannelBan).filter(ChannelBan.chat_id == chat_id,
                                                 ChannelBan.channel_to_ban == channel_name).first() is not None
    SESSION.close()
    return is_exists


def delete_channel_ban(chat_id, channel_ban):
    with CHANNEL_BAN_INSERTION_LOCK:
        channel_ban = SESSION.query(ChannelBan).filter(
            ChannelBan.chat_id == chat_id & ChannelBan.channel_to_ban == channel_ban)
        if channel_ban:
            SESSION.delete(channel_ban)
            SESSION.commit()
            return True
        SESSION.close()
    return False


def add_channel_global_bans(channel_to_ban):
    with CHANNEL_GLOBAL_BAN_INSERTION_LOCK:
        SESSION.merge(ChannelGlobalBan(channel_to_ban))
        SESSION.commit()


def get_channel_global_bans():
    channel_global_bans = SESSION.query(ChannelBan).all()
    SESSION.close()
    if channel_global_bans:
        return channel_global_bans
    return None


def is_global_channel_ban_exists(channel_name):
    is_exists = SESSION.query(ChannelBan).filter(ChannelBan.channel_to_ban == channel_name).first() is not None
    SESSION.close()
    return is_exists


def delete_channel_global_ban(channel_global_ban):
    with CHANNEL_GLOBAL_BAN_INSERTION_LOCK:
        channel_global_ban = SESSION.query(ChannelBan).filter(ChannelBan.channel_to_ban == channel_global_ban)
        if channel_global_ban:
            SESSION.delete(channel_global_ban)
            SESSION.commit()
            return True
        SESSION.close()
    return False


def migrate_chat(old_chat_id, new_chat_id):
    with CHANNEL_BAN_INSERTION_LOCK:
        channel_bans = SESSION.query(ChannelBan).filter(ChannelBan.chat_id == old_chat_id)
        for channel_ban in channel_bans:
            channel_ban.chat_id = str(new_chat_id)
        SESSION.commit()
