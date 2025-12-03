from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.decorators import api_view, authentication_classes

from account.models import User
from account.serializers import UserSerializer
from account.auth import TelegramAuthentication
from account.permissions import IsAdmin

from .models import Subscription
from .serializers import SubscriptionSerializer
from .tasks import check_subscription_expiry

    
class CreateSubView(APIView):
    authentication_classes = [TelegramAuthentication]

    def post(self, request):
        serializer = SubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
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
        attendance[date] = bool(status)
        sub.attendance = attendance

        sub.used_lessons = sum(1 for s in attendance.values() if s)
        sub.save()
        check_subscription_expiry.delay(sub.id)
        check_and_delete_sub(sub.id)
        return Response({'message': 'Attendance updated', 'attendance': sub.attendance, 'total_lessons':sub.total_lessons})
    
def check_and_delete_sub(sub_id):
    sub = Subscription.objects.get(id=sub_id)
    if len(sub.attendance) == sub.total_lessons:
        sub.delete()

class DeleteSubView(APIView):
    authentication_classes = [TelegramAuthentication]
    def delete(self, request, sub_id):
        sub = Subscription.objects.get(id=sub_id)
        sub.delete()
        return Response({"detail":"Group deleted"})

    
