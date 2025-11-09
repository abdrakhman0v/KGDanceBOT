from rest_framework import serializers

from .models import Group

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'
    
    user_count = serializers.SerializerMethodField()

    def get_user_count(self, obj):
        return obj.get_users_count()