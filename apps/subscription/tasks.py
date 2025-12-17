from celery import shared_task
from telebot import TeleBot
from telebot.apihelper import ApiTelegramException
from decouple import config
from .models import Subscription

bot = TeleBot(config('TG_TOKEN'))

@shared_task
def check_subscription_expiry(sub_id, date, status):
    sub = Subscription.objects.get(id=sub_id)
    time_str = sub.group.time.strftime("%H:%M") if sub.group.time else ""
    not_cancel_days = sum(1 for m in sub.attendance.values() if m != 'cancel')
    lessons_left = sub.total_lessons - not_cancel_days


    try:
        if status == 1:
            mark = '✅'
        elif status == 0:
            mark = '❌'
        else:
            text = (
                f"❗️Занятие отменено.\nДата: {date}\n"
                f"Добавлена новая дата занятия {sub.end_date.strftime('%d-%m-%Y')}")
            bot.send_message(sub.user.telegram_id, text)
            return
    
        text =(
            f"<b>Группа: {sub.group.title} {time_str}\n</b>"
            f"Отметка за {date}: {mark}\n"
            f"Осталось {lessons_left} занятий(я).\n"
            )
        
        if lessons_left == 2:
            text += "⚠️ Абонемент скоро закончится."
        elif lessons_left == 1:
            text += ("❗ У вас осталось последнее занятие. "
                    "Пора приобрести новый абонемент!")
        elif lessons_left == 0:
            text = (f"<b>Группа: {sub.group.title} {time_str}\n</b>"
                    "❗ Ваш абонемент истек. Приобретите новый.")
            bot.send_message(sub.user.telegram_id, text, parse_mode="HTML")
            sub.delete()
            return
        bot.send_message(sub.user.telegram_id, text, parse_mode="HTML")

    except ApiTelegramException:
        if status == 1:
            mark = '✅'
        elif status == 0:
            mark = '❌'
        else:
            text = (f"<b>Группа: {sub.group.title} {time_str}\n</b>"
                    f"<b>Ребенок: {sub.user.last_name} {sub.user.first_name}\n</b>"
                    f"❗️Занятие отменено. Дата: {date}"
                    f"Добавлена новая дата занятия {sub.end_date.strftime('%d-%m-%Y')}")
            bot.send_message(sub.user.parent.telegram_id, text, parse_mode="HTML")
        
        text = (f"<b>Группа: {sub.group.title} {time_str}\n</b>"
                f"<b>Ребенок: {sub.user.last_name} {sub.user.first_name}\n</b>"
                f"Отметка за {date}: {mark}\n"
                f"Осталось {lessons_left} занятий(я).\n")
        if lessons_left == 2:
            text += "⚠️ У вашего ребенка осталось 2 занятия. Абонемент скоро закончится."
        elif lessons_left == 1:
            text += (
            "❗ У вашего ребенка осталось последнее занятие. "
            "Пора приобрести новый абонемент!"
        )
        elif lessons_left == 0:
            text = (f"<b>Группа: {sub.group.title} {time_str}\n</b>"
                    f"<b>Ребенок: {sub.user.last_name} {sub.user.first_name}\n</b>"
                    "❗ Абонемент вашего ребенка истек. Приобретите новый.")
            bot.send_message(sub.user.parent.telegram_id, text)
            sub.delete()
            return
        bot.send_message(sub.user.parent.telegram_id, text, parse_mode="HTML")
        
@shared_task
def created_notification(sub_id):
    sub = Subscription.objects.get(id=sub_id)
    time_str = sub.group.time.strftime("%H:%M") if sub.group.time else ""
    try:
        bot.send_message(sub.user.telegram_id,
                    "✅ Абонемент создан успешно!\n"
                    f"👤 Ф.И.О.: {sub.user.last_name} {sub.user.first_name}\n"
                    f"👥 Группа: {sub.group.title} {time_str}\n"
                    f"📅 Период: {sub.start_date} - {sub.end_date}\n"
                    f"💰 Сумма: {sub.price} сом\n"
                    f"🎟 Кол-во занятий: {sub.total_lessons}")
    except ApiTelegramException:
        bot.send_message(sub.user.parent.telegram_id,
                    "✅ Абонемент создан успешно!\n"
                    f"👤 Ф.И.О.: {sub.user.last_name} {sub.user.first_name}\n"
                    f"👥 Группа: {sub.group.title} {time_str}\n"
                    f"📅 Период: {sub.start_date} - {sub.end_date}\n"
                    f"💰 Сумма: {sub.price} сом\n"
                    f"🎟 Кол-во занятий: {sub.total_lessons}")

@shared_task
def deleted_notification(sub_id):
    sub = Subscription.objects.get(id=sub_id)
    time_str = sub.group.time.strftime("%H:%M") if sub.group.time else ""
    try:
        bot.send_message(sub.user.telegram_id, 
                     "❗️Ваш абонемент был удален администраторам.\n\n"
                     f"👤 Ф.И.О.: {sub.user.last_name} {sub.user.first_name}\n"
                     f"👥 Группа: {sub.group.title} {time_str}\n"
                     f"📅 Период: {sub.start_date} - {sub.end_date}\n"
                     f"💰 Сумма: {sub.price} сом\n"
                     f"🎟 Кол-во занятий: {sub.total_lessons}"
                     )
    except ApiTelegramException:
        bot.send_message(sub.user.parent.telegram_id, 
                     "❗️Абонемент вашего ребенка был удален администраторам.\n\n"
                     f"👤 Ф.И.О.: {sub.user.last_name} {sub.user.first_name}\n"
                     f"👥 Группа: {sub.group.title} {time_str}\n"
                     f"📅 Период: {sub.start_date} - {sub.end_date}\n"
                     f"💰 Сумма: {sub.price} сом\n"
                     f"🎟 Кол-во занятий: {sub.total_lessons}"
                     )
    finally:
        sub.delete()

