import requests
from telebot import types
from telebot_calendar import Calendar, CallbackData, RUSSIAN_LANGUAGE
from datetime import datetime
from datetime import timedelta

API_URL = 'http://127.0.0.1:8000/subscription/'
API_URL_GROUP = 'http://127.0.0.1:8000/group/'


class SubscriptionHandler:
     
    def __init__(self, bot):
        self.bot = bot
        self.sub_data = {}
        self.update_data = {}

        self.calendar = Calendar(language=RUSSIAN_LANGUAGE)
        self.calendar_callback = CallbackData('calendar', 'action', 'year', 'month', 'day')
        self.bot.callback_query_handler(func=lambda call:call.data == 'cancel_create_sub')(self.cancel_creation)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('create_sub_'))(self.create_sub)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('update_sub_'))(self.update_sub)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('confirm_delete_sub_'))(self.confirm_delete_sub)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('delete_sub_'))(self.delete_sub)
        
        self.bot.callback_query_handler(func=lambda call: call.data.startswith(self.calendar_callback.prefix))(self.calendar_handler)
        self.bot.callback_query_handler(func=lambda call:call.data == 'my_subscriptions')(self.show_my_subscriptions)
        self.bot.callback_query_handler(func=lambda call:call.data == 'my_childs_subscriptions')(self.show_childs_subscriptions)

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
    
# to-do получить total_lessons автоматически

    def create_sub(self, call):
        telegram_id = call.data.split('_')[2]
        group_id = call.data.split('_')[3]

        self.sub_data[call.message.chat.id] = {'telegram_id':telegram_id}
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
                self.bot.send_message(call.message.chat.id, f"✅ Дата выбрана: {date.strftime('%d-%m-%Y')}")

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
                self.bot.send_message(call.message.chat.id, f"✅ Дата выбрана: {date.strftime('%d-%m-%Y')}")
                

                self.bot.send_message(call.message.chat.id, 'Введите количество занятий: ', reply_markup=self.cancel_markup())
                self.bot.register_next_step_handler_by_chat_id(call.message.chat.id,
                                                       callback=lambda msg: self.get_total_lessons(msg))
        
    def get_total_lessons(self, message):
        chat_id = message.chat.id
        telegram_id = message.from_user.id
        total_lessons = int(message.text.strip())

        self.sub_data[message.chat.id]['total_lessons'] = total_lessons

        start_date = datetime.strptime(self.sub_data[chat_id]['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(self.sub_data[chat_id]['end_date'], '%Y-%m-%d')

        group_id = self.sub_data[chat_id]['group_id']
        group_response = requests.get(f"http://127.0.0.1:8000/group/detail/{group_id}/", headers={'X-Telegram-Id':str(telegram_id)})
        days = group_response.json().get('days')
        
        day_map = {
            'mon':0,
            'tue':1,
            'wed':2,
            'thu':3,
            'fri':4,
            'sat':5,
            'sun':6
        }

        active_days = [day_map[d] for d in days.split('/')]
        
        lesson_dates = []
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() in active_days:
                lesson_dates.append(current_date.strftime('%d-%m-%Y'))
            current_date += timedelta(days=1)

        data = {
                'user':self.sub_data[chat_id]['telegram_id'],
                'group':self.sub_data[chat_id]['group_id'],
                'price':self.sub_data[chat_id]['price'],
                'start_date':self.sub_data[chat_id]['start_date'],
                'end_date':self.sub_data[chat_id]['end_date'],
                'total_lessons':self.sub_data[chat_id]['total_lessons'],
                'lesson_dates':lesson_dates
            }

        try:
            response = requests.post(f'{API_URL}create_subscription/', json=data, headers={'X-Telegram-Id':str(telegram_id)})
            if response.status_code in [200, 201]:
                sub = response.json()
                self.bot.send_message(chat_id,
                                      "✅ Абонемент создан успешно!\n"
            f"👤 Клиент: {sub['first_name']} {sub['last_name']}\n"
            f"👥 Группа: {sub['group_title']} {sub['group_time'][:5]}\n"
            f"📅 Период: {sub['start_date']} - {sub['end_date']}\n"
            f"💰 Сумма: {sub['price']} сом\n"
            f"🏷 Кол-во занятий: {self.sub_data[message.chat.id]['total_lessons']}")
            else:
                self.bot.send_message(message.chat.id, f'Ошибка при создании: {response.status_code} {response.text}')

            from bot.main import list_group_handler
            if sub['group_days'] == 'mon/wed/fri':
                list_group_handler.groups_list_mon(chat_id, telegram_id, message.message_id)
            elif sub['group_days'] == 'tue/thu/sat':
                list_group_handler.groups_list_tue(chat_id, telegram_id, message.message_id)
            elif sub['group_days'] == 'sat/sun':
                list_group_handler.groups_list_sun(chat_id, telegram_id, message.message_id)

        except Exception as e:
            self.bot.send_message(message.chat.id, f'Ошибка: {e}')
        finally:
            self.sub_data.pop


    
    def update_sub(self, call):
        sub_id = call.data.split('_')[2]
        self.update_data[call.message.chat.id] = {'sub_id':sub_id}

        today = datetime.now()
        markup = self.calendar.create_calendar(
            name=self.calendar_callback.prefix,
            year = today.year,
            month = today.month
        )

        self.bot.send_message(call.message.chat.id, '📅 Выберите дату начала абонемента:', reply_markup=markup)


        name, action, year, month, day = call.data.split(self.calendar_callback.sep)
        date = self.calendar.calendar_query_handler(bot=self.bot, call=call, name=name, action=action, year=year, month=month, day=day)
        
        if action == 'DAY':

            if 'start_date' not in self.sub_data.get(call.message.chat.id):
                self.update_data[call.message.chat.id]['start_date'] = date.strftime('%Y-%m-%d')
                self.bot.send_message(call.message.chat.id, f"✅ Дата выбрана: {date.strftime('%d-%m-%Y')}")

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
                self.bot.send_message(call.message.chat.id, f"✅ Дата выбрана: {date.strftime('%d-%m-%Y')}")

    def confirm_delete_sub(self, call):
        sub_id = call.data.split('_')[3]
        telegram_id = call.data.split('_')[4]
        group_id = call.data.split('_')[5]

        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton('Подтвердить', callback_data=f'delete_sub_{sub_id}'),
            types.InlineKeyboardButton('⬅️ Назад', callback_data=f'group_user_{telegram_id}_{group_id}')
            )
        self.bot.edit_message_text(text='Вы уверены, что хотите удалить абонемент?',
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
                                   )
        
    def delete_sub(self,call):
        sub_id = call.data.split('_')[2]
        response=requests.delete(f"{API_URL}delete_sub/{sub_id}/", headers={'X-Telegram-Id':str(call.from_user.id)}) 
        self.bot.answer_callback_query(call.id, 'Абонемент удален')

    def show_my_subscriptions(self,call):
        telegram_id = call.from_user.id

        try:
            response = requests.get(f'{API_URL}get_user_sub/{telegram_id}/', headers={'X-Telegram-Id':str(telegram_id)})
            if response.status_code == 200:
                subscriptions = response.json()

                markup = types.InlineKeyboardMarkup()
                if not subscriptions:
                     markup.add(types.InlineKeyboardButton('⬅️ Главное меню', callback_data='menu'))
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
        f"<b>Ф.И.О: {sub['last_name']} {sub['first_name']}</b>\n"
        f"<b>Группа: {sub['group_title']} {sub['group_time'][:5]}</b>\n"
        f"<b>Дата: {sub['start_date']}</b> — <b>{sub['end_date']}</b>\n"
        f"<i>Посещено:</i> {sub['used_lessons']} из {sub['total_lessons']} занятий\n"
        f"🗓 Даты занятий:\n")
                    attendance = sub['attendance']
                    
                    for day in sub['lesson_dates']:
                        
                        mark = ''
                        if day in attendance:
                            if attendance[day] == True:
                                mark = '✅'
                            else:
                                mark = '❌'

                        text += f" • {day.replace('-', '.')} {mark}\n"
                    text += "────────────────────\n\n"
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
        f"<b>Ф.И.О: {sub['last_name']} {sub['first_name']}</b>\n"
        f"<b>Группа: {sub['group_title']}{sub['group_time'][:5]}</b>\n"
        f"<b>Дата: {sub['start_date']}</b> — <b>{sub['end_date']}</b>\n"
        f"📊 <i>Посещено:</i> {sub['used_lessons']} из {sub['total_lessons']} занятий\n"
        f"🗓 Даты занятий:\n")
                    attendance = sub['attendance']
                    
                    for day in sub['lesson_dates']:
                        
                        mark = ''
                        if day in attendance:
                            if attendance[day] == True:
                                mark = '✅'
                            else:
                                mark = '❌'
                        
                        text += f" • {day.replace('-', '.')} {mark}\n"
                    text += "────────────────────\n\n"

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



    




