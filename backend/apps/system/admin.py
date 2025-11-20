from django.contrib import admin
from .models import SystemSetting


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'category', 'is_encrypted', 'is_public', 'created_at', 'updated_at']
    list_filter = ['category', 'is_encrypted', 'is_public']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

