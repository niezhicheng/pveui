"""发卡商城模型：商品、订单、卡密。"""

from django.db import models
from apps.common.models import BaseAuditModel


class Product(BaseAuditModel):
    """商品模型。"""

    name = models.CharField(max_length=200, verbose_name='商品名称')
    description = models.TextField(blank=True, default='', verbose_name='商品描述')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='价格')
    stock = models.PositiveIntegerField(default=0, verbose_name='库存数量')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    sort_order = models.IntegerField(default=0, verbose_name='排序')

    class Meta:
        verbose_name = '商品'
        verbose_name_plural = '商品'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name


class Card(BaseAuditModel):
    """卡密模型。"""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cards', verbose_name='商品')
    card_number = models.CharField(max_length=200, verbose_name='卡号/账号')
    card_password = models.CharField(max_length=200, blank=True, default='', verbose_name='卡密/密码')
    is_sold = models.BooleanField(default=False, verbose_name='是否已售出')
    sold_at = models.DateTimeField(null=True, blank=True, verbose_name='售出时间')

    class Meta:
        verbose_name = '卡密'
        verbose_name_plural = '卡密'
        indexes = [
            models.Index(fields=['product', 'is_sold']),
        ]

    def __str__(self):
        return f'{self.product.name} - {self.card_number}'


class Order(BaseAuditModel):
    """订单模型。"""

    ORDER_STATUS_PENDING = 'pending'
    ORDER_STATUS_PAID = 'paid'
    ORDER_STATUS_COMPLETED = 'completed'
    ORDER_STATUS_CANCELLED = 'cancelled'

    ORDER_STATUS_CHOICES = [
        (ORDER_STATUS_PENDING, '待支付'),
        (ORDER_STATUS_PAID, '已支付'),
        (ORDER_STATUS_COMPLETED, '已完成'),
        (ORDER_STATUS_CANCELLED, '已取消'),
    ]

    order_no = models.CharField(max_length=50, unique=True, verbose_name='订单号')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='orders', verbose_name='商品')
    quantity = models.PositiveIntegerField(default=1, verbose_name='购买数量')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='总价')
    contact = models.CharField(max_length=200, verbose_name='联系方式')
    remark = models.TextField(blank=True, default='', verbose_name='备注')
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default=ORDER_STATUS_PENDING, verbose_name='订单状态')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='支付时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')

    class Meta:
        verbose_name = '订单'
        verbose_name_plural = '订单'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_no']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f'{self.order_no} - {self.product.name}'


class OrderCard(BaseAuditModel):
    """订单卡密关联。"""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_cards', verbose_name='订单')
    card = models.ForeignKey(Card, on_delete=models.PROTECT, related_name='order_cards', verbose_name='卡密')

    class Meta:
        verbose_name = '订单卡密'
        verbose_name_plural = '订单卡密'
        unique_together = [['order', 'card']]

    def __str__(self):
        return f'{self.order.order_no} - {self.card.card_number}'
