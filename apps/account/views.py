from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import User
from .serializers import UserSerializer
from .auth import TelegramAuthentication
from utils.permissions import IsParentOrAdmin


class TelegramRegisterView(APIView):
    authentication_classes = []

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail":"user created succeful"})

class TelegramLoginView(APIView):
    authentication_classes = [TelegramAuthentication]

    def post(self, request):
        telegram_id = request.data.get('telegram_id')
        user = get_object_or_404(User, telegram_id=telegram_id)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=200)

class ChildRegisterView(APIView):
    authentication_classes = [TelegramAuthentication]
    permission_classes = [IsParentOrAdmin]
    def post(self, request):
        telegram_id = int(request.headers.get("X-Telegram-Id"))
        parent = User.objects.get(telegram_id=telegram_id)
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(parent=parent)
        return Response({"detail":"child created succeful"})


class CheckRoleView(APIView):
    authentication_classes = [TelegramAuthentication]

    def post(self, request):
        telegram_id = request.data.get('telegram_id')
        user = get_object_or_404(User, telegram_id=telegram_id)
        return Response({'role':user.role})
    
class GetChildsView(APIView):
    authentication_classes = [TelegramAuthentication]
    
    def get(self, request):
        user_id = request.query_params.get('user_id')
        parent = User.objects.get(id=user_id)
        children = parent.children.all()
        serializer = UserSerializer(children, many=True)
        return Response(serializer.data)
    
class GetUserByPhoneView(APIView):
    authentication_classes = [TelegramAuthentication]

    def get(self, request):
        phone = request.query_params.get('phone')
        user = get_object_or_404(User, phone=phone)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=200)
    
class GetAdminsView(APIView):
    authentication_classes = [TelegramAuthentication]

    def get(self, request):
        admins = User.objects.filter(role='admin')
        serializer = UserSerializer(admins, many=True)
        return Response(serializer.data, status=200)





