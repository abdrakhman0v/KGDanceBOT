import requests
from telebot import types
import random

API_URL = 'http://127.0.0.1:8000/account/'

class Register:

    def __init__(self, bot):
        self.bot = bot
        self.user_data = {}
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('role'))(self.choose_role)

    def authentication(self, message):
        telegram_id = message.from_user.id
        
        response = requests.post(f"{API_URL}tg_login/", json={"telegram_id":telegram_id})
        if response.status_code == 200:
            data = response.json()
            # print(data)
            name = data.get('first_name')
            role = data.get('role')
            markup = types.InlineKeyboardMarkup()

            if role == 'user':
                markup.add(types.InlineKeyboardButton('Мои абонементы', callback_data='my_subscriptions'))
                markup.add(types.InlineKeyboardButton('Расписание занятий', callback_data='timetable'))
                
            elif role == 'parent':
                markup.add(types.InlineKeyboardButton('Мои абонементы', callback_data='my_subscriptions'))
                markup.add(types.InlineKeyboardButton('Абонементы моих детей', callback_data='my_childs_subscriptions'))
                markup.add(types.InlineKeyboardButton('Зарегистрировать ребенка', callback_data='register_child'))
                markup.add(types.InlineKeyboardButton('Расписание занятий', callback_data='timetable'))
                

            elif role == 'admin':
                markup.add(types.InlineKeyboardButton('Открыть панель администратора', callback_data='admin_panel'))
                markup.add(types.InlineKeyboardButton('Расписание занятий', callback_data='timetable'))

            self.bot.send_message(message.chat.id,f'С возвращением {name}! 🥳', reply_markup=markup)

        elif response.status_code == 404:

            self.user_data[telegram_id] = {}

            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton('Родитель', callback_data=f'role_parent_{telegram_id}'),
                types.InlineKeyboardButton('Пользователь', callback_data=f'role_user_{telegram_id}')
            )
            self.bot.send_message(message.chat.id,'Укажите кто вы:', reply_markup=markup)


    def choose_role(self, call):
        telegram_id = int(call.data.split('_')[-1])
        role = call.data.split('_')[1] 
        self.user_data[telegram_id]={'role':role}

        self.bot.send_message(call.message.chat.id, 'Введите ваше имя: ')
        self.bot.register_next_step_handler_by_chat_id(chat_id=call.message.chat.id, 
                                                       callback=lambda message:self.get_name(message, telegram_id))


    def get_name(self, message, telegram_id):
        name = message.text.strip()
        self.user_data[telegram_id]['name'] = name

        if not name:
            self.bot.send_message(message.chat.id, "Имя не может быть пустым. Попробуйте еще раз:")
            self.bot.register_next_step_handler(message, self.get_name)
            
        self.bot.send_message(message.chat.id, 'Введите фамилию: ')
        self.bot.register_next_step_handler_by_chat_id(chat_id=message.chat.id, 
                                                       callback=lambda message:self.get_last_name(message, telegram_id))


    def get_last_name(self, message, telegram_id):
        last_name = message.text.strip()
        self.user_data[telegram_id]['last_name'] = last_name

        if not last_name:
            self.bot.send_message(message.chat.id, "Фамилия не может быть пустым. Попробуйте еще раз:")
            self.bot.register_next_step_handler(message, self.get_last_name)
        
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton(text='📞 Отправить номер', request_contact=True))
        self.bot.send_message(message.chat.id, 'Отправьте номер телефона(+996): ', reply_markup=markup)
        self.bot.register_next_step_handler_by_chat_id(chat_id=message.chat.id, 
                                                       callback=lambda message:self.get_phone(message, telegram_id))
        
    
    def get_phone(self, message, telegram_id):
        # print(f"USER_DATA for {telegram_id}:", self.user_data.get(telegram_id))

        if message.contact:
            phone = message.contact.phone_number
        else:
            phone = message.text.strip()

        if phone.startswith('9'):
            phone = '+' + phone 
        if not phone or not phone.startswith("+") or not phone[1:].isdigit():
            self.bot.send_message(message.chat.id, f'Неверный формат номера ({phone}). Попробуйте ещё раз: ')
            self.bot.register_next_step_handler(message, lambda msg: self.get_phone(msg, telegram_id))
            return

        self.user_data[telegram_id]['phone'] = phone
        # remove_markup = types.ReplyKeyboardRemove()

        data = {
            'telegram_id':telegram_id,
            'username':f'user_{telegram_id}',
            'role':self.user_data[telegram_id]['role'],
            'first_name':self.user_data[telegram_id]['name'],
            'last_name':self.user_data[telegram_id]['last_name'],
            'phone':phone
        }

        try:
            response = requests.post(f"{API_URL}tg_register/", json = data)
            if response.status_code == 200:
                role = self.user_data[message.chat.id]['role']
                markup = types.InlineKeyboardMarkup()
                if role == 'user':
                    markup.add(types.InlineKeyboardButton('Мои абонементы', callback_data='my_subscriptions'))
                    markup.add(types.InlineKeyboardButton('Расписание занятий', callback_data='timetable'))

                elif role == 'parent':
                    markup.add(types.InlineKeyboardButton('Мои абонементы', callback_data='my_subscriptions'))
                    markup.add(types.InlineKeyboardButton('Абонементы моих детей', callback_data='my_childs_subscriptions'))
                    markup.add(types.InlineKeyboardButton('Зарегистрировать ребенка', callback_data='register_child'))
                    markup.add(types.InlineKeyboardButton('Расписание занятий', callback_data='timetable'))

                elif role == 'admin':
                    markup.add(types.InlineKeyboardButton('Открыть панель администратора', callback_data='admin_panel'))
                    markup.add(types.InlineKeyboardButton('Расписание занятий', callback_data='timetable'))

                    
                self.bot.send_message(message.chat.id, 'Добро пожаловать! 🎉 Вы зарегистрированы.', reply_markup=markup)
                
            else:
                self.bot.send_message(message.chat.id, f'Ошибка при регистрации: {response.status_code}\n{response.text}')
        except Exception as e:
            self.bot.send_message(message.chat.id, f'Ошибка при регестрации: {e}')
        finally:
                self.user_data.pop(telegram_id)



class ChildRegister:

    def __init__(self, bot):
        self.bot = bot
        self.child_data = {}

        self.bot.callback_query_handler(func=lambda call:call.data == 'reenter_parent_phone')(self.reenter_parent_phone)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('set_parent_'))(self.set_parent)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('child_register_'))(self.get_days)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('set_group_'))(self.set_group)

    def child_register(self, message):

        if message.chat.id in self.child_data:
            self.bot.answer_callback_query(message.id, "⏳ Вы уже начали регестрацию.")
            return
           
        self.bot.send_message(message.chat.id, 'Введите имя ребенка: ')
        self.bot.register_next_step_handler(message, self.get_child_name)

    def get_child_name(self, message):
        name = message.text
        self.child_data[message.chat.id] = {'name':name}

        self.bot.send_message(message.chat.id, 'Введите фамилию')
        self.bot.register_next_step_handler(message, self.get_child_last_name)

    def get_child_last_name(self, message):
        last_name = message.text
        self.child_data[message.chat.id]['last_name'] = last_name

        self.bot.send_message(message.chat.id, 'Введите номер родителя: ')
        self.bot.register_next_step_handler(message, self.get_parent_phone)

    def get_parent_phone(self, message):
        phone = message.text.strip()
        if phone.startswith('9'):
            phone = '+' + phone 
        if not phone or not phone.startswith("+") or not phone[1:].isdigit():
            self.bot.send_message(message.chat.id, f'Неверный формат номера ({phone}). Попробуйте ещё раз: ')
            self.bot.register_next_step_handler(message, self.get_parent_phone)
            return

        response = requests.get(f'{API_URL}get_user/', headers={'X-Telegram-Id':str(message.from_user.id)} ,params={'phone':phone})
        if response.status_code == 200:
            parent = response.json()
            first_name = parent['first_name']
            last_name = parent['last_name']
            parent_id = parent['id']
            role = parent['role']
            if role != 'parent':
                self.bot.send_message(message.chat.id, 'Этот пользователь не зарегистрирован как родитель. Попробуйте ещё раз: ')
                self.bot.register_next_step_handler(message, self.get_parent_phone)
                return

            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton('Подтвердить', callback_data = f'set_parent_{parent_id}'),
                types.InlineKeyboardButton('Ввести номер заново', callback_data = f'reenter_parent_phone')
                )

            self.bot.send_message(
                message.chat.id,
                f"Родитель найден:\n{first_name} {last_name}.\nПодтвердить?",
                reply_markup=markup
)
        
        elif response.status_code == 404:
            self.bot.send_message(message.chat.id, 'Родителя с таким номером не существует. Попробйте ещё раз: ')
            self.bot.register_next_step_handler(message, self.get_parent_phone)

    def reenter_parent_phone(self, call):
        chat_id = call.message.chat.id
        self.bot.send_message(chat_id, 'Введите номер родителя заново (+996): ')
        self.bot.register_next_step_handler(call.message, self.get_parent_phone)

    def set_parent(self,call):
        parent_id = call.data.split('_')[2]
        self.child_data[call.message.chat.id]['parent_id'] = parent_id

        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Пн/Ср/Пт', callback_data='child_register_mon/wed/fri'))
        markup.add(types.InlineKeyboardButton('Вт/Чт/Сб', callback_data='child_register_tue/thu/sat'))
        markup.add(types.InlineKeyboardButton('Сб/Вс', callback_data='child_register_sat/sun'))

        self.bot.edit_message_text(
        text = 'Выберите дни группы: ',
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
    )

    def get_days(self, call):
        days = call.data.split('_')[2]

        response = requests.get(f'{'http://127.0.0.1:8000/group/list/'}', params={'days':days}, headers={'X-Telegram-Id':str(call.from_user.id)})
        if response.status_code == 200:
            groups = response.json()
            markup = types.InlineKeyboardMarkup()
            for group in groups:
                title = group['title']
                time = group['time'][:5] 
                age = group['age']
                group_id = group['id']
                markup.add(types.InlineKeyboardButton(f"{time} {title} {age} лет", callback_data=f'set_group_{group_id}'))
            markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='set_parent_'))
            
        show_days = {'mon/wed/fri':'Пн-Ср-Пт','tue/thu/sat':'Вт-Чт-Сб','sat/sun':'Сб-Вс'}.get(days)
        self.bot.edit_message_text(
                    text=f"<b>Список групп({show_days}):</b>",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    parse_mode='HTML',
                    reply_markup=markup
                )
        
    def set_group(self, call):
        chat_id =call.message.chat.id
        group_id = call.data.split('_')[2]
        self.child_data[chat_id]['group_id']=group_id

        child_telegram_id = random.randint(10**9, 10**12)

        data = {
            'telegram_id':child_telegram_id,
            'first_name':self.child_data[chat_id]['name'],
            'last_name':self.child_data[chat_id]['last_name'],
            'parent':self.child_data[chat_id]['parent_id'],
            'group':self.child_data[chat_id]['group_id'],
            'role':'student'
        }
        try:
            response = requests.post(f"{API_URL}child_register/", 
                                     headers = {'X-Telegram-Id':str(call.from_user.id)},
                                     json=data)
            if response.status_code == 201:
                self.bot.send_message(chat_id, f"Ребёнок, {self.child_data[chat_id]['last_name']} {self.child_data[chat_id]['name']}, зарегистрирован! ✅")
            else:
                self.bot.send_message(chat_id, f'Ошибка при регистрации: {response.status_code}\n{response.text}')
        except Exception as e:
            self.bot.send_message(chat_id,f"Произошла ошибка при регистрации: {e}")
        finally:
                self.child_data.pop(chat_id)


