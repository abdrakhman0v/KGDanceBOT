from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics

from account.models import User
from account.serializers import UserSerializer
from account.auth import TelegramAuthentication
from account.permissions import IsAdmin

from .models import Subscription
from .serializers import SubscriptionSerializer

    
class CreateSubView(generics.CreateAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAdmin]
    authentication_classes = [TelegramAuthentication]

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
    
