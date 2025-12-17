from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.account.models import User
from apps.account.auth import TelegramAuthentication

from .models import Subscription
from .serializers import SubscriptionSerializer
from .tasks import check_subscription_expiry, created_notification, deleted_notification

from datetime import timedelta

    
class CreateSubView(APIView):
    authentication_classes = [TelegramAuthentication]

    def post(self, request):
        serializer = SubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sub = serializer.save()
        created_notification.delay(sub.id)
        return Response(serializer.data)

class GetUserSubView(APIView):
    authentication_classes = [TelegramAuthentication]

    def get(self, request, telegram_id):
        user = User.objects.get(telegram_id=telegram_id)
        subscriptions = Subscription.objects.filter(user=user)
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data, status=200)
    
class GetChildSubView(APIView):
    authentication_classes = [TelegramAuthentication]
    
    def get(self, request, telegram_id):
        parent = User.objects.get(telegram_id=telegram_id)
        children = parent.children.all()
        subscriptions = Subscription.objects.filter(user__in=children)
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data, status=200)
    
class MarkAttendance(APIView):
    authentication_classes = [TelegramAuthentication]

    def patch(self, request, subscription_id):
        sub = Subscription.objects.get(id=subscription_id)
        date = request.data.get('date')
        status = request.data.get('status')

        attendance = sub.attendance or {}

        day_map = {
                'mon':0,
                'tue':1,
                'wed':2,
                'thu':3,
                'fri':4,
                'sat':5,
                'sun':6
            }
        active_days = [day_map[d] for d in sub.group.days.split('/')]
        
        if status == '1':
            status = 1
        elif status == '0':
            status = 0
        else:
            status == 'cancel'

            if sub.attendance.get(date) == 'cancel':
                    return Response({"detail":"Этот день уже отменен."}, status=400)
            
            while True:
                next_date = sub.end_date + timedelta(days=1)
                if next_date.weekday() in active_days:
                    sub.lesson_dates.append(next_date.strftime("%d-%m-%Y"))
                    sub.end_date = next_date.strftime("%Y-%m-%d")
                    break
                sub.end_date = next_date

        if date in sub.attendance and sub.attendance.get(date) == 'cancel':
            sub.lesson_dates.pop(-1)
            prev_date = sub.end_date - timedelta(days=1)
            while prev_date.weekday() not in active_days:
                prev_date -= timedelta(days=1)
            sub.end_date = prev_date.strftime("%Y-%m-%d")

        attendance[date] = status
        sub.attendance = attendance

        sub.used_lessons = sum(1 for s in attendance.values() if s == 1)
        sub.save()
        check_subscription_expiry.delay(sub.id, date, status)
        return Response({'message': 'Attendance updated', 'attendance': sub.attendance, 'total_lessons':sub.total_lessons})

class DeleteSubView(APIView):
    authentication_classes = [TelegramAuthentication]
    def delete(self, request, sub_id):
        sub = Subscription.objects.get(id=sub_id)
        deleted_notification.delay(sub.id)
        return Response({"detail":"Subscription deleted"})

    
