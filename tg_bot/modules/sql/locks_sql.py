# New chat added -> setup permissions
from sqlalchemy import Column, String, Boolean
from sqlalchemy.exc import IntegrityError

from tg_bot.modules.sql import SESSION, BASE


# TODO: add gifs
class Permissions(BASE):
    __tablename__ = "permissions"
    chat_id = Column(String(14), primary_key=True)
    audio = Column(Boolean, default=False)
    voice = Column(Boolean, default=False)
    contact = Column(Boolean, default=False)
    video = Column(Boolean, default=False)
    document = Column(Boolean, default=False)
    photo = Column(Boolean, default=False)
    sticker = Column(Boolean, default=False)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)  # ensure string
        self.audio = False
        self.voice = False
        self.contact = False
        self.video = False
        self.document = False
        self.photo = False
        self.sticker = False

    def __repr__(self):
        return "<Permissions for %s>" % self.chat_id


class Restrictions(BASE):
    __tablename__ = "restrictions"
    chat_id = Column(String(14), primary_key=True)
    messages = Column(Boolean, default=False)
    media = Column(Boolean, default=False)
    other = Column(Boolean, default=False)
    preview = Column(Boolean, default=False)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)  # ensure string
        self.messages = False
        self.media = False
        self.other = False
        self.previews = False

    def __repr__(self):
        return "<Restrictions for %s>" % self.chat_id

Permissions.__table__.create(checkfirst=True)
Restrictions.__table__.create(checkfirst=True)

LOCK_KEYSTORE = {}
RESTR_KEYSTORE = {}


def init_permissions(chat_id, reset=False):
    curr_perm = SESSION.query(Permissions).get(str(chat_id))
    if reset:
        SESSION.delete(curr_perm)
        SESSION.flush()
    perm = Permissions(str(chat_id))
    LOCK_KEYSTORE[str(chat_id)] = perm
    SESSION.add(perm)
    SESSION.commit()
    return perm


def init_restrictions(chat_id, reset=False):
    curr_restr = SESSION.query(Restrictions).get(str(chat_id))
    if reset:
        SESSION.delete(curr_restr)
        SESSION.flush()
    restr = Restrictions(str(chat_id))
    RESTR_KEYSTORE[str(chat_id)] = restr
    SESSION.add(restr)
    SESSION.commit()
    return restr


def update_lock(chat_id, lock_type, locked):
    curr_perm = LOCK_KEYSTORE.get(str(chat_id))
    if not curr_perm:
        print("Perms didnt exist for {}! creating".format(chat_id))
        curr_perm = init_permissions(chat_id)

    if lock_type == "audio":
        curr_perm.audio = locked
    elif lock_type == "voice":
        curr_perm.voice = locked
    elif lock_type == "contact":
        curr_perm.contact = locked
    elif lock_type == "video":
        curr_perm.video = locked
    elif lock_type == "document":
        curr_perm.document = locked
    elif lock_type == "photo":
        curr_perm.photo = locked
    elif lock_type == "sticker":
        curr_perm.sticker = locked

    curr = SESSION.object_session(curr_perm)
    curr.add(curr_perm)
    curr.commit()


def update_restriction(chat_id, restr_type, locked):
    curr_restr = RESTR_KEYSTORE.get(str(chat_id))
    if not curr_restr:
        print("Restr didnt exist for {}! creating".format(chat_id))
        curr_restr = init_restrictions(chat_id)
    if restr_type == "messages":
        curr_restr.messages = locked
    elif restr_type == "media":
        curr_restr.media = locked
    elif restr_type == "other":
        curr_restr.other = locked
    elif restr_type == "previews":
        curr_restr.preview = locked

    curr = SESSION.object_session(curr_restr)
    curr.add(curr_restr)
    curr.commit()


def is_locked(chat_id, lock_type):
    curr_perm = LOCK_KEYSTORE.get(str(chat_id))
    if not curr_perm:
        return False

    elif lock_type == "sticker":
        return curr_perm.sticker
    elif lock_type == "photo":
        return curr_perm.photo
    elif lock_type == "audio":
        return curr_perm.audio
    elif lock_type == "voice":
        return curr_perm.voice
    elif lock_type == "contact":
        return curr_perm.contact
    elif lock_type == "video":
        return curr_perm.video
    elif lock_type == "document":
        return curr_perm.document


def is_restr_locked(chat_id, lock_type):
    curr_restr = RESTR_KEYSTORE.get(str(chat_id))
    if not curr_restr:
        return False

    if lock_type == "messages":
        return curr_restr.messages
    elif lock_type == "media":
        return curr_restr.media
    elif lock_type == "other":
        return curr_restr.other
    elif lock_type == "previews":
        return curr_restr.previews


def load_ks():
    all_perms = SESSION.query(Permissions).all()
    for chat in all_perms:
        LOCK_KEYSTORE[chat.chat_id] = chat
    all_restr = SESSION.query(Restrictions).all()
    for chat in all_restr:
        RESTR_KEYSTORE[chat.chat_id] = chat
    print("Locked types keystore loaded, length " + str(len(LOCK_KEYSTORE)))

# LOAD KEYSTORE ON BOT START
load_ks()
