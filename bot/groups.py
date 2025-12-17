import requests
from telebot import types
from datetime import datetime

API_URL = "http://127.0.0.1:8000/group/"

class CreateGroup:
    def __init__(self, bot):
        self.bot = bot
        self.group_data = {}
        self.bot.callback_query_handler(func=lambda call:call.data in ['mon/wed/fri', 'tue/thu/sat', 'sat/sun'])(self.choose_day)
        self.bot.callback_query_handler(func=lambda call:call.data == 'cancel_create_group')(self.cancel_create)

    def cancel_create(self, call):
        self.group_data.pop(call.message.chat.id)
        self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
        self.bot.send_message(call.message.chat.id, '❌ Создание группы отменено.')

    def cancel_markup(self):
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Отменить:", callback_data="cancel_create_group"))
        return markup

    def create_group(self, call):
        if call.message.chat.id in self.group_data:
            self.bot.answer_callback_query(call.id, "⏳ Вы уже начали создание.")
            return
        self.group_data[call.message.chat.id] = {}

        self.bot.send_message(call.message.chat.id, 'Введите название группы: ', reply_markup=self.cancel_markup())
        self.bot.register_next_step_handler(call.message, self.get_title)

    def get_title(self, message):
        title = message.text.strip()
        self.group_data[message.chat.id]['title'] = title

        self.bot.send_message(message.chat.id, 'Введите время группы: ')
        self.bot.register_next_step_handler(message, self.get_time)
    
    def get_time(self, message):
        time_str = message.text.strip()
        
        try:
            datetime.strptime(time_str, "%H:%M")  
        except ValueError:
            self.bot.send_message(message.chat.id, "❌ Неверный формат времени. Введите в формате ЧЧ:ММ (например, 18:30).")
            self.bot.register_next_step_handler(message, self.get_time)
            return

        self.group_data[message.chat.id]['time'] = time_str

        self.bot.send_message(message.chat.id, 'Введите имя хореографа/тренера: ', reply_markup=self.cancel_markup())
        self.bot.register_next_step_handler(message, self.get_teacher)

    def get_teacher(self, message):
        teacher = message.text.strip()
        self.group_data[message.chat.id]['teacher'] = teacher

        self.bot.send_message(message.chat.id, 'Введите возраст для группы: ', reply_markup=self.cancel_markup())
        self.bot.register_next_step_handler(message, self.get_age)

    def get_age(self, message):
        age = message.text.strip()
        self.group_data[message.chat.id]['age'] = age

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('пн/ср/пт', callback_data='mon/wed/fri'))
        markup.add(types.InlineKeyboardButton('вт/чт/сб', callback_data='tue/thu/sat'))
        markup.add(types.InlineKeyboardButton('сб/вс', callback_data='sat/sun'))
        markup.add(types.InlineKeyboardButton('❌ Отменить', callback_data='cancel_create_group'))
        self.bot.send_message(message.chat.id, 'Выберите дни: ', reply_markup=markup)


    def choose_day(self, call):
        telegram_id = call.from_user.id
        days = call.data

        data = {
            'title':self.group_data[call.message.chat.id]['title'],
            'time':self.group_data[call.message.chat.id]['time'],
            'teacher':self.group_data[call.message.chat.id]['teacher'],
            'age':self.group_data[call.message.chat.id]['age'],
            'days':days
        }
        show_days = {'mon/wed/fri':'Пн-Ср-Пт','tue/thu/sat':'Вт-Чт-Сб','sat/sun':'Сб-Вс'}.get(days)
        try:
            response = requests.post(f'{API_URL}create/', headers={'X-Telegram-Id':str(telegram_id)}, json=data)
            if response.status_code == 201:
                self.bot.send_message(call.message.chat.id, f'Группа "{self.group_data[call.message.chat.id]['title']} {self.group_data[call.message.chat.id]['time']} {show_days}" создана. ✅')
            else:
                self.bot.send_message(call.message.chat.id, f'Ошибка при создании: {response.status_code}\n{response.text}\n{call.message.text}')
            self.bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

            from bot.main import list_group_handler
            if days == 'mon/wed/fri':
                list_group_handler.groups_list_mon(call.message.chat.id, telegram_id, call.message.message_id)
            elif days == 'tue/thu/sat':
                list_group_handler.groups_list_tue(call.message.chat.id, telegram_id, call.message.message_id)
            elif days == 'sat/sun':
                list_group_handler.groups_list_sun(call.message.chat.id, telegram_id, call.message.message_id)

        except Exception as e:
            self.bot.send_message(call.message.chat.id, f'Ошибка при создании: {e}')
        finally:
            self.group_data.pop(call.message.chat.id, None)

        


class ListGroup:
    def __init__(self, bot):
        self.bot = bot

    def _send_groups(self, chat_id, telegram_id, days, message_id=None):
        response = requests.get(f'{API_URL}list/', headers={"X-Telegram-Id": str(telegram_id)}, params={"days": days})
        if response.status_code != 200:
            self.bot.send_message(chat_id, f'Ошибка: {response.status_code} {response.text}')
            return

        groups = response.json()
        markup = types.InlineKeyboardMarkup()

        for group in groups:
            title = group['title']
            time = group['time'][:5] 
            age = group['age']
            group_id = group['id']
            markup.add(types.InlineKeyboardButton(f"{time} {title} возраст: {age}", callback_data=f'group_detail_{group_id}'))

        markup.add(types.InlineKeyboardButton('⬅️Назад', callback_data='groups'))

        try:
            if message_id:
                self.bot.edit_message_text(
                    text=f"<b>Список групп ({self._days_display(days)}):</b>",
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            else:
                self.bot.send_message(chat_id,
                    text=f"<b>Список групп ({self._days_display(days)}):</b>",
                    parse_mode='HTML',
                    reply_markup=markup
                )
        except:
            self.bot.send_message(chat_id,
                    text=f"<b>Список групп ({self._days_display(days)}):</b>",
                    parse_mode='HTML',
                    reply_markup=markup
            )

    def groups_list_mon(self, chat_id, telegram_id, message_id=None):
        self._send_groups(chat_id, telegram_id, "mon/wed/fri", message_id)

    def groups_list_tue(self, chat_id, telegram_id, message_id=None):
        self._send_groups(chat_id, telegram_id, "tue/thu/sat", message_id)

    def groups_list_sun(self, chat_id, telegram_id, message_id=None):
        self._send_groups(chat_id, telegram_id, "sat/sun", message_id)

    def _days_display(self, days):
        return {'mon/wed/fri':'Пн/Ср/Пт','tue/thu/sat':'Вт/Чт/Сб','sat/sun':'Сб/Вс'}.get(days, days)
    



class DetailGroup:

    def __init__(self, bot):
        self.bot = bot
        self.group_id = {}
        self.user_to_add = {}

        self.bot.callback_query_handler(func=lambda call:call.data == 'add_client')(self.find_user)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('confirm_add_client_'))(self.add_client)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('users_list_'))(self.users_list)
        # self.bot.callback_query_handler(func=lambda call:call.data == 'cancel_add_client')(self.cancel_add_client)
    

    def detail_group(self, call):
        group_id = call.data.split('_')[2] 
        self.group_id[call.message.chat.id] = group_id
        telegram_id=call.from_user.id
        response = requests.get(f"{API_URL}detail/{group_id}/", headers={'X-Telegram-Id':str(telegram_id)})
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Список учеников", callback_data=f'users_list_{group_id}'))
        if response.status_code == 200:
            title = response.json().get('title')
            time = response.json().get('time')
            days = response.json().get('days')
            amount = response.json().get('user_count')
            teacher = response.json().get('teacher')
        else:
            self.bot.send_message(call.message.chat.id, f'Ошибка: {response.status_code} {response.text}')
            return
        
        markup.add(types.InlineKeyboardButton("✏️ Редактировать группу", callback_data=f'edit_{group_id}_{days}'))
        markup.add(types.InlineKeyboardButton("🗑 Удалить группу", callback_data=f'confirm_delete_group_{group_id}_{days}'))

        if days == 'mon/wed/fri':
            markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='mon_wed_fri'))
            show_days = 'Пн-Ср-Пт'
        elif days == 'tue/thu/sat':
            markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='tue_thu_sat'))
            show_days = 'Вт-Чт-Сб'
        elif days == 'sat/sun':
            markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='sat_sun'))
            show_days = 'Сб-Вс'


        text = f"""
<b>📌 Название группы:</b> {title}
<b>⏰ Время:</b> {time[:5]}
<b>👤 Хореограф/Тренер:</b> {teacher}
<b>📅 Дни занятий:</b> {show_days}
<b>👥 Количество учеников:</b> {amount}
"""
        self.bot.edit_message_text(text, 
                                   call.message.chat.id, 
                                   call.message.message_id, 
                                   reply_markup=markup,
                                   parse_mode='HTML')

    
    def users_list(self, call): 
        telegram_id=call.from_user.id
        group_id = call.data.split('_')[2]

        response = requests.get(f"{API_URL}get_group_users/{group_id}", headers={'X-Telegram-Id':str(call.from_user.id)})
        users = response.json()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("+ Добавить клиента в группу", callback_data=f'add_client'))

        count = 0
        for user in users:
            telegram_id = user['telegram_id']
            first_name = user['first_name']
            last_name = user['last_name']
            count += 1
            markup.add(types.InlineKeyboardButton(f"{count}. {last_name} {first_name}", callback_data=f'group_user_{telegram_id}_{group_id}'))
        markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data=f'group_detail_{group_id}'))

        self.bot.edit_message_text(text='<b>Список учеников</b>',
                                   chat_id=call.message.chat.id,
                                   message_id=call.message.message_id,
                                   parse_mode='HTML',
                                   reply_markup=markup)
        
# -------------------ДОБАВЛЕНИЕ КЛИЕНТА В ГРУППУ----------------------------------
        
    # def cancel_add_client(self, call):
    #     chat_id = call.message.chat.id
    #     self.user_to_add.pop(chat_id)
    #     self.bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)
    #     self.bot.send_message(chat_id, '❌ Добавление пользователя отменено.')
    
    # def cancel_markup(self):
    #     markup = types.InlineKeyboardMarkup()
    #     markup.add(types.InlineKeyboardButton('❌ Отменить', callback_data='cancel_add_client'))
    #     return markup
    
    def find_user(self, call):
        # if call.message.chat.id in self.user_to_add:
        #     self.bot.answer_callback_query(call.id, '⏳ Вы уже начали добавление.')
        #     return
        
        self.user_to_add[call.message.chat.id] = {}
        self.bot.send_message(call.message.chat.id, '📞 Введите номер телефона(+996): ')
        self.bot.register_next_step_handler_by_chat_id(call.message.chat.id, 
                                                       callback=lambda message: self.get_phone(message)
                                                       )
        
    def get_phone(self, message):
        phone = message.text.strip()

        if phone.startswith('9'):
            phone = '+' + phone 
        if not phone or not phone.startswith("+") or not phone[1:].isdigit():
            self.bot.send_message(message.chat.id, f'Неверный формат номера ({phone}). Попробуйте ещё раз: ')
            self.bot.register_next_step_handler(message, lambda msg: self.get_phone(msg))
            return
        
        response = requests.get(f'http://127.0.0.1:8000/account/get_user_by_phone/', headers={'X-Telegram-Id':str(message.from_user.id)} ,params={'phone':phone})
        try:
            if response.status_code == 200:
                data=response.json()
                first_name = data.get('first_name')
                last_name = data.get('last_name')
                role = data.get('role')
                show_role = {'parent':'Родитель','user':'Пользователь', 'student':'Ученик'}.get(role, role)
                user_id = data.get('id')

                if role == 'parent':
                    markup = types.InlineKeyboardMarkup()
                    markup.row(
                        types.InlineKeyboardButton('Добавить', callback_data=f'confirm_add_client_{user_id}'),
                        types.InlineKeyboardButton('Ввести номер заново', callback_data='add_client')
                        )
                    # markup.add(types.InlineKeyboardButton('❌ Отменить', callback_data='cancel_add_client'))

                    parent_text = (
                    "📌 <b>Информация о клиенте:</b>\n\n"
                    f"👤 Имя: <b>{first_name}</b>\n"
                    f"👤 Фамилия: <b>{last_name}</b>\n"
                    f"🎯 Роль: <b>{show_role}</b>\n")

                    self.bot.send_message(message.chat.id, parent_text, parse_mode='HTML', reply_markup=markup)

                    response = requests.get(f"{'http://127.0.0.1:8000/account/get_childs/'}", 
                                            headers={'X-Telegram-Id':str(message.from_user.id)}, 
                                            params={'user_id':user_id})
                    if response.status_code == 200:
                        childs = response.json()
                        for child in childs:
                            markup_for_childs = types.InlineKeyboardMarkup()
                            child_text = (
                                "📌 <b>Информация о ребенке:</b>\n\n"
                                f"👶 Имя: <b>{child['first_name']}</b>\n"
                                f"👶 Фамилия: <b>{child['last_name']}</b>\n"
                                f"👤 Родитель: <b>{child['parent_name']} {child['parent_last_name']}</b>"
                            )
                            markup_for_childs.add(types.InlineKeyboardButton("Добавить ребенка", 
                                                                             callback_data=f"confirm_add_client_{child['id']}"))
                            self.bot.send_message(message.chat.id, 
                                                  child_text, 
                                                  parse_mode="HTML",
                                                  reply_markup=markup_for_childs)

                else:
                    markup = types.InlineKeyboardMarkup()
                    markup.row(
                        types.InlineKeyboardButton('Добавить', callback_data=f'confirm_add_client_{user_id}'),
                        types.InlineKeyboardButton('Ввести номер заново', callback_data='add_client')
                        )
                    # markup.add(types.InlineKeyboardButton('❌ Отменить', callback_data='cancel_add_client'))
                    text = (
                    "📌 <b>Информация о клиенте:</b>\n\n"
                    f"👤 Имя: <b>{first_name}</b>\n"
                    f"👤 Фамилия: <b>{last_name}</b>\n"
                    f"🎯 Роль: <b>{show_role}</b>\n")

                    self.bot.send_message(message.chat.id,
                                      text=text,
                                      parse_mode='HTML',
                                      reply_markup=markup)
                
                
            elif response.status_code == 404:
                self.bot.send_message(message.chat.id, '🤷🏻‍♂️ Пользователя с таким номером не существует. Попробуйте снова:')
                self.bot.register_next_step_handler(message, lambda msg: self.get_phone(msg))

            else:
                self.bot.send_message(message.chat.id, f'Ошибка при поиске клиента: {response.status_code} {response.text}')
        except Exception as e:
                self.bot.send_message(message.chat.id, f'Ошибка: {e}')

    def add_client(self, call):
        chat_id = call.message.chat.id
        telegram_id = call.from_user.id
        user_id = call.data.split('_')[3]
        data = {
            'user_id':user_id,
            'group_id':self.group_id[chat_id]
        }
        try:
            response = requests.patch(f"{API_URL}add_user/", json=data, headers={'X-Telegram-Id':str(telegram_id)})
            if response.status_code == 200:
                r_data = response.json()
                self.bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)           
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(f"{r_data['last_name']} {r_data['first_name']}",
                                                       callback_data=f"group_user_{r_data['telegram_id']}_{r_data['group_id']}"))
                self.bot.send_message(chat_id, 
                                      f'✅ Добавлен новый пользователь  в группу "{r_data["group_title"]} {r_data["group_time"][:5]}"',
                                      reply_markup=markup)
            elif response.status_code == 400:
                r_data=response.json()
                self.bot.send_message(chat_id,
                        f'❌ {r_data["last_name"]} {r_data["first_name"]} уже состоит в группе "{r_data["group_title"]} {r_data["group_time"][:5]}"')
            else:   
                self.bot.send_message(chat_id, f'Ошибка при добавлении: {response.status_code} {response.text}')    
        except Exception as e:
            self.bot.send_message(chat_id, f'Ошибка: {e}')
        finally:
            self.user_to_add.pop(chat_id, None)


class DetailGroupUser:
    
    def __init__(self, bot):
        self.bot = bot

        self.bot.callback_query_handler(func=lambda call:call.data.startswith('mark_attendance_'))(self.mark_attendance)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('delete_from_group_'))(self.confirm_delete)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('confirm_delete_user_'))(self.delete_user)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('set_attendance_'))(self.set_attendance)
    

    def get_user_subs(self, call):  
        telegram_id = call.data.split('_')[2]
        group_id = call.data.split('_')[3]       
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        try:
            response = requests.get(f"http://127.0.0.1:8000/subscription/get_user_sub/{telegram_id}/", headers={'X-Telegram-Id':str(call.from_user.id)})
            if response.status_code == 200:
                subscriptions = response.json()

                markup = types.InlineKeyboardMarkup()
                if not subscriptions:
                     markup.add(types.InlineKeyboardButton('+ Создать абонемент', callback_data=f'create_sub_{telegram_id}_{group_id}'))
                     markup.add(types.InlineKeyboardButton('Удалить из группы', callback_data=f'delete_from_group_{telegram_id}_{group_id}'))
                     markup.add(types.InlineKeyboardButton('⬅️Назад', callback_data=f'users_list_{group_id}'))
                     self.bot.edit_message_text(
                      '🤷🏻‍♂️ У этого клиента нет активных абонементов',
                      chat_id=chat_id,
                      message_id=message_id,
                      reply_markup=markup
                    )
                     return
                
                active_text = "<b>Активные абонементы:</b>\n\n"
                # inactive_text = "<b>Неактивные абонементы:</b>\n\n"
                for sub in subscriptions:
                    if sub['group'] == int(group_id):
                        active_text += (
                        f"<b>Ф.И.О: {sub['last_name']} {sub['first_name']}</b>\n"
                        f"<b>Группа: {sub['group_title']} {sub['group_time'][:5]}</b>\n"
                        f"<b>Дата: {sub['start_date']}</b> — <b>{sub['end_date']}</b>\n"
                        f"<b>Оплачено: {sub['price']} сом</b>\n"
                        f"<i>Посещено:</i> {sub['used_lessons']} из {sub['total_lessons']} занятий\n"
                        f"🗓 Даты занятий:\n")
                        attendance = sub['attendance']

                        for day in sub['lesson_dates']:
                            mark = ''
                            if day in attendance:
                                if attendance[day] == 1:
                                    mark = "✅"
                                elif attendance[day] == 0:
                                    mark = "❌"
                                else:
                                    mark = "Отмена"

                            markup.add(types.InlineKeyboardButton(f'📅 {day.replace('-', '.')[:5]} {mark}', callback_data=f'mark_attendance_{sub['id']}_{day}_{telegram_id}_{group_id}'))
                        markup.add(types.InlineKeyboardButton('Удалить абонемент', callback_data=f'confirm_delete_sub_{sub['id']}_{telegram_id}_{group_id}'))
                        markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data=f'users_list_{group_id}'))
                        self.bot.edit_message_text(text=active_text,
                                           chat_id=chat_id,
                                           message_id=message_id,
                                           reply_markup=markup,
                                           parse_mode='HTML')
                        break

                    # elif sub['group'] == int(group_id) and sub['is_active'] == False:
                    #     inactive_text += (
                    #     f" <b>{sub['last_name']}</b> <b>{sub['first_name']}</b>\n"
                    #     f"💃 <b>{sub['group_title']}</b> {sub['group_time'][:5]}\n"
                    #     f"📅 <b>{sub['start_date']}</b> — <b>{sub['end_date']}</b>\n"
                    #     f"📊 <i>Посещено:</i> {sub['used_lessons']} из {sub['total_lessons']} занятий\n"
                    #     f"────────────────────\n"
                    #     )    
                    #     attendance = sub['attendance'] 

                    #     for day in sub['lesson_dates']:
                    #         mark = ''
                    #         if day in attendance:
                    #             if attendance[day] == True:
                    #                 mark = "✅"
                    #             else:
                    #                 mark = "❌"

                    #         markup.add(types.InlineKeyboardButton(f'📅 {day.replace('-', '.')[:5]} {mark}', callback_data=f'mark_attendance_{sub['id']}_{day}_{telegram_id}_{group_id}'))
                    #     markup.add(types.InlineKeyboardButton('Обновить абонемент', callback_data=f'update_sub_{sub['id']}'))
                    #     markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data=f'users_list_{group_id}'))
                    #     self.bot.edit_message_text(text=inactive_text,
                    #                        chat_id=chat_id,
                    #                        message_id=message_id,
                    #                        reply_markup=markup,
                    #                        parse_mode='HTML')
                    #     break
                        
                else:
                    markup.add(types.InlineKeyboardButton('+ Создать абонемент', callback_data=f'create_sub_{telegram_id}_{group_id}'))
                    markup.add(types.InlineKeyboardButton('Удалить из группы', callback_data=f'delete_from_group_{telegram_id}_{group_id}'))
                    markup.add(types.InlineKeyboardButton('⬅️Назад', callback_data=f'users_list_{group_id}'))
                    self.bot.edit_message_text(
                    '🤷🏻‍♂️ У этого клиента нет активных абонементов',
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=markup
                    )
            else:
                 self.bot.send_message(call.message.chat.id, f'Ошибка response: {response.status_code} {response.text}')
        except Exception as e:
            self.bot.send_message(call.message.chat.id, f'Ошибка: {e}')


    def mark_attendance(self, call):
        sub_id = call.data.split('_')[2]
        date = call.data.split('_')[3]
        telegram_id = call.data.split('_')[4]
        group_id = call.data.split('_')[5]

        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton('✅', callback_data=f'set_attendance_1_{sub_id}_{date}_{telegram_id}_{group_id}'),
            types.InlineKeyboardButton('❌', callback_data=f'set_attendance_0_{sub_id}_{date}_{telegram_id}_{group_id}')
        )
        markup.add(types.InlineKeyboardButton('Отмена занятия', callback_data=f'set_attendance_cancel_{sub_id}_{date}_{telegram_id}_{group_id}'))
        markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data=f'group_user_{telegram_id}_{group_id}'))

        self.bot.edit_message_text(
            f"Отметка посещаемости на <b>{date}</b>",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )

    def set_attendance(self, call):
        status = call.data.split('_')[2]
        sub_id = call.data.split('_')[3]
        date = call.data.split('_')[4]
        telegram_id = call.data.split('_')[5]
        group_id = call.data.split('_')[6]

        data = {
            'date':date,
            'status':status
        }

        response = requests.patch(f"http://127.0.0.1:8000/subscription/mark_attendance/{sub_id}/", json=data, headers={'X-Telegram-Id':str(call.from_user.id)})
        sub_data = response.json()
        if response.status_code == 200:
            not_cancel_days = sum(1 for m in sub_data['attendance'].values() if m != 'cancel')
            if not_cancel_days == sub_data['total_lessons']:
                self.bot.answer_callback_query(call.id, 'Абонемент закончился.', show_alert=True)
            self.bot.answer_callback_query(call.id, 'Отмечено')
        elif response.status_code == 400:
            self.bot.answer_callback_query(call.id, 'Этот день уже отменен')



    def confirm_delete(self, call):
        telegram_id = call.data.split('_')[3]
        group_id = call.data.split('_')[4]
        markup = types.InlineKeyboardMarkup()
        markup.row(
                   types.InlineKeyboardButton('Удалить', callback_data=f'confirm_delete_user_{telegram_id}_{group_id}'),
                   types.InlineKeyboardButton('Отмена', callback_data=f'group_user_{telegram_id}_{group_id}')
                   )
        markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data=f'users_list_{group_id}'))

        self.bot.edit_message_text(text='Вы уверены, что хотите удалить пользователя из группы?',
                                   chat_id=call.message.chat.id,
                                   message_id=call.message.message_id,
                                   reply_markup=markup)
        
    def delete_user(self, call):
        telegram_id = call.data.split('_')[3]
        group_id = call.data.split('_')[4]

        data = {
            'telegram_id':telegram_id,
            'group_id':group_id
        }
        try:
            response = requests.patch(f"{API_URL}delete_user_from_group/", json=data, headers={"X-Telegram-Id":str(call.from_user.id)})
            if response.status_code == 200:
                self.bot.answer_callback_query(call.id, 'Пользователь удален из группы.')
            else:
                self.bot.send_message(call.message.chat.id, f'Ошибка при удалении юзера: {response.status_code} {response.text}')
        except Exception as e:
            self.bot.send_message(call.message.chat.id, f'Ошибка: {e}')



class UpdateGroup:

    def __init__(self, bot):
        self.bot = bot
        self.edit_data = {}
        self.bot.callback_query_handler(func=lambda call: call.data in ['edit_title', 'edit_time', 'edit_age','edit_teacher','edit_days', 'save_changes', 'cancel_edit'])(self.callback_handler)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith('set_new_teacher_'))(self.callback_handler)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith('set_new_days_'))(self.callback_handler)

    def start_update(self, call):
        group_id = call.data.split('_')[1]
        days = call.data.split('_')[2]
        self.edit_data[call.message.chat.id] = {'group_id':group_id, 'telegram_id':call.from_user.id,'show_days':days ,'data': {}}
        self.show_edit_menu(call.message.chat.id)

    def show_edit_menu(self, chat_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✏️ Изменить название", callback_data='edit_title'))
        markup.add(types.InlineKeyboardButton("⏰ Изменить время", callback_data='edit_time'))
        markup.add(types.InlineKeyboardButton("🔢 Изменить категорию возраста", callback_data='edit_age'))
        markup.add(types.InlineKeyboardButton("👤 Изменить хореографа/тренера", callback_data='edit_teacher'))
        markup.add(types.InlineKeyboardButton("📅 Изменить дни", callback_data='edit_days'))
        markup.add(types.InlineKeyboardButton("✅ Сохранить изменения", callback_data='save_changes'))
        markup.add(types.InlineKeyboardButton("❌ Отменить", callback_data='cancel_edit'))
        self.bot.send_message(chat_id, "Выберите, что хотите изменить:", reply_markup=markup)

    def callback_handler(self, call):
        if call.data == 'edit_title':
            self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            self.bot.send_message(call.message.chat.id, 'Введите новое название группы:')
            self.bot.register_next_step_handler_by_chat_id(call.message.chat.id, self.get_title)
        elif call.data == 'edit_time':
            self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            self.bot.send_message(call.message.chat.id, 'Введите новое время группы:')
            self.bot.register_next_step_handler(call.message, self.get_time)
        elif call.data == 'edit_age':
            self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            self.bot.send_message(call.message.chat.id, 'Введите новую категорию возраста группы:')
            self.bot.register_next_step_handler_by_chat_id(call.message.chat.id, self.get_age)
        elif call.data == 'edit_teacher':
            self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            self.bot.send_message(call.message.chat.id, 'Введите нового хореографа/тренера:')
            self.bot.register_next_step_handler_by_chat_id(call.message.chat.id, self.set_new_teacher)
        elif call.data == 'edit_days':
            self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            self.choose_days(call)
        elif call.data.startswith('set_new_days_'):
            self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            self.get_days(call)
        elif call.data == 'save_changes':
            self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            self.save_changes(call.message.chat.id,call.from_user.id,call.message)
        elif call.data == 'cancel_edit':
            self.edit_data.pop(call.message.chat.id)
            self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            self.bot.send_message(call.message.chat.id, "Редактирование отменено ❌")

    def get_title(self, message):
        title = message.text
        self.edit_data[message.chat.id]['data']['title'] = title
        self.show_edit_menu(message.chat.id)
        
    def get_time(self, message):
        time_str = message.text.strip()

        try:
            datetime.strptime(time_str, '%H:%M')
        except ValueError:
            self.bot.send_message(message.chat.id, "❌ Неверный формат времени. Введите в формате ЧЧ:ММ (например, 18:30).")
            self.bot.register_next_step_handler(message, self.get_time)
            return

        self.edit_data[message.chat.id]['data']['time'] = time_str
        self.show_edit_menu(message.chat.id)

    def get_age(self, message):
        age = message.text.strip()
        self.edit_data[message.chat.id]['data']['age'] = age
        self.show_edit_menu(message.chat.id)

    def set_new_teacher(self, message):
        teacher = message.text.strip()
        self.edit_data[message.chat.id]['data']['teacher'] = teacher
        self.show_edit_menu(message.chat.id)

    def choose_days(self, call):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('пн/ср/пт', callback_data='set_new_days_mon/wed/fri'))
        markup.add(types.InlineKeyboardButton('вт/чт/сб', callback_data='set_new_days_tue/thu/sat'))
        markup.add(types.InlineKeyboardButton('сб/вс', callback_data='set_new_days_sat/sun'))
        self.bot.send_message(call.message.chat.id, 'Выберите дни: ', reply_markup=markup)

    def get_days(self, call):
        days = call.data.split('_')[3]
        self.edit_data[call.message.chat.id]['data']['days'] = days
        self.show_edit_menu(call.message.chat.id)

    def save_changes(self, chat_id, telegram_id, message):
        group_id = self.edit_data[chat_id]['group_id']
        data = self.edit_data[chat_id]['data']

        if not data:
            self.bot.send_message(chat_id, "❌ Вы ничего не изменили.")
            return
        
        changes = []
        for k, v in data.items():
            if k == 'title':
                k_display = 'Название'
                v_display = v
            elif k == 'time':
                k_display = 'Время'
                v_display = v
            elif k == 'age':
                k_display = 'Категория возраста'
                v_display = v
            elif k == 'teacher':
                k_display = 'Хореограф/Тренер'
                v_display = v
            elif k == 'days':
                k_display= 'Дни'
                v_display = {'mon/wed/fri':'Пн-Ср-Пт','tue/thu/sat':'Вт-Чт-Сб','sat/sun':'Сб-Вс'}.get(v)
            else:
                k_display = k
                v_display = v
            changes.append(f"{k_display} : {v_display}")
        self.bot.send_message(chat_id, "Сохраняем изменения:\n" + "\n".join(changes))

        try:
            response = requests.patch(
                f'{API_URL}detail/{group_id}/',
                json=data,
                headers = {'X-Telegram-Id':str(telegram_id)})
            if response.status_code in [200,204]:
                self.bot.send_message(message.chat.id, 
                                      f'Группа изменена. ✅ ')
            else:
                self.bot.send_message(message.chat.id, f'Ошибка при редактировании: {response.status_code} {response.text}')

            days = self.edit_data[message.chat.id]['show_days']

            from bot.main import list_group_handler
            if days == 'mon/wed/fri':
                list_group_handler.groups_list_mon(message.chat.id, telegram_id, message.message_id)
            elif days == 'tue/thu/sat':
                list_group_handler.groups_list_tue(message.chat.id, telegram_id, message.message_id)
            elif days == 'sat/sun':
                list_group_handler.groups_list_sun(message.chat.id, telegram_id, message.message_id)

        except Exception as e:
            self.bot.send_message(message.chat.id, f'Ошибка: {e}')
        finally:
            self.edit_data.pop(message.chat.id)

            

class DeleteGroup:
    
    def __init__(self, bot):
        self.bot = bot

    def delete(self, call):
        telegram_id = call.from_user.id
        group_id = call.data.split('_')[2]
        days = call.data.split('_')[3]

        response = requests.delete(f'{API_URL}delete/{group_id}/', headers={'X-Telegram-Id':str(telegram_id)})

        if response.status_code in [200, 204]:
            self.bot.send_message(call.message.chat.id, 'Группа удалена. ✅')
        elif response.status_code == 400:
            self.bot.send_message(call.message.chat.id, "❌ Невозможно удалить группу: в ней есть активные абонементы")
        else:
            self.bot.send_message(call.message.chat.id, f'Ошибка при удалении: {response.status_code} {response.text}')
            
        from bot.main import list_group_handler
        if days == 'mon/wed/fri':
            list_group_handler.groups_list_mon(call.message.chat.id, telegram_id, call.message.message_id)
        elif days == 'tue/thu/sat':
            list_group_handler.groups_list_tue(call.message.chat.id, telegram_id, call.message.message_id)
        elif days == 'sat/sun':
            list_group_handler.groups_list_sun(call.message.chat.id, telegram_id, call.message.message_id)

