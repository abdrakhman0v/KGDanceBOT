from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import User

class TelegramAuthentication(BaseAuthentication):
    def authenticate(self, request):
        telegram_id = request.headers.get('X-Telegram-Id')
        if not telegram_id:
            return None
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')
        
        return (user, None)
        