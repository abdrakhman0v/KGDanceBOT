import requests
from telebot import types
from telebot_calendar import Calendar, CallbackData, RUSSIAN_LANGUAGE
from datetime import datetime

API_URL = 'http://127.0.0.1:8000/subscription/'
API_URL_GROUP = 'http://127.0.0.1:8000/group/'


# to-do доделать функцию нахождения юзера,добавить функции отмены создания

class CreateSubscription:

    def __init__(self, bot):
        self.bot = bot
        self.phone_for_search = {}
        self.sub_data = {}
        self.calendar = Calendar(language=RUSSIAN_LANGUAGE)
        self.calendar_callback = CallbackData('calendar', 'action', 'year', 'month', 'day')

        self.bot.callback_query_handler(func=lambda call:call.data == 'cancel_create_sub')(self.cancel_creation)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('get_group_'))(self.get_group)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('selected_child_'))(self.select_child)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith(self.calendar_callback.prefix))(self.calendar_handler)

    def cancel_creation(self, call):
         self.sub_data.pop(call.message.chat.id, None)
         self.bot.edit_message_text(
              "❌ Создание абонемента отменено.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
         )

    def cancel_markup(self):
         markup = types.InlineKeyboardMarkup()
         markup.add(types.InlineKeyboardButton('❌ Отменить', callback_data='cancel_create_sub'))
         return markup

    def find_user(self, call):
        self.bot.send_message(call.message.chat.id, '📞 Введите номер телефона(+996): ',reply_markup=self.cancel_markup())
        self.bot.register_next_step_handler_by_chat_id(call.message.chat.id, 
                                                       callback=lambda message: self.get_phone(message)
                                                       )
        
    def get_phone(self, message):
        phone = message.text.strip()
        if phone.lower() == 'отмена':
            self.bot.send_message(message.chat.id, "❌ Создание отменено.")
            self.sub_data.pop(message.chat.id, None)
            return

        if phone.startswith('9'):
            phone = '+' + phone 
        if not phone or not phone.startswith("+") or not phone[1:].isdigit():
            self.bot.send_message(message.chat.id, f'Неверный формат номера ({phone}). Попробуйте ещё раз: ')
            self.bot.register_next_step_handler(message, lambda msg: self.get_phone(msg))
            return
        
        response = requests.get(f'http://127.0.0.1:8000/acccount/get_user/', headers={'X-Telegram-Id':str(message.from_user.id)} ,params={'phone':phone})
        try:
            if response.status_code == 200:
                data=response.json()
                first_name = data.get('first_name')
                last_name = data.get('last_name')
                role = data.get('role')
                show_role = {'parent':'Родитель','user':'Пользователь', 'student':'Ученик'}.get(role, role)
                user_id = data.get('id')

                self.sub_data[message.chat.id] = {'user_id':user_id}
                self.sub_data[message.chat.id]['first_name'] = first_name
                self.sub_data[message.chat.id]['last_name'] = last_name

                markup = types.InlineKeyboardMarkup()
                markup.row(
                    types.InlineKeyboardButton('Создать абонемент', callback_data='confirm_create_sub'),
                    types.InlineKeyboardButton('Ввести номер заново', callback_data='create_subscription')
                    )
                markup.add(types.InlineKeyboardButton('❌ Отменить', callback_data='cancel_create_sub'))
                text = (
 "📌 <b>Информация о клиенте:</b>\n\n"
    f"👤 Имя: <b>{first_name}</b>\n"
    f"👤 Фамилия: <b>{last_name}</b>\n"
    f"🎯 Роль: <b>{show_role}</b>\n")

                self.bot.send_message(message.chat.id,
                                      text=text,
                                      parse_mode='HTML',
                                      reply_markup=markup)
                if role == 'parent':
                    self.get_childs(message, user_id)
                
            elif response.status_code == 404:
                self.bot.send_message(message.chat.id, '🤷🏻‍♂️ Пользователя с таким номером не существует. Попробуйте снова:')
                self.bot.register_next_step_handler(message, lambda msg: self.get_phone(msg))

            else:
                self.bot.send_message(message.chat.id, f'Ошибка при поиске клиента: {response.status_code} {response.text}')
        except Exception as e:
                self.bot.send_message(message.chat.id, f'Ошибка: {e}')

    def get_childs(self, message, user_id):
        try:
            response = requests.get(f"{'http://127.0.0.1:8000/account/get_childs/'}", headers={'X-Telegram-Id':str(message.from_user.id)}, params={'user_id':user_id})
            if response.status_code == 200:
                data = response.json()
                markup = types.InlineKeyboardMarkup()
                for child in data:
                    child_first_name = child.get('first_name')
                    child_last_name = child.get('last_name')
                    child_id = child.get('id')

                    markup.add(types.InlineKeyboardButton(f'{child_first_name} {child_last_name}', callback_data=f'selected_child_{child_id}'))
                markup.add(types.InlineKeyboardButton('❌ Отменить', callback_data='cancel_create_sub'))
                
                self.sub_data[message.chat.id]['children'] = data
                text = "📌 <b>Выберите ребёнка, для которого создаём абонемент:</b>"
                self.bot.send_message(message.chat.id,
                                    text=text,
                                    parse_mode='HTML',
                                    reply_markup=markup)
                

            else:
                            self.bot.send_message(message.chat.id, f'Ошибка: {response.status_code} {response.text}')
        except Exception as e:
                        self.bot.send_message(message.chat.id, f'Ошибка: {e}')

    def select_child(self, call):
        child_id = call.data.split('_')[2]
        children = self.sub_data[call.message.chat.id]['children']
        child = next((c for c in children if str(c['id']) == child_id), None)

        self.sub_data[call.message.chat.id] = {'user_id':child['id']}
        self.sub_data[call.message.chat.id]['first_name']=child['first_name']
        self.sub_data[call.message.chat.id]['last_name']=child['last_name']

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Создать абонемент', callback_data='confirm_create_sub'))
        markup.add(types.InlineKeyboardButton('❌ Отменить', callback_data='cancel_create_sub'))

        text = (
            "📌 <b>Информация о ребёнке:</b>\n\n"
            f"👶 Имя: <b>{child['first_name']}</b>\n"
            f"👶 Фамилия: <b>{child['last_name']}</b>\n"
        )

        self.bot.send_message(
            call.message.chat.id,
            text=text,
            parse_mode='HTML',
            reply_markup=markup
        )
    
    def groups_list_mon(self, call):
        user_id = call.from_user.id

        response = requests.get(f'{API_URL_GROUP}list/', headers={"X-Telegram-Id":str(user_id)} ,params={"days":"mon/wed/fri"})
        if response.status_code == 200:
            groups = response.json()
            markup = types.InlineKeyboardMarkup()
            for group in groups:
                title = group['title']
                time = group['time'][:5]
                id = group['id']
                markup.add(types.InlineKeyboardButton(f"{title} {time}", callback_data=f'get_group_{id}'))
            markup.add(types.InlineKeyboardButton('⬅️Назад', callback_data='confirm_create_sub'))
            markup.add(types.InlineKeyboardButton('❌ Отменить', callback_data='cancel_create_sub'))
     
            self.bot.edit_message_text(text="<b>Список групп(пн/ср/пт):</b> ", 
                                       chat_id=call.message.chat.id, 
                                       message_id=call.message.message_id, 
                                       parse_mode='HTML',
                                       reply_markup=markup)
        else:
            self.bot.send_message(call.message.chat.id, f'Ошибка: {response.status_code} {response.text}')

    def groups_list_tue(self, call):
        user_id = call.from_user.id

        response = requests.get(f'{API_URL_GROUP}list/', headers={"X-Telegram-Id":str(user_id)} ,params={"days":"tue/thu/sat"})
        if response.status_code == 200:
            groups = response.json()
            markup = types.InlineKeyboardMarkup()
            for group in groups:
                title = group['title']
                time = group['time'][:5]
                id = group['id']
                markup.add(types.InlineKeyboardButton(f"{title} {time}", callback_data=f'get_group_{id}'))
            markup.add(types.InlineKeyboardButton('⬅️Назад', callback_data='confirm_create_sub'))
            markup.add(types.InlineKeyboardButton('❌ Отменить', callback_data='cancel_create_sub'))
     
            self.bot.edit_message_text(text="<b>Список групп(вт/чт/сб):</b> ", 
                                       chat_id=call.message.chat.id, 
                                       message_id=call.message.message_id, 
                                       parse_mode='HTML',
                                       reply_markup=markup)
        else:
            self.bot.send_message(call.message.chat.id, f'Ошибка: {response.status_code} {response.text}')

    def groups_list_sun(self, call):
        user_id = call.from_user.id

        response = requests.get(f'{API_URL_GROUP}list/', headers={"X-Telegram-Id":str(user_id)} ,params={"days":"sat/sun"})
        if response.status_code == 200:
            groups = response.json()
            markup = types.InlineKeyboardMarkup()
            for group in groups:
                title = group['title']
                time = group['time'][:5]
                id = group['id']
                markup.add(types.InlineKeyboardButton(f"{title} {time}", callback_data=f'get_group_{id}'))
            markup.add(types.InlineKeyboardButton('⬅️Назад', callback_data='confirm_create_sub'))
            markup.add(types.InlineKeyboardButton('❌ Отменить', callback_data='cancel_create_sub'))

     
            self.bot.edit_message_text(text="<b>Список групп(сб/вс):</b> ", 
                                       chat_id=call.message.chat.id, 
                                       message_id=call.message.message_id,  
                                       parse_mode='HTML',
                                       reply_markup=markup)
        else:
            self.bot.send_message(call.message.chat.id, f'Ошибка: {response.status_code} {response.text}')

    
    def get_group(self, call):
        group_id = call.data.split('_')[2]
        
        self.sub_data[call.message.chat.id]['group_id'] = group_id

        self.bot.send_message(call.message.chat.id, '💰 Введите оплаченную сумму: ', reply_markup=self.cancel_markup())
        self.bot.register_next_step_handler_by_chat_id(call.message.chat.id,
                                                       callback=lambda message: self.get_price(message))
        
    def get_price(self, message):
        price = int(message.text.strip())
        
        self.sub_data[message.chat.id]['price'] = price

        today = datetime.now()
        markup = self.calendar.create_calendar(
            name=self.calendar_callback.prefix,
            year = today.year,
            month = today.month
        )
        markup.add(types.InlineKeyboardButton('❌ Отменить', callback_data='cancel_create_sub'))

        self.bot.send_message(message.chat.id, '📅 Выберите дату начала абонемента:', reply_markup=markup)

    def calendar_handler(self, call):
        name, action, year, month, day = call.data.split(self.calendar_callback.sep)
        date = self.calendar.calendar_query_handler(bot=self.bot, call=call, name=name, action=action, year=year, month=month, day=day)
        
        if action == 'DAY':

            if 'start_date' not in self.sub_data.get(call.message.chat.id):
                self.sub_data[call.message.chat.id]['start_date'] = date.strftime('%Y-%m-%d')
                self.bot.send_message(call.message.chat.id, f"✅ Дата выбрана: {date.strftime('%d.%m.%Y')}")

                today = datetime.now()
                markup = self.calendar.create_calendar(
                    name=self.calendar_callback.prefix,
                    year = today.year,
                    month = today.month
                )
                markup.add(types.InlineKeyboardButton('❌ Отменить', callback_data='cancel_create_sub'))

                self.bot.send_message(call.message.chat.id, '📅 Теперь выберите дату конца абонемента:', reply_markup=markup)

            else:

                self.sub_data[call.message.chat.id]['end_date'] = date.strftime('%Y-%m-%d')
                self.bot.send_message(call.message.chat.id, f"✅ Дата выбрана: {date.strftime('%d.%m.%Y')}")

                self.bot.send_message(call.message.chat.id, 'Введите количество занятий: ', reply_markup=self.cancel_markup())
                self.bot.register_next_step_handler_by_chat_id(call.message.chat.id,
                                                       callback=lambda msg: self.get_total_lessons(msg))
        
    def get_total_lessons(self, message):
        total_lessons = int(message.text.strip())

        self.sub_data[message.chat.id]['total_lessons'] = total_lessons

        data = {
                'user':self.sub_data[message.chat.id]['user_id'],
                'group':self.sub_data[message.chat.id]['group_id'],
                'price':self.sub_data[message.chat.id]['price'],
                'start_date':self.sub_data[message.chat.id]['start_date'],
                'end_date':self.sub_data[message.chat.id]['end_date'],
                'total_lessons':self.sub_data[message.chat.id]['total_lessons'],
            }

        try:
            response = requests.post(f'{API_URL}create_subscription/', json=data, headers={'X-Telegram-Id':str(message.from_user.id)})
            if response.status_code == 201:
                self.bot.send_message(message.chat.id,
                                      '✅ Абонемент создан успешно!\n'
            f"👤 Клиент: {self.sub_data[message.chat.id]['first_name']} {self.sub_data[message.chat.id]['last_name']}\n"
            f"📅 Период: {self.sub_data[message.chat.id]['start_date']} - {self.sub_data[message.chat.id]['end_date']}\n"
            f"💰 Сумма: {self.sub_data[message.chat.id]['price']} сом\n"
            f"🏷 Кол-во занятий: {self.sub_data[message.chat.id]['total_lessons']}")
            else:
                self.bot.send_message(message.chat.id, f'Ошибка при создании: {response.status_code} {response.text}')
        except Exception as e:
            self.bot.send_message(message.chat.id, f'Ошибка: {e}')
            


class SubscriptionHandler:
     
    def __init__(self, bot):
          self.bot = bot
          self.bot.callback_query_handler(func=lambda call:call.data == 'my_subscriptions')(self.show_my_subscriptions)
          self.bot.callback_query_handler(func=lambda call:call.data == 'my_childs_subscriptions')(self.show_childs_subscriptions)

    def show_my_subscriptions(self,call):
        telegram_id = call.from_user.id

        try:
            response = requests.get(f'{API_URL}get_user_sub/{telegram_id}/', headers={'X-Telegram-Id':str(telegram_id)})
            if response.status_code == 200:
                subscriptions = response.json()

                markup = types.InlineKeyboardMarkup()
                if not subscriptions:
                     markup.add(types.InlineKeyboardButton('⬅️Назад', callback_data='menu'))
                     self.bot.edit_message_text(
                      '🤷🏻‍♂️ У вас нет активных абонементов',
                      chat_id=call.message.chat.id,
                      message_id=call.message.message_id,
                      reply_markup=markup
                    )
                     return
                
                text = "<b>Ваши абонементы:</b>\n\n"
                for sub in subscriptions:
                     text += (
        f"💃 <b>{sub['group_title']}</b> {sub['group_time'][:5]}\n"
        f"📅 <b>{sub['start_date']}</b> — <b>{sub['end_date']}</b>\n"
        f"📊 <i>Посещено:</i> {sub['used_lessons']} из {sub['total_lessons']} занятий\n"
        f"────────────────────\n"
    )

                markup.add(types.InlineKeyboardButton('⬅️Назад', callback_data='menu'))
                self.bot.edit_message_text(text=text,
                                           chat_id=call.message.chat.id,
                                           message_id=call.message.message_id,
                                           reply_markup=markup,
                                           parse_mode='HTML')
                
            else:
                 self.bot.send_message(call.message.chat.id, f'Ошибка response: {response.status_code} {response.text}')
        except Exception as e:
            self.bot.send_message(call.message.chat.id, f'Ошибка: {e}')

    
    def show_childs_subscriptions(self, call):
        telegram_id = call.from_user.id

        try:
            response = requests.get(f"{API_URL}get_child_sub/{telegram_id}/", headers={'X-Telegram-Id':str(telegram_id)})
            if response.status_code == 200:
                subscriptions = response.json()

                markup = types.InlineKeyboardMarkup()

                if not subscriptions:
                     markup.add(types.InlineKeyboardButton('⬅️ Главное меню', callback_data='menu'))
                     self.bot.edit_message_text(
                      '🤷🏻‍♂️ У ваших детей нет активных абонементов',
                      chat_id=call.message.chat.id,
                      message_id=call.message.message_id,
                      reply_markup=markup
                    )
                     return
                
                text = "<b>Абонементы ваших детей:</b>\n\n"
                for sub in subscriptions:
                     text += (
        f"👶 <b>{sub['last_name']} {sub['first_name']}</b>\n"
        f"💃 <b>{sub['group_title']}</b> {sub['group_time'][:5]}\n"
        f"📅 <b>{sub['start_date']}</b> — <b>{sub['end_date']}</b>\n"
        f"📊 <i>Посещено:</i> {sub['used_lessons']} из {sub['total_lessons']} занятий\n"
        f"────────────────────\n"
    )

                markup.add(types.InlineKeyboardButton('⬅️ Главное меню', callback_data='menu'))
                self.bot.edit_message_text(text=text,
                                           chat_id=call.message.chat.id,
                                           message_id=call.message.message_id,
                                           reply_markup=markup,
                                           parse_mode='HTML')
                
            else:
                 self.bot.send_message(call.message.chat.id, f'Ошибка response: {response.status_code} {response.text}')
        except Exception as e:
            self.bot.send_message(call.message.chat.id, f'Ошибка: {e}')




