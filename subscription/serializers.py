from rest_framework import serializers

from .models import Subscription

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'

    group_title = serializers.CharField(source='group.title', read_only=True)
    group_time = serializers.CharField(source='group.time', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
 
