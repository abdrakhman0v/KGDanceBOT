from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from django.db.models import ProtectedError

from .models import Group
from .serializers import GroupSerializer
from account.permissions import IsAdmin
from account.auth import TelegramAuthentication

class GroupCreateView(generics.CreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdmin]
    authentication_classes = [TelegramAuthentication]

class GroupListView(APIView):
    authentication_classes = [TelegramAuthentication]

    def get(self, request):
        days = request.query_params.get('days')
        queryset = Group.objects.filter(days=days).order_by('time')
        serializer = GroupSerializer(queryset, many=True)
        return Response(serializer.data)
    
class GroupDetailView(generics.RetrieveUpdateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdmin]
    authentication_classes = [TelegramAuthentication]

class GroupDeleteAPIView(APIView):
    authentication_classes = [TelegramAuthentication]

    def delete(self, request, pk):
        try:
            group = Group.objects.get(pk=pk)
            group.delete()
            return Response({"datail":"Группа успешно удалена"})
        except ProtectedError:
            return Response({"detail":"❌ Невозможно удалить группу: в ней есть активные абонементы"}, status=400)


