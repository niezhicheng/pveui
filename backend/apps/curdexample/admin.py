from django.contrib import admin
from .models import Example


@admin.register(Example)
class ExampleAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'price', 'is_active',
        'owner_organization', 'created_by', 'created_at', 'updated_by', 'updated_at', 'is_deleted',
    )
    search_fields = ('name', 'description')
    list_filter = ('is_active', 'owner_organization')
    ordering = ('-id',)

# Register your models here.
