import requests
from telebot import types
from datetime import datetime

API_URL = "http://127.0.0.1:8000/group/"

# to-do добавить функции отмены создания, редактирования
class CreateGroup:
    def __init__(self, bot):
        self.bot = bot
        self.group_data = {}
        self.bot.callback_query_handler(func=lambda call:call.data in ['mon/wed/fri', 'tue/thu/sat', 'sat/sun'])(self.choose_day)

    def create_group(self, call):
        if  call.message.chat.id in self.group_data:
            self.bot.answer_callback_query(call.id, "⏳ Начните заново.")
            return

        self.bot.send_message(call.message.chat.id, 'Введите название группы: ')
        self.bot.register_next_step_handler(call.message, self.get_title)

    def get_title(self, message):
        title = message.text.strip()
        self.group_data[message.chat.id] = {'title':title}

        self.bot.send_message(message.chat.id, 'Введите время группы: ')
        self.bot.register_next_step_handler(message, self.get_time)
    
    def get_time(self, message):
        time_str = message.text.strip()
        
        try:
            valid_time = datetime.strptime(time_str, "%H:%M")  
        except ValueError:
            self.bot.send_message(message.chat.id, "❌ Неверный формат времени. Введите в формате ЧЧ:ММ (например, 18:30).")
            self.bot.register_next_step_handler(message, self.get_time)
            return

        self.group_data[message.chat.id]['time'] = time_str

        self.bot.send_message(message.chat.id, 'Введите возраст для группы:')
        self.bot.register_next_step_handler(message, self.get_age)

    def get_age(self, message):
        age = message.text.strip()
        self.group_data[message.chat.id]['age'] = age

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('пн/ср/пт', callback_data='mon/wed/fri'))
        markup.add(types.InlineKeyboardButton('вт/чт/сб', callback_data='tue/thu/sat'))
        markup.add(types.InlineKeyboardButton('сб/вс', callback_data='sat/sun'))
        self.bot.send_message(message.chat.id, 'Выберите дни: ', reply_markup=markup)


    def choose_day(self, call):
        telegram_id = call.from_user.id
        days = call.data

        data = {
            'title':self.group_data[call.message.chat.id]['title'],
            'time':self.group_data[call.message.chat.id]['time'],
            'age':self.group_data[call.message.chat.id]['age'],
            'days':days
        }
    
        try:
            response = requests.post(f'{API_URL}create/', headers={'X-Telegram-Id':str(telegram_id)}, json=data)
            if response.status_code == 201:
                self.bot.send_message(call.message.chat.id, f'Группа "{self.group_data[call.message.chat.id]['title']} {self.group_data[call.message.chat.id]['time']}" создана. ✅')
            else:
                error_text=f'Ошибка при создании: {response.status_code}\n{response.text}\n{call.message.text}'
                if len(error_text) > 1000:
                    error_text = error_text[:1000] + '...'
                self.bot.send_message(call.message.chat.id, error_text)
            
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
            markup.add(types.InlineKeyboardButton(f"{time} {title} {age} лет", callback_data=f'group_detail_{group_id}'))

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

    def detail_group(self, call):
        group_id = call.data.split('_')[2] 
        telegram_id=call.from_user.id
        response = requests.get(f"{API_URL}detail/{group_id}/", headers={'X-Telegram-Id':str(telegram_id)})
        try:
            if response.status_code == 200:
                title = response.json().get('title')
                time = response.json().get('time')
                days = response.json().get('days')
                amount = response.json().get('user_count')

            else:
                self.bot.send_message(call.message.chat.id, f'Ошибка: {response.status_code} {response.text}')
        except Exception as e:
            self.bot.send_message(call.message.chat.id, f'Ошибка: {e}')

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✏️ Редактировать", callback_data=f'edit_{group_id}'))
        markup.add(types.InlineKeyboardButton("🗑 Удалить", callback_data=f'confirm_delete_{group_id}'))

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
<b>📅 Дни занятий:</b> {show_days}
<b>👥 Количество клиентов:</b> {amount}
"""
        self.bot.edit_message_text(text, 
                                   call.message.chat.id, 
                                   call.message.message_id, 
                                   reply_markup=markup,
                                   parse_mode='HTML')
        

class UpdateGroup:

    def __init__(self, bot):
        self.bot = bot
        self.edit_data = {}
        self.bot.callback_query_handler(func=lambda call: call.data in ['edit_title', 'edit_time', 'edit_days', 'mon/wed/fri', 'tue/thu/sat', 'sat/sun','save_changes', 'cancel_edit'])(self.callback_handler)

    def start_update(self, call):
        group_id = call.data.split('_')[1]
        self.edit_data[call.message.chat.id] = {'group_id':group_id, 'telegram_id':call.from_user.id,'data': {}}
        self.show_edit_menu(call.message.chat.id)

    def show_edit_menu(self, chat_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✏️ Изменить название", callback_data='edit_title'))
        markup.add(types.InlineKeyboardButton("⏰ Изменить время", callback_data='edit_time'))
        markup.add(types.InlineKeyboardButton("📅 Изменить дни", callback_data='edit_days'))
        markup.add(types.InlineKeyboardButton("✅ Сохранить изменения", callback_data='save_changes'))
        markup.add(types.InlineKeyboardButton("❌ Отменить", callback_data='cancel_edit'))
        self.bot.send_message(chat_id, "Выберите, что хотите изменить:", reply_markup=markup)

    def callback_handler(self, call):
        if call.data == 'edit_title':
            self.bot.send_message(call.message.chat.id, 'Введите новое название группы:')
            self.bot.register_next_step_handler_by_chat_id(call.message.chat.id, self.get_title)
        elif call.data == 'edit_time':
            self.bot.send_message(call.message.chat.id, 'Введите новое время группы:')
            self.bot.register_next_step_handler(call.message, self.get_time)
        elif call.data == 'edit_days':
            self.choose_days(call)
        elif call.data in ['mon/wed/fri', 'tue/thu/sat', 'sat/sun']:
            self.get_days(call)
        elif call.data == 'save_changes':
            self.save_changes(call.message.chat.id,call.from_user.id,call.message)
        elif call.data == 'cancel_edit':
            self.bot.send_message(call.message.chat.id, "Редактирование отменено ❌")
            self.edit_data.pop(call.message.chat.id, None)

    def get_title(self, message):
        title = message.text
        self.edit_data[message.chat.id]['data']['title'] = title
        self.show_edit_menu(message.chat.id)
        
    def get_time(self, message):
        time_str = message.text.strip()

        try:
            validate_time = datetime.strptime(time_str, '%H:%M')
        except ValueError:
            self.bot.send_message(message.chat.id, "❌ Неверный формат времени. Введите в формате ЧЧ:ММ (например, 18:30).")
            self.bot.register_next_step_handler(message, self.get_time)
            return

        self.edit_data[message.chat.id]['data']['time'] = time_str
        self.show_edit_menu(message.chat.id)

    def choose_days(self, call):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('пн/ср/пт', callback_data='mon/wed/fri'))
        markup.add(types.InlineKeyboardButton('вт/чт/сб', callback_data='tue/thu/sat'))
        markup.add(types.InlineKeyboardButton('сб/вс', callback_data='sat/sun'))
        self.bot.send_message(call.message.chat.id, 'Выберите дни: ', reply_markup=markup)

    def get_days(self, call):
        days = call.data
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
            elif k == 'days':
                k_display=k
                v_display = {'mon/wed/fri':'Пн-Ср-Пт','tue/thu/sat':'Вт-Чт-Сб','sat/sun':'Сб-Вс'}.get(v)
            else:
                k_display = k
                v_display = v
            changes.append(f"{k_display} : {v_display}")
        self.bot.send_message(chat_id, "Сохраняем изменения:\n" + "\n".join(changes))

        get_days = requests.get(f'{API_URL}detail/{group_id}/', headers={'X-Telegram-Id':str(telegram_id)})
        days = get_days.json().get('days')

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
        group_id = call.data.split('_')[1]
        get_days = requests.get(f'{API_URL}detail/{group_id}/', headers={'X-Telegram-Id':str(telegram_id)})
        days = get_days.json().get('days')
        response = requests.delete(f'{API_URL}delete/{group_id}/', headers={'X-Telegram-Id':str(telegram_id)})
        if response.status_code in  [200, 204]:
            self.bot.send_message(call.message.chat.id, 'Группа удалена. ✅')
        elif response.status_code == 400:
            self.bot.send_message(call.message.chat.id, "❌ Невозможно удалить группу: в ней есть активные абонементы")
        else:
            self.bot.send_message(call.message.chat.id, f'Ошибка при удалении: {response.status_code} {response.text}')
            
        from bot.main import list_group_handler
        if days == 'mon/wed/fri':
            list_group_handler.groups_list_mon(call.message.chat.id, telegram_id)
        elif days == 'tue/thu/sat':
            list_group_handler.groups_list_tue(call.message.chat.id, telegram_id)
        elif days == 'sat/sun':
            list_group_handler.groups_list_sun(call.message.chat.id, telegram_id)

        




            
        



        
