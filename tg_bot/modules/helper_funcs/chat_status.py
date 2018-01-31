from functools import wraps

from tg_bot import DEL_CMDS, SUDO_USERS, WHITELIST_USERS


def can_delete(chat, bot_id):
    return chat.get_member(bot_id).can_delete_messages


def is_user_ban_protected(chat, user_id, member=None):
    if not member:
        member = chat.get_member(user_id)
    return chat.type == 'private' \
           or member.status == 'administrator' \
           or member.status == 'creator' \
           or member.user.id in SUDO_USERS \
           or member.user.id in WHITELIST_USERS


def is_user_admin(chat, user_id, member=None):
    if not member:
        member = chat.get_member(user_id)
    return chat.type == 'private' \
           or member.status == 'administrator' \
           or member.status == 'creator' \
           or member.user.id in SUDO_USERS


def is_bot_admin(chat, bot_id):
    bot_member = chat.get_member(bot_id)
    return chat.type == 'private' \
           or bot_member.status == 'administrator' \
           or bot_member.status == 'creator'


def is_user_in_chat(chat, user_id):
    member = chat.get_member(user_id)
    return member.status != 'left' and member.status != 'kicked'


def bot_can_delete(func):
    @wraps(func)
    def delete_rights(bot, update, *args, **kwargs):
        if update.effective_chat.get_member(bot.id).can_delete_messages:
            func(bot, update, *args, **kwargs)
        else:
            update.effective_message.reply_text("I can't delete messages here! "
                                                "Make sure I'm admin and can delete other user's messages.")

    return delete_rights


def can_pin(func):
    @wraps(func)
    def pin_rights(bot, update, *args, **kwargs):
        if update.effective_chat.get_member(bot.id).can_pin_messages:
            func(bot, update, *args, **kwargs)
        else:
            update.effective_message.reply_text("I can't pin messages here! "
                                                "Make sure I'm admin and can pin messages.")

    return pin_rights


def can_promote(func):
    @wraps(func)
    def promote_rights(bot, update, *args, **kwargs):
        if update.effective_chat.get_member(bot.id).can_promote_members:
            func(bot, update, *args, **kwargs)
        else:
            update.effective_message.reply_text("I can't promote/demote people here! "
                                                "Make sure I'm admin and can appoint new admins.")

    return promote_rights


def can_restrict(func):
    @wraps(func)
    def promote_rights(bot, update, *args, **kwargs):
        if update.effective_chat.get_member(bot.id).can_restrict_members:
            func(bot, update, *args, **kwargs)
        else:
            update.effective_message.reply_text("I can't restrict people here! "
                                                "Make sure I'm admin and can appoint new admins.")

    return promote_rights


def bot_admin(func):
    @wraps(func)
    def is_admin(bot, update, *args, **kwargs):
        if is_bot_admin(update.effective_chat, bot.id):
            func(bot, update, *args, **kwargs)
        else:
            update.effective_message.reply_text("I'm not admin!")

    return is_admin


def user_admin(func):
    @wraps(func)
    def is_admin(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        if is_user_admin(update.effective_chat, user_id):
            func(bot, update, *args, **kwargs)

        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()

        else:
            update.effective_message.reply_text("Who dis non-admin telling me what to do?")

    return is_admin


def user_admin_no_reply(func):
    @wraps(func)
    def is_admin(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        if is_user_admin(update.effective_chat, user_id):
            func(bot, update, *args, **kwargs)

        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()

    return is_admin


def user_not_admin(func):
    @wraps(func)
    def is_not_admin(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        if not is_user_admin(update.effective_chat, user_id):
            func(bot, update, *args, **kwargs)

    return is_not_admin
