from django.contrib import admin

from .models import Subscription

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    search_fields = ('user__first_name', 'user__last_name', 'group__title', 'group__time')
