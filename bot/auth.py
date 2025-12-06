import requests
from telebot import types
import random
from .utils import show_menu

API_URL = 'http://127.0.0.1:8000/account/'

class Auth:

    def __init__(self, bot):
        self.bot = bot
        self.user_data = {}

        self.bot.callback_query_handler(func=lambda call:call.data.startswith('role'))(self.choose_role)

    def authentication(self, message):
        telegram_id = message.from_user.id
        
        response = requests.post(f"{API_URL}tg_login/", json={"telegram_id":telegram_id})
        if response.status_code == 200:
            data = response.json()
            name = data.get('first_name')
            role = data.get('role')
            show_menu(self.bot, role, message.chat.id)
            self.bot.send_message(message.chat.id,f'С возвращением, {name}! 🥳')

        elif response.status_code == 404:

            self.user_data[telegram_id] = {}

            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton('Родитель', callback_data=f'role_parent_{telegram_id}'),
                types.InlineKeyboardButton('Пользователь', callback_data=f'role_student_{telegram_id}')
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
        self.user_data[telegram_id]['name']=name
            
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
                show_menu(self.bot, role, message.chat.id)

                self.bot.send_message(message.chat.id, 'Добро пожаловать! 🎉 Вы зарегистрированы.', reply_markup=types.ReplyKeyboardRemove())
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

        self.bot.callback_query_handler(func=lambda call:call.data=='cancel_register_child')(self.cancel_register)

    def cancel_register(self, call):
        self.child_data.pop(call.message.chat.id, None)
        self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
        self.bot.send_message(call.message.chat.id, '❌ Регистрация отменена.')

    def cancel_markup(self):
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('❌ Отменить', callback_data='cancel_register_child'))
        return markup

    def child_register(self, call):
        if call.message.chat.id in self.child_data:
            self.bot.answer_callback_query(call.id, '⏳ Вы уже начали регистрацию')
            return
        
        self.child_data[call.message.chat.id] = {}

        self.bot.send_message(call.message.chat.id, 'Введите имя ребенка: ', reply_markup=self.cancel_markup())
        self.bot.register_next_step_handler(call.message, self.get_child_name)

    def get_child_name(self, message):
        if message.chat.id not in self.child_data:
            return
        
        first_name = message.text.strip()
        self.child_data[message.chat.id]['first_name'] = first_name

        self.bot.send_message(message.chat.id, 'Введите фамилию', reply_markup=self.cancel_markup())
        self.bot.register_next_step_handler(message, self.get_child_last_name)

    def get_child_last_name(self, message):
        if message.chat.id not in self.child_data:
            return
        last_name = message.text.strip()
        chat_id = message.chat.id
        self.child_data[chat_id]['last_name'] = last_name

        child_telegram_id = random.randint(10**8, 10**10)

        data={
            'telegram_id':child_telegram_id,
            'first_name':self.child_data[chat_id]['first_name'],
            'last_name':self.child_data[chat_id]['last_name'],
            'role':'child'
        }

        try:
            response=requests.post(f"{API_URL}child_register/", json=data, headers={'X-Telegram-Id':str(message.from_user.id)})
            if response.status_code in [200,201]:
                self.bot.send_message(chat_id, f"✅ Ребёнок, {self.child_data[chat_id]['last_name']} {self.child_data[chat_id]['first_name']}, зарегистрирован! ")
            else:
                self.bot.send_message(chat_id, f'Ошибка при регистрации: {response.status_code}\n{response.text}')
        except Exception as e:
            self.bot.send_message(chat_id,f"Произошла ошибка при регистрации: {e}")
        finally:
                self.child_data.pop(chat_id)


