from django.contrib import admin

from .models import Group

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    search_fields = ('title', 'time', 'age', 'teacher__first_name', 'teacher__last_name', 'days')
