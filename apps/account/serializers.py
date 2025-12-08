from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    # users_group_title = serializers.CharField(source='group.title', read_only=True)
    # users_group_time = serializers.CharField(source='group.time', read_only=True)

    class Meta:
        model = User
        fields = '__all__'
