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

        if phone.startswith('996'):
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

class MyProfile:

    def __init__(self, bot):
        self.bot = bot
        self.child_data = {}
        self.edit_data = {}
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('my_childs_profile_'))(self.show_my_childs)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('edit_profile_'))(self.edit_profile)
        self.bot.callback_query_handler(func=lambda call:call.data == 'cancel_edit')(self.cancel_edit)
        self.bot.message_handler(
            content_types=['text', 'contact'],
            func=lambda m:m.chat.id in self.edit_data)(self.edit_profile_fsm)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('my_child_detail_'))(self.my_childs_detail)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('edit_childs_name_'))(self.edit_childs_name)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('confirm_delete_child_'))(self.confirm_delete_child)
        self.bot.callback_query_handler(func=lambda call:call.data.startswith('delete_child_'))(self.delete_child)

    def start_profile(self, call):
        self.show_my_profile(call.message.chat.id,
                             call.message.message_id,
                             call.from_user.id)

    def show_my_profile(self, chat_id, message_id, telegram_id):
        response = requests.get(f"{API_URL}get_users_data/",
                                params={'telegram_id':telegram_id},
                                headers={"X-Telegram-Id":str(telegram_id)})
        user = response.json()
        role = user['role']
        show_role = {'parent':'Родитель', 'admin':'Администратор', 'student':'Ученик'}.get(role, role)
        markup = types.InlineKeyboardMarkup()
        if role == 'parent':
            markup.add(types.InlineKeyboardButton("Мои дети", callback_data=f"my_childs_profile_{user['id']}"))
        markup.add(types.InlineKeyboardButton("✏️ Редактировать профиль", callback_data=f"edit_profile_{user['id']}"))
        markup.add(types.InlineKeyboardButton("⬅️ Главное меню", callback_data='menu'))

        text = (
            f"<b>Имя:</b> {user['first_name']}\n"
            f"<b>Фамилия:</b> {user['last_name']}\n"
            f"<b>Номер:</b> {user['phone']}\n"
            f"<b>Роль:</b> {show_role}\n"
        )
        try:
            self.bot.edit_message_text(text=text,
                                   chat_id=chat_id,
                                   message_id=message_id,
                                   parse_mode="HTML",
                                   reply_markup=markup)
        except Exception:
            self.bot.send_message(chat_id, text, parse_mode="HTML",reply_markup=markup)
        
    def cancel_edit(self, call):
        self.edit_data.pop(call.message.chat.id, None)
        self.child_data.pop(call.message.chat.id, None)
        self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
        self.bot.send_message(call.message.chat.id, '❌ Редактирование отменено.', reply_markup=types.ReplyKeyboardRemove())

    def cancel_markup(self):
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('❌ Отменить', callback_data='cancel_edit'))
        return markup
    
    def edit_profile(self, call):
        if call.message.chat.id in self.edit_data:
            self.bot.answer_callback_query(call.id, '⏳ Вы уже начали редактирование.')
            return
        
        user_id = call.data.split('_')[-1]
        self.edit_data[call.message.chat.id] = {'id':user_id}
        self.edit_data[call.message.chat.id]['step'] = 'first_name'

        self.bot.send_message(call.message.chat.id, "Введите имя:", reply_markup=self.cancel_markup())

    def edit_profile_fsm(self, message):
        chat_id = message.chat.id
        if chat_id not in self.edit_data:
            return
        data = self.edit_data[chat_id]
        step = data['step']

        if step == 'first_name':
            first_name = message.text.strip()
            data['first_name'] = first_name
            data['step'] = 'last_name'
            self.bot.send_message(message.chat.id, "Введите фамилию:", reply_markup=self.cancel_markup())

        elif step == 'last_name':
            last_name = message.text.strip()
            data['last_name'] = last_name
            data['step'] = 'phone'
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add(types.KeyboardButton(text='📞 Отправить номер', request_contact=True))
            self.bot.send_message(message.chat.id, 'Отправьте номер телефона(+996): ', reply_markup=markup)
        
        elif step == 'phone':
            if message.contact:
                phone = message.contact.phone_number
            else:
                phone = message.text.strip()

            if phone.startswith('996'):
                phone = '+' + phone 
            if not phone or not phone.startswith("+") or not phone[1:].isdigit():
                self.bot.send_message(message.chat.id, f'Неверный формат номера ({phone}). Попробуйте ещё раз: ')
                return

            data['phone'] = phone
            self.bot.send_message(
            message.chat.id,
            "Обновляю данные...",
            reply_markup=types.ReplyKeyboardRemove()
            )

            payload = {
                'id':data['id'],
                'first_name':data['first_name'],
                'last_name':data['last_name'],
                'phone':data['phone'],
            }
            response = requests.patch(f"{API_URL}update_user/", json=payload, headers={"X-Telegram-Id":str(message.from_user.id)})
            if response.status_code == 200:
                self.bot.send_message(message.chat.id, "✅ Профиль успешно обновлен!")
                from .main import my_profile_handler
                my_profile_handler.show_my_profile(chat_id, message.message_id, message.from_user.id)
                self.edit_data.pop(message.chat.id)
            else:
                self.bot.send_message(message.chat.id, f"Ошибка при обновлении: {response.status_code} {response.text}")
                self.edit_data.pop(message.chat.id)
            

    def show_my_childs(self, call):
        user_id = call.data.split('_')[3]
        response = requests.get(f"{API_URL}get_childs/", 
                                params={'user_id':user_id},
                                headers={"X-Telegram-Id":str(call.from_user.id)})
        childs = response.json()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('+ Зарегистрировать ребенка', callback_data='register_child'))
        for child in childs:
            markup.add(types.InlineKeyboardButton(f"{child['first_name']} {child['last_name']}", callback_data=f'my_child_detail_{child['id']}_{user_id}'))
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data='my_profile'))
        self.bot.edit_message_text(text="<b>Мои дети :</b>",
                                   chat_id=call.message.chat.id,
                                   message_id=call.message.message_id,
                                   parse_mode="HTML",
                                   reply_markup=markup)
        
    def my_childs_detail(self, call):
        child = call.data.split('_')[3]
        user_id = call.data.split('_')[4]
        response = requests.get(f"{API_URL}get_child_data/{child}/", headers={"X-Telegram-Id":str(call.from_user.id)})
        child = response.json()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✏️ Изменить имя и фамилию", callback_data=f"edit_childs_name_{child['id']}"))
        markup.add(types.InlineKeyboardButton("❌ Удалить ребенка", callback_data=f"confirm_delete_child_{child['id']}_{user_id}"))
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"my_childs_profile_{user_id}"))
        text = (
            f"<b>Имя:</b> {child['first_name']}\n"
            f"<b>Фамилия:</b> {child['last_name']}\n"
        )
        self.bot.edit_message_text(text,
                                   call.message.chat.id,
                                   call.message.message_id,
                                   parse_mode='HTML',
                                   reply_markup=markup)
        
    def edit_childs_name(self, call):
        child_id = call.data.split('_')[-1]
        self.child_data[call.message.chat.id]={'child_id':child_id}

        self.bot.send_message(call.message.chat.id,"Введите имя ребенка: ", reply_markup=self.cancel_markup())
        self.bot.register_next_step_handler(call.message, self.get_child_name)

    def get_child_name(self, message):
        first_name = message.text.strip()
        self.child_data[message.chat.id]['first_name'] = first_name

        self.bot.send_message(message.chat.id,"Введите фамилию ребенка: ", reply_markup=self.cancel_markup())
        self.bot.register_next_step_handler(message, self.get_child_last_name)

    def get_child_last_name(self, message):
        chat_id = message.chat.id
        last_name = message.text.strip()
        self.child_data[chat_id]['last_name'] = last_name
        data = {
            'id':self.child_data[chat_id]['child_id'],
            'first_name':self.child_data[chat_id]['first_name'],
            'last_name':self.child_data[chat_id]['last_name'],
        }
        response = requests.patch(f"{API_URL}update_user/", json=data, headers={"X-Telegram-Id":str(message.from_user.id)})
        if response.status_code == 200:
            self.bot.send_message(chat_id, '✅ Фамилие и имя успешно изменены!')
            self.child_data.pop(chat_id)
        else:
            self.bot.send_message(chat_id, f"Ошибка при обновлении: {response.status_code} {response.text}")

    def confirm_delete_child(self, call):
        child_id = call.data.split('_')[3]
        user_id = call.data.split('_')[4]
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✅ Подтвердить", callback_data=f'delete_child_{child_id}'),
            types.InlineKeyboardButton("❌ Отмена", callback_data=f'my_child_detail_{child_id}_{user_id}'),
            )
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f'my_childs_profile_{user_id}'))
        self.bot.edit_message_text("Вы уверены что хотите удалить ребенка?",
                                   call.message.chat.id,
                                   call.message.message_id,
                                   reply_markup=markup)

    def delete_child(self, call):
        id = call.data.split('_')[-1]
        chat_id = call.message.chat.id
        response = requests.delete(f"{API_URL}delete_child/{id}/", headers={"X-Telegram-Id":str(call.from_user.id)})
        if response.status_code in [200, 204]:
            self.bot.answer_callback_query(call.id, 'Ребенок удален.')
        elif response.status_code == 400:
            self.bot.send_message(chat_id, '❌ Невозможно удалить ребенка, у него есть активные абонементы.')
        else:
            self.bot.send_message(chat_id, f"Ошибка при удалении: {response.status_code} {response.text}")
