from celery import shared_task
from telebot import TeleBot
from decouple import config
from .models import Subscription

@shared_task
def check_subscription_expiry(sub_id):
    bot = TeleBot(config('TG_TOKEN'))
    sub = Subscription.objects.get(id=sub_id)
    lessons_left = sub.total_lessons - len(sub.attendance)
    last_date = list(sub.attendance.keys())[-1]
    last_mark = sub.attendance[last_date]
    mark = '✅' if last_mark else '❌'
    if lessons_left == 2:
        bot.send_message(sub.user.telegram_id,
                         f"Отметка за {last_date}: {mark}\n"
                         f"Осталось {len(sub.attendance)}/{sub.total_lessons} занятий.\n"
                         "⚠️ У вас осталось 2 занятия. Абонемент скоро закончится.")
    elif lessons_left == 1:
        bot.send_message(
            sub.user.telegram_id,
            f"Отметка за {last_date}: {mark}\n"
            f"Осталось {len(sub.attendance)}/{sub.total_lessons} занятий.\n"
            "❗ У вас осталось последнее занятие. "
            "Пора приобрести новый абонемент!"
        )
    elif lessons_left == 0:
        bot.send_message(sub.user.telegram_id, "❗ Ваш абонемент истек. Приобретите новый.")
    else:
        bot.send_message(sub.user.telegram_id, 
                         f"Отметка за {last_date}: {mark}\n"
                         f"Осталось {len(sub.attendance)}/{sub.total_lessons} занятий.")