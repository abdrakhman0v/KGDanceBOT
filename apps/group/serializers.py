from rest_framework import serializers

from .models import Group

class GroupSerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField()
    time = serializers.TimeField(format="%H:%M")

    class Meta:
        model = Group
        fields = '__all__'
    
    def get_user_count(self, obj):
        return obj.get_users_count()