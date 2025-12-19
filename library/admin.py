from django.contrib import admin
from .models import Staff

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    # Поля, отображаемые в списке сотрудников в админке
    list_display = ['first_name', 'last_name', 'email', 'role']

    # Поля, по которым доступен поиск в верхней панели админки
    search_fields = ['email', 'first_name', 'last_name']