from rest_framework import serializers

from .models import Group

class GroupSerializer(serializers.ModelSerializer):
    teachers_first_name = serializers.CharField(source='teacher.first_name', read_only=True)
    teachers_last_name = serializers.CharField(source='teacher.last_name', read_only=True)
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = '__all__'
    
    def get_user_count(self, obj):
        return obj.get_users_count()