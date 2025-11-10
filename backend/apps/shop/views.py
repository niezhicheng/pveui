"""发卡商城视图集。"""

import uuid
from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.utils import timezone
from apps.common.pagination import LargePageSizePagination
from .models import Product, Order, Card, OrderCard
from .serializers import (
    ProductSerializer,
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """商品视图集：只读（前台用户查看）。"""

    queryset = Product.objects.filter(is_active=True).order_by('sort_order', 'id')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]  # 允许匿名访问
    pagination_class = None  # 不分页


class OrderViewSet(viewsets.ModelViewSet):
    """订单视图集。"""

    queryset = Order.objects.all().order_by('-created_at')
    permission_classes = [AllowAny]  # 允许匿名访问
    pagination_class = LargePageSizePagination

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderListSerializer

    def create(self, request, *args, **kwargs):
        """创建订单并自动分配卡密。"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        contact = serializer.validated_data['contact']
        remark = serializer.validated_data.get('remark', '')

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({'detail': '商品不存在或已下架'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查库存
        available_cards = Card.objects.filter(product=product, is_sold=False)
        if available_cards.count() < quantity:
            return Response({'detail': f'库存不足，当前可用库存：{available_cards.count()}'}, status=status.HTTP_400_BAD_REQUEST)

        # 生成订单号
        order_no = f'ORD{datetime.now().strftime("%Y%m%d%H%M%S")}{uuid.uuid4().hex[:8].upper()}'
        total_price = product.price * quantity

        with transaction.atomic():
            # 创建订单
            order = Order.objects.create(
                order_no=order_no,
                product=product,
                quantity=quantity,
                total_price=total_price,
                contact=contact,
                remark=remark,
                status=Order.ORDER_STATUS_PAID,  # 假设自动支付成功
                paid_at=timezone.now(),
            )

            # 分配卡密
            cards_to_sell = available_cards[:quantity]
            card_list = []
            for card in cards_to_sell:
                card.is_sold = True
                card.sold_at = timezone.now()
                card.save()
                OrderCard.objects.create(order=order, card=card)
                card_list.append(f"{card.card_number}" + (f" / {card.card_password}" if card.card_password else ''))

            # 更新库存
            product.stock = available_cards.count() - quantity
            product.save()

            # 标记订单完成
            order.status = Order.ORDER_STATUS_COMPLETED
            order.completed_at = timezone.now()
            order.save()

        # 返回订单详情
        detail_serializer = OrderDetailSerializer(order)
        return Response({
            'success': True,
            'message': '订单创建成功',
            'data': {
                **detail_serializer.data,
                'cards': card_list,
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='query/(?P<order_no>[^/.]+)')
    def query(self, request, order_no=None):
        """根据订单号查询订单。"""
        try:
            order = Order.objects.get(order_no=order_no)
            serializer = OrderDetailSerializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response({'detail': '订单不存在'}, status=status.HTTP_404_NOT_FOUND)
