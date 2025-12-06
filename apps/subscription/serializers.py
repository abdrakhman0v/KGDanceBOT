from rest_framework import serializers

from account.models import User
from .models import Subscription

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'

    user = serializers.IntegerField(write_only=True)
    group_title = serializers.CharField(source='group.title', read_only=True)
    group_time = serializers.CharField(source='group.time', read_only=True)
    group_days = serializers.CharField(source='group.days', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    def create(self, validated_data):
        telegram_id = validated_data.pop('user')
        user = User.objects.get(telegram_id=telegram_id)
        subscription = Subscription.objects.create(user=user, **validated_data)
        return subscription
 
