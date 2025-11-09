from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import telebot
import json

from .main import bot

@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(APIView):
    authentication_classes = []

    def post(self, request):
        try:
            # print("📩 Получен апдейт:", request.data)
            if not request.data:
                return Response({"ok": True})
            json_str = json.dumps(request.data)
            update = telebot.types.Update.de_json(json_str)
            bot.process_new_updates([update])
            return Response({"ok":True})
        except Exception as e:
            print("❌ Ошибка при обработке апдейта:", e)
            return Response({"ok": True})