import telebot
from telebot import types
import requests
from decouple import config

from bot.auth import Register, ChildRegister
from bot.groups import CreateGroup, ListGroup, DetailGroup, UpdateGroup, DeleteGroup
from bot.subscriptions import CreateSubscription, SubscriptionHandler
from .utils import show_menu


TOKEN = config('TG_TOKEN')
bot = telebot.TeleBot(TOKEN)
API_URL = 'http://127.0.0.1:8000/'
WEBHOOK_URL = 'https://lena-nonmetalliferous-pura.ngrok-free.dev/webhook/'


requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}",)



register_handler = Register(bot)
@bot.message_handler(commands=['start'])
def authentication(message):
    register_handler.authentication(message)
    
    
child_register_handler = ChildRegister(bot)
@bot.callback_query_handler(func=lambda call:call.data == 'register_child')
def register_child_handler(call):
    child_register_handler.child_register(call.message)

# ----------ГЛАВНОЕ МЕНЮ-----------
@bot.message_handler(commands=['menu'])
def menu_handler(message):
    telegram_id = message.from_user.id
    response = requests.post(f'{API_URL}account/role/', json={'telegram_id':telegram_id}, headers={'X-Telegram-Id':str(telegram_id)})
    if response.status_code == 200:
        role = response.json().get('role')
        show_menu(bot, role, message.chat.id, role)

@bot.callback_query_handler(func=lambda call:call.data == 'menu')
def menu(call):
    telegram_id = call.from_user.id
    response = requests.post(f'{API_URL}account/role/', json={'telegram_id':telegram_id}, headers={'X-Telegram-Id':str(telegram_id)})
    if response.status_code == 200:
        role = response.json().get('role')
        show_menu(bot, role ,call.message.chat.id, call.message.message_id, edit=True)

@bot.callback_query_handler(func=lambda call: call.data == 'exit')
def exit(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)


# --------Расписание-------
@bot.callback_query_handler(func=lambda call:call.data == 'timetable')
def timetable_handler(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Пн-Ср-Пт', callback_data='timetable_mon/wed/fri'))
    markup.add(types.InlineKeyboardButton('Вт-Чт-Сб', callback_data='timetable_tue/thu/sat'))
    markup.add(types.InlineKeyboardButton('Сб-Вс', callback_data='timetable_sat/sun'))
    markup.add(types.InlineKeyboardButton('⬅️ Главное меню', callback_data='menu'))
    bot.edit_message_text(
        'Выберите дни недели:',
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call:call.data.startswith('timetable_'))
def days_handler(call):
    days = call.data.split('_')[1]
    print(days)
    response = requests.get(f"{API_URL}/group/list/", params={'days':days}, headers={"X-Telegram-Id":str(call.from_user.id)})
    if response.status_code == 200:
        groups = response.json()
        markup = types.InlineKeyboardMarkup()
        for group in groups:
            title = group['title']
            time = group['time'][:5]
            age = group['age']
            group_id = group['id']
            markup.add(types.InlineKeyboardButton(f"{time} {title} {age}", callback_data='/'))
        markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='timetable'))

        show_days = {'mon/wed/fri':'Пн-Ср-Пт','tue/thu/sat':'Вт-Чт-Сб','sat/sun':'Сб-Вс'}.get(days)
        bot.edit_message_text(
                    text=f"<b>Список групп({show_days}):</b>",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    parse_mode='HTML',
                    reply_markup=markup
                )
        
# ------Адрес и контакты-----------
@bot.callback_query_handler(func=lambda call:call.data == 'adress_contacts')
def adress_contacts(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('⬅️ Главное меню', callback_data='menu'))
    text = (
           "<b>📍 Адрес:</b>\n"
        "🏢 ул. Токтогула 259/1, г. Каракол\n"
        "🧭 Ориентир: 2 этаж, здание банка «Capital» (бывшее кафе «Караван»)\n\n"
        
        "<b>📞 Контакты:</b>\n"
        "☎️ +996 704 490 100\n"
        "☎️ +996 704 335 430\n"
        "📲 WhatsApp: +996 550 245 254\n"
        "📸 Instagram: <a href='https://www.instagram.com/kgdance_karakol/'>@kgdance_karakol</a>\n\n"
        
        "<b>🕒 График работы:</b>\n"
        "Пн–Сб: 08:00 – 20:00\n"
        "Вс: 9:00 – 14:00"
    )

    bot.edit_message_text(
        text = text,
        chat_id = call.message.chat.id,
        message_id = call.message.message_id,
        parse_mode='HTML',
        reply_markup=markup)


# -------------ПАНЕЛЬ АДМИНИСТРАТОРА------------------
@bot.message_handler(commands=['admin'])
def check_role(message):
        telegram_id = message.from_user.id
        response = requests.post(f"{API_URL}account/role/", json={"telegram_id":telegram_id})
        role = response.json().get('role')
        if role == 'admin':
            admin(message)
        else:
            bot.send_message(message.chat.id, "❌ Вы не можете использовать эту команду.")
        
            
def admin(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Группы', callback_data='groups'))
    markup.add(types.InlineKeyboardButton('Абонементы', callback_data='subscriptions'))
    markup.add(types.InlineKeyboardButton('Зарегистрировать ребенка', callback_data='register_child'))
    markup.add(types.InlineKeyboardButton('⬅️ Главное меню', callback_data='menu'))

    bot.send_message(message.chat.id,
                          '<b>👑 Панель администратора</b>',
                          parse_mode='HTML',
                          reply_markup=markup
                          )
    
@bot.callback_query_handler(func=lambda call:call.data == 'admin_panel')
def admin_panel(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Группы', callback_data='groups'))
    markup.add(types.InlineKeyboardButton('Абонементы', callback_data='subscriptions'))
    markup.add(types.InlineKeyboardButton('Зарегистрировать ребенка', callback_data='register_child'))
    markup.add(types.InlineKeyboardButton('⬅️ Главное меню', callback_data='menu'))


    bot.edit_message_text(text = '<b>👑 Панель администратора</b>',
                          chat_id =call.message.chat.id,
                          message_id=call.message.message_id,
                          parse_mode='HTML',
                          reply_markup=markup
                          )
    


# --ГРУППЫ--
@bot.callback_query_handler(func=lambda call:call.data == 'groups')
def choose_days(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('➕ Создать', callback_data='create_group'))
    markup.add(types.InlineKeyboardButton('Пн/Ср/Пт', callback_data='mon_wed_fri'))
    markup.add(types.InlineKeyboardButton('Вт/Чт/Сб', callback_data='tue_thu_sat'))
    markup.add(types.InlineKeyboardButton('Сб/Вс', callback_data='sat_sun'))
    markup.add(types.InlineKeyboardButton('⬅️Назад', callback_data='admin_panel'))

    bot.edit_message_text(
        text = 'Выберите дни: ',
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
        )
    
list_group_handler = ListGroup(bot)
@bot.callback_query_handler(func=lambda call:call.data in ['mon_wed_fri', 'tue_thu_sat', 'sat_sun'])
def groups(call):
    if call.data == 'mon_wed_fri':
        list_group_handler.groups_list_mon(call.message.chat.id, call.from_user.id, call.message.message_id)

    elif call.data == 'tue_thu_sat':
        list_group_handler.groups_list_tue(call.message.chat.id, call.from_user.id, call.message.message_id)

    elif call.data == 'sat_sun':
        list_group_handler.groups_list_sun(call.message.chat.id, call.from_user.id, call.message.message_id)
        
create_group_handler = CreateGroup(bot)
@bot.callback_query_handler(func=lambda call:call.data == 'create_group')
def start_create_group(call):
    create_group_handler.create_group(call)

detail_group_handler = DetailGroup(bot)
@bot.callback_query_handler(func=lambda call:call.data.startswith('group_detail_'))
def start_detail(call):
    detail_group_handler.detail_group(call)

update_group_handler = UpdateGroup(bot)
@bot.callback_query_handler(func=lambda call:call.data.startswith('edit_'))
def start_update(call):
    update_group_handler.start_update(call)

@bot.callback_query_handler(func=lambda call:call.data.startswith('confirm_delete_'))
def confirm_delete(call):
    group_id = call.data.split('_')[2]

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data=f'delete_{group_id}'),
        types.InlineKeyboardButton("❌ Отмена", callback_data=f'group_detail_{group_id}')
    )
    bot.edit_message_text(
        text = 'Вы уверены что хотите удалить группу?',
        chat_id = call.message.chat.id,
        message_id = call.message.message_id,
        reply_markup=markup
    )


delete_group_handler = DeleteGroup(bot)
@bot.callback_query_handler(func=lambda call:call.data.startswith('delete'))
def start_delete(call):
    delete_group_handler.delete(call)

# --АБОНЕМЕНТЫ--

@bot.callback_query_handler(func=lambda call:call.data == 'subscriptions')
def abonements(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('+ Создать', callback_data='create_subscription'))
    markup.add(types.InlineKeyboardButton('⬅️Назад', callback_data='admin_panel'))

    bot.edit_message_text(
        '<b>Абонементы</b>',
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='HTML'
    )


create_sub_handler = CreateSubscription(bot)
@bot.callback_query_handler(func=lambda call:call.data == 'create_subscription')
def start_create(call):
    create_sub_handler.find_user(call)
    

@bot.callback_query_handler(func=lambda call:call.data == 'confirm_create_sub')
def choose_day(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Пн/Ср/Пт', callback_data='m_w_f'))
    markup.add(types.InlineKeyboardButton('Вт/Чт/Сб', callback_data='t_t_s'))
    markup.add(types.InlineKeyboardButton('Сб/Вс', callback_data='s_s'))
    markup.add(types.InlineKeyboardButton('❌ Отменить', callback_data='cancel_create_sub'))

    bot.edit_message_text(
        text = 'Выберите дни: ',
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
    )

@bot.callback_query_handler(func=lambda call:call.data in ['m_w_f', 't_t_s', 's_s'])
def groups(call):
    if call.data == 'm_w_f':
        create_sub_handler.groups_list_mon(call)

    elif call.data == 't_t_s':
        create_sub_handler.groups_list_tue(call)

    elif call.data == 's_s':
        create_sub_handler.groups_list_sun(call)

sub_handler = SubscriptionHandler(bot)






    



