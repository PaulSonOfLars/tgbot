from tg_bot.models import UserInfo, UserBio
from tg_bot.modules.sql import SESSION


def get_user_me_info(user_id):
    userinfo = SESSION.query(UserInfo).get(user_id)
    if userinfo:
        return userinfo.info
    return None


def set_user_me_info(user_id, info):
    userinfo = SESSION.query(UserInfo).get(user_id)
    if userinfo:
        userinfo.info = info
    else:
        userinfo = UserInfo(user_id, info)
    SESSION.add(userinfo)
    SESSION.commit()


def get_user_bio(user_id):
    userbio = SESSION.query(UserBio).get(user_id)
    if userbio:
        return userbio.bio
    return None


def set_user_bio(user_id, bio):
    userbio = SESSION.query(UserBio).get(user_id)
    if userbio:
        userbio.bio = bio
    else:
        userbio = UserBio(user_id, bio)
    SESSION.add(userbio)
    SESSION.commit()
