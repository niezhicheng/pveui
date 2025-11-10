"""发卡商城管理后台。"""

from django.contrib import admin
from .models import Product, Card, Order, OrderCard


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'stock', 'is_active', 'sort_order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['sort_order', 'id']


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'card_number', 'card_password', 'is_sold', 'sold_at', 'created_at']
    list_filter = ['is_sold', 'product', 'created_at']
    search_fields = ['card_number', 'card_password']
    readonly_fields = ['sold_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_no', 'product', 'quantity', 'total_price', 'contact', 'status', 'created_at', 'paid_at']
    list_filter = ['status', 'created_at', 'paid_at']
    search_fields = ['order_no', 'contact']
    readonly_fields = ['order_no', 'created_at', 'paid_at', 'completed_at']


@admin.register(OrderCard)
class OrderCardAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'card', 'created_at']
    list_filter = ['created_at']
    search_fields = ['order__order_no', 'card__card_number']
