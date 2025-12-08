from telebot import types
import requests

def show_menu(bot, role, chat_id, message_id=None, edit=False):
    markup = types.InlineKeyboardMarkup()

    if role == 'student':
        markup.add(types.InlineKeyboardButton('Мой профиль', callback_data='my_profile'))
        markup.add(types.InlineKeyboardButton('Мои абонементы', callback_data='my_subscriptions'))
        markup.add(types.InlineKeyboardButton('Расписание занятий', callback_data='timetable'))
        markup.add(types.InlineKeyboardButton('Адрес и контакты', callback_data='adress_contacts'))
        markup.add(types.InlineKeyboardButton('Выйти из меню', callback_data='exit'))
        
    elif role == 'parent':
        markup.add(types.InlineKeyboardButton('Мои профиль', callback_data='my_profile'))
        markup.add(types.InlineKeyboardButton('Мои абонементы', callback_data='my_subscriptions'))
        markup.add(types.InlineKeyboardButton('Абонементы моих детей', callback_data='my_childs_subscriptions'))
        markup.add(types.InlineKeyboardButton('Расписание занятий', callback_data='timetable'))
        markup.add(types.InlineKeyboardButton('Адрес и контакты', callback_data='adress_contacts'))
        markup.add(types.InlineKeyboardButton('Выйти из меню', callback_data='exit'))

    elif role == 'admin':
        markup.add(types.InlineKeyboardButton('Мои профиль', callback_data='my_profile'))
        markup.add(types.InlineKeyboardButton('Открыть панель администратора', callback_data='admin_panel'))
        markup.add(types.InlineKeyboardButton('Расписание занятий', callback_data='timetable'))
        markup.add(types.InlineKeyboardButton('Выйти из меню', callback_data='exit'))

    if edit and message_id:
        bot.edit_message_text(
            "🏠 <b>Главное меню</b>",
            chat_id=chat_id,
            message_id=message_id,
            parse_mode='HTML',
            reply_markup=markup
        )
    else:
        bot.send_message(
            chat_id,
            "🏠 <b>Главное меню</b>",
            parse_mode='HTML',
            reply_markup=markup
        )



