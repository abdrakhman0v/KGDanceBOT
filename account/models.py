from django.db import models

from .manager import UserManager

class User(models.Model):
    ROLES = (
        ('student','ученик'),
        ('parent', 'родитель'),
        ('user', 'пользователь'),
        ('admin','админ')
    )
    telegram_id = models.BigIntegerField(unique=True,null=True, blank=True)
    phone = models.CharField(max_length=13, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length = 100, blank=True, null=True)
    last_name = models.CharField(max_length = 100, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLES, default='user')
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, related_name='children', null=True, blank=True)

    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


