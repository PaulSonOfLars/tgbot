# New chat added -> setup permissions
from sqlalchemy import Column, String, Boolean

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

Permissions.__table__.create()

KEYSTORE = {}


def init_permissions(chat_id, reset=False):
    curr_perm = SESSION.query(Permissions).get(str(chat_id))
    if reset:
        SESSION.delete(curr_perm)
        SESSION.flush()
    perm = Permissions(str(chat_id))
    KEYSTORE[str(chat_id)] = perm
    SESSION.add(perm)
    SESSION.commit()
    return perm


def update_lock(chat_id, lock_type, locked):
    # curr_perm = session.query(Permissions).get(str(chat_id))
    curr_perm = KEYSTORE.get(str(chat_id))
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

    SESSION.add(curr_perm)  # NOTE: do i really need to add...?
    SESSION.commit()


def is_locked(chat_id, lock_type):
    curr_perm = KEYSTORE.get(str(chat_id))
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


def load_ks():
    all_perms = SESSION.query(Permissions).all()
    for chat in all_perms:
        KEYSTORE[chat.chat_id] = chat
    print("Locked types keystore loaded, length " + str(len(KEYSTORE)))

# LOAD KEYSTORE ON BOT START
load_ks()
