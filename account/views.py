from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics

from .models import  User
from .serializers import UserSerializer
from .auth import TelegramAuthentication
from .permissions import IsParentOrAdmin


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


class ChildRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsParentOrAdmin]
    authentication_classes = [TelegramAuthentication]


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
    
class GetUserView(APIView):
    authentication_classes = [TelegramAuthentication]

    def get(self, request):
        phone = request.query_params.get('phone')
        user = get_object_or_404(User, phone=phone)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=200)
        





