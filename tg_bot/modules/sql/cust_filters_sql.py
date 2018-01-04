import collections
import threading

from sqlalchemy import Column, String, UnicodeText, Boolean, Integer, distinct, func

from tg_bot.modules.sql import BASE, SESSION


class CustomFilters(BASE):
    __tablename__ = "cust_filters"
    chat_id = Column(String(14), primary_key=True)
    keyword = Column(UnicodeText, primary_key=True, nullable=False)
    reply = Column(UnicodeText, nullable=False)
    is_sticker = Column(Boolean, nullable=False, default=False)
    is_document = Column(Boolean, nullable=False, default=False)
    is_image = Column(Boolean, nullable=False, default=False)
    is_audio = Column(Boolean, nullable=False, default=False)
    is_voice = Column(Boolean, nullable=False, default=False)
    is_video = Column(Boolean, nullable=False, default=False)

    has_buttons = Column(Boolean, nullable=False, default=False)
    # NOTE: Here for legacy purposes, to ensure older filters don't mess up.
    has_markdown = Column(Boolean, nullable=False, default=False)

    def __init__(self, chat_id, keyword, reply, is_sticker=False, is_document=False, is_image=False, is_audio=False,
                 is_voice=False, is_video=False, has_buttons=False):
        self.chat_id = str(chat_id)  # ensure string
        self.keyword = keyword
        self.reply = reply
        self.is_sticker = is_sticker
        self.is_document = is_document
        self.is_image = is_image
        self.is_audio = is_audio
        self.is_voice = is_voice
        self.is_video = is_video
        self.has_buttons = has_buttons
        self.has_markdown = True

    def __repr__(self):
        return "<Permissions for %s>" % self.chat_id

    def __eq__(self, other):
        return bool(isinstance(other, CustomFilters)
                    and self.chat_id == other.chat_id
                    and self.keyword == other.keyword)


class Buttons(BASE):
    __tablename__ = "cust_filter_urls"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(14), primary_key=True)
    keyword = Column(UnicodeText, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    url = Column(UnicodeText, nullable=False)

    def __init__(self, chat_id, keyword, name, url):
        self.chat_id = str(chat_id)
        self.keyword = keyword
        self.name = name
        self.url = url


CustomFilters.__table__.create(checkfirst=True)
Buttons.__table__.create(checkfirst=True)

CUST_FILT_LOCK = threading.RLock()
BUTTON_LOCK = threading.RLock()

FILTER_KEYSTORE = collections.defaultdict(list)
BUTTON_KEYSTORE = collections.defaultdict(list)


def get_all_filters():
    try:
        return SESSION.query(CustomFilters).all()
    finally:
        SESSION.close()


def add_filter(chat_id, keyword, reply, is_sticker=False, is_document=False, is_image=False, is_audio=False,
               is_voice=False, is_video=False, buttons=None):
    if buttons is None:
        buttons = []

    with CUST_FILT_LOCK:
        prev = SESSION.query(CustomFilters).get((str(chat_id), keyword))
        if prev:
            with BUTTON_LOCK:
                prev_buttons = SESSION.query(Buttons).filter(Buttons.chat_id == str(chat_id),
                                                             Buttons.keyword == keyword).all()
                for btn in prev_buttons:
                    SESSION.delete(btn)
            SESSION.delete(prev)

        filt = CustomFilters(str(chat_id), keyword, reply, is_sticker, is_document, is_image, is_audio, is_voice,
                             is_video, bool(buttons))

        if filt in FILTER_KEYSTORE[filt.chat_id]:  # if there already is a filter on that kw, remove it
            FILTER_KEYSTORE[filt.chat_id].remove(filt)

        FILTER_KEYSTORE[filt.chat_id].append(filt)
        SESSION.add(filt)
        SESSION.commit()

    for b_name, url in buttons:
        add_note_button_to_db(chat_id, keyword, b_name, url)


def remove_filter(chat_id, keyword):
    with CUST_FILT_LOCK:
        filt = SESSION.query(CustomFilters).get((str(chat_id), keyword))
        if filt:
            FILTER_KEYSTORE[filt.chat_id].remove(filt)
            SESSION.delete(filt)
            SESSION.commit()
            return True
        SESSION.close()
        return False


def get_chat_filters(chat_id):
    return FILTER_KEYSTORE[str(chat_id)]


def add_note_button_to_db(chat_id, keyword, b_name, url):
    with BUTTON_LOCK:
        button = Buttons(chat_id, keyword, b_name, url)
        SESSION.add(button)
        SESSION.commit()


def get_buttons(chat_id, keyword):
    try:
        return SESSION.query(Buttons).filter(Buttons.chat_id == str(chat_id), Buttons.keyword == keyword).all()
    finally:
        SESSION.close()


def num_filters():
    try:
        return SESSION.query(CustomFilters).count()
    finally:
        SESSION.close()


def num_chats():
    try:
        return SESSION.query(func.count(distinct(CustomFilters.chat_id))).scalar()
    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with CUST_FILT_LOCK:
        chat_filters = SESSION.query(CustomFilters).filter(CustomFilters.chat_id == str(old_chat_id)).all()
        for filt in chat_filters:
            filt.chat_id = str(new_chat_id)
        SESSION.commit()

        with BUTTON_LOCK:
            chat_buttons = SESSION.query(Buttons).filter(Buttons.chat_id == str(old_chat_id)).all()
            for b in chat_buttons:
                b.chat_id = str(new_chat_id)
            SESSION.commit()

        load_keystore()


def load_keystore():
    global FILTER_KEYSTORE
    global BUTTON_KEYSTORE

    FILTER_KEYSTORE = collections.defaultdict(list)
    BUTTON_KEYSTORE = collections.defaultdict(list)

    with CUST_FILT_LOCK:
        all_filters = SESSION.query(CustomFilters).all()
        for filt in all_filters:
            FILTER_KEYSTORE[filt.chat_id].append(filt)
        SESSION.close()
    print("{} total filters added to {} chats.".format(len(all_filters), len(FILTER_KEYSTORE)))

    with BUTTON_LOCK:
        all_buttons = SESSION.query(Buttons).all()
        for btn in all_buttons:
            BUTTON_KEYSTORE[btn.chat_id].append(btn)
        SESSION.close()
    print("{} total filter buttons added to {} chats.".format(len(all_buttons), len(BUTTON_KEYSTORE)))


load_keystore()
