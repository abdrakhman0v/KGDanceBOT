from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.first_name', read_only=True)
    parent_last_name = serializers.CharField(source='parent.last_name', read_only=True)

    class Meta:
        model = User
        fields = '__all__'
