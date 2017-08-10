from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
from tg_bot import dispatcher
from tg_bot.modules.sql import finance_sql as sql


def owes(bot, update, args, user_data):
    if len(args) == 0:
        # kb of x
        owers = sql.get_owers()
        keyb = make_keyboard(owers)
        user_data["action"] = "owers"
        update.effective_message.reply_text(owers, reply_markup=keyb)
    elif len(args) == 1:
        # kb of y's who x owes money to
        ower = args[0]
        owees = sql.get_owees(ower)  # TODO: exists check
        keyb = make_keyboard(owees)
        user_data["action"] = "owees"
        user_data["ower"] = ower
        update.effective_message.reply_text(owees, reply_markup=keyb)
    elif len(args) == 2:
        # money x owes to y + add/sub button
        ower = args[0]
        owee = args[1]
        amount = sql.get_sum(ower, owee)
        keyb = make_keyboard(["add", "subtract"])
        user_data["action"] = "amount"
        user_data["ower"] = ower
        user_data["owee"] = owee
        update.effective_message.reply_text(str(amount), reply_markup=keyb)
    elif len(args) == 3:
        ower = args[0]
        # set that x owes y £z
        owee = args[1]
        amount = int(args[2])
        res = sql.set_sum(ower, owee, amount)
        update.effective_message.reply_text(res)


# TODO chekcs/error stmts
def add(bot, update, args):
    if len(args) >= 1:
        sql.add_person(args[0])


# TODO
def reset(bot, update, args, user_data):
    if len(args) >= 2:
        # clear x's debts to y
        pass


def button(bot, update, user_data):
    query = update.callback_query
    action = user_data.pop("action")
    if not action:
        # no action
        pass
    elif action == "owers":
        owers = sql.get_owers()
        keyb = make_keyboard(owers)
        user_data["action"] = "owees"
        user_data["ower"] = query.data
        bot.edit_message_text(text=query.data,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=keyb)

    elif action == "owees":
        ower = user_data.pop("ower")
        owees = sql.get_owees(ower)  # TODO: exists check
        keyb = make_keyboard(owees)
        user_data["action"] = "amount"
        user_data["ower"] = ower
        user_data["owee"] = query.data
        bot.edit_message_text(text=query.data,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=keyb)

    elif action == "amount":
        ower = user_data.pop("ower")
        owee = user_data.pop("owee")
        amount = sql.get_sum(ower, owee)
        keyb = make_keyboard(["add", "subtract"])
        bot.edit_message_text(text=amount,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=keyb)


def make_keyboard(keyboard_elems):
    max_col_n = 3
    keyboard = []
    for idx, elem in enumerate(keyboard_elems):
        if idx % max_col_n == 0:
            keyboard.append([])
        keyboard[idx // max_col_n].append(InlineKeyboardButton(elem, callback_data=elem))

    return InlineKeyboardMarkup(keyboard)


dispatcher.add_handler(CommandHandler("owes", owes, pass_args=True, pass_user_data=True))
dispatcher.add_handler(CommandHandler("reset", reset, pass_args=True, pass_user_data=True))
dispatcher.add_handler(CommandHandler("add", add, pass_args=True))
dispatcher.add_handler(CallbackQueryHandler(button, pass_user_data=True))
