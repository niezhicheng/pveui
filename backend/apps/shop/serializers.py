"""发卡商城序列化器。"""

from rest_framework import serializers
from .models import Product, Order, Card, OrderCard


class ProductSerializer(serializers.ModelSerializer):
    """商品序列化器。"""

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class OrderCreateSerializer(serializers.Serializer):
    """订单创建序列化器。"""

    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1, max_value=10)
    contact = serializers.CharField(required=True, max_length=200)
    remark = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_quantity(self, value):
        if value <= 0 or value > 10:
            raise serializers.ValidationError('购买数量必须在1-10之间')
        return value


class CardSerializer(serializers.ModelSerializer):
    """卡密序列化器（用于订单返回）。"""

    class Meta:
        model = Card
        fields = ['card_number', 'card_password']


class OrderDetailSerializer(serializers.ModelSerializer):
    """订单详情序列化器。"""

    product_name = serializers.CharField(source='product.name', read_only=True)
    cards = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_no', 'product', 'product_name', 'quantity', 'total_price',
            'contact', 'remark', 'status', 'created_at', 'paid_at', 'completed_at', 'cards'
        ]
        read_only_fields = fields

    def get_cards(self, obj):
        """获取订单关联的卡密列表。"""
        cards = Card.objects.filter(order_cards__order=obj).values('card_number', 'card_password')
        return [f"{c['card_number']}" + (f" / {c['card_password']}" if c['card_password'] else '') for c in cards]


class OrderListSerializer(serializers.ModelSerializer):
    """订单列表序列化器。"""

    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_no', 'product', 'product_name', 'quantity', 'total_price', 'status', 'created_at']
        read_only_fields = fields

