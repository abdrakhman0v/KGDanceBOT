from django.db import models

from account.models import User

class Group(models.Model):
    DAYS = (
        ('mon/wed/fri','пн/ср/пт'),
        ('tue/thu/sat','вт/чт/сб'),
        ('sat/sun','сб/вс')
    )
    title = models.CharField(max_length=100)
    users = models.ManyToManyField(User, related_name='groups', blank=True)
    time = models.TimeField(blank=True, null=True)
    days = models.CharField(max_length=50, choices=DAYS, null=True)
    age = models.CharField(max_length=100, default='Все возраста')
    amount = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.title} {self.time}'

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def get_users_count(self):
        return self.users.count()