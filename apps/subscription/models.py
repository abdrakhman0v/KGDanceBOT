from django.db import models

from django.utils import timezone

from apps.account.models import User
from apps.group.models import Group

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='subscriptions')
    group = models.ForeignKey(Group, on_delete=models.PROTECT, related_name='subscriptions')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    price = models.PositiveIntegerField()
    total_lessons = models.PositiveIntegerField(default=12)
    used_lessons = models.PositiveIntegerField(default=0)
    lesson_dates = models.JSONField(default=list, blank=True)
    attendance = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Абонемент'
        verbose_name_plural = 'Абонементы'

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} | {self.group}"
    
    


