from tg_bot.models import UserInfo, UserBio
from tg_bot.modules.sql import session


def get_user_me_info(user_id):
    userinfo = session.query(UserInfo).get(user_id)
    if userinfo:
        return userinfo.info
    return None


def set_user_me_info(user_id, info):
    userinfo = session.query(UserInfo).get(user_id)
    if userinfo:
        userinfo.info = info
    else:
        userinfo = UserInfo(user_id, info)
    session.add(userinfo)
    session.commit()


def get_user_bio(user_id):
    userbio = session.query(UserBio).get(user_id)
    if userbio:
        return userbio.bio
    return None


def set_user_bio(user_id, bio):
    userbio = session.query(UserBio).get(user_id)
    if userbio:
        userbio.bio = bio
    else:
        userbio = UserBio(user_id, bio)
    session.add(userbio)
    session.commit()
