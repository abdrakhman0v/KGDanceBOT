from celery import shared_task
from telebot import TeleBot
from telebot.apihelper import ApiTelegramException
from decouple import config
from .models import Subscription

bot = TeleBot(config('TG_TOKEN'))

@shared_task
def check_subscription_expiry(sub_id, date, status):
    sub = Subscription.objects.get(id=sub_id)
    lessons_left = sub.total_lessons - len(sub.attendance)
    time_str = sub.group.time.strftime("%H:%M") if sub.group.time else ""
    booled_status = bool(status)
    mark = '✅' if booled_status else '❌'
    try:
        if lessons_left == 2:
            bot.send_message(sub.user.telegram_id,
                         f"Группа: {sub.group.title} {time_str}\n"
                         f"Отметка за {date}: {mark}\n"
                         f"Осталось {len(sub.attendance)}/{sub.total_lessons} занятий.\n"
                         "⚠️ У вас осталось 2 занятия. Абонемент скоро закончится.")
        elif lessons_left == 1:
            bot.send_message(
            sub.user.telegram_id,
            f"Группа: {sub.group.title} {time_str}\n"
            f"Отметка за {date}: {mark}\n"
            f"Осталось {len(sub.attendance)}/{sub.total_lessons} занятий.\n"
            "❗ У вас осталось последнее занятие. "
            "Пора приобрести новый абонемент!"
        )
        elif lessons_left == 0:
            sub.delete()
            bot.send_message(sub.user.telegram_id, "❗ Ваш абонемент истек. Приобретите новый.")
        else:
            bot.send_message(sub.user.telegram_id,
                         f"Группа: {sub.group.title} {time_str}\n"
                         f"Отметка за {date}: {mark}\n"
                         f"Осталось {len(sub.attendance)}/{sub.total_lessons} занятий.")
    except ApiTelegramException:
        if lessons_left == 2:
            bot.send_message(sub.user.parent.telegram_id,
                         f"Группа: {sub.group.title} {time_str}\n"
                         f"Ребенок: {sub.user.last_name} {sub.user.first_name}\n"
                         f"Отметка за {date}: {mark}\n"
                         f"Осталось {len(sub.attendance)}/{sub.total_lessons} занятий.\n"
                         "⚠️ У вас осталось 2 занятия. Абонемент скоро закончится.")
        elif lessons_left == 1:
            bot.send_message(
            sub.user.parent.telegram_id,
            f"Группа: {sub.group.title} {time_str}\n"
            f"Ребенок: {sub.user.last_name} {sub.user.first_name}\n"
            f"Отметка за {date}: {mark}\n"
            f"Осталось {len(sub.attendance)}/{sub.total_lessons} занятий.\n"
            "❗ У вас осталось последнее занятие. "
            "Пора приобрести новый абонемент!"
        )
        elif lessons_left == 0:
            sub.delete()
            bot.send_message(sub.user.parent.telegram_id, "❗ Ваш абонемент истек. Приобретите новый.")
        else:
            bot.send_message(sub.user.parent.telegram_id, 
                         f"Группа: {sub.group.title} {time_str}\n"
                         f"Ребенок: {sub.user.last_name} {sub.user.first_name}\n"
                         f"Отметка за {date}: {mark}\n"
                         f"Осталось {len(sub.attendance)}/{sub.total_lessons} занятий.") 
        
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

