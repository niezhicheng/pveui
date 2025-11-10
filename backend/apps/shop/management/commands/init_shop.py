"""初始化发卡网测试数据。

用法：
    python manage.py init_shop
    python manage.py init_shop --reset  # 删除现有数据后重新创建
"""

from django.core.management.base import BaseCommand
from apps.shop.models import Product, Card


class Command(BaseCommand):
    help = '初始化发卡网测试数据（商品、卡密）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='删除现有数据后重新创建（危险操作）',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('正在删除现有发卡网数据...'))
            Card.objects.all().delete()
            Product.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('已删除现有数据'))

        # 创建商品
        self.stdout.write('创建商品...')
        
        products_data = [
            {
                'name': 'Steam 游戏激活码',
                'description': 'Steam 平台游戏激活码，支持多款热门游戏',
                'price': 29.90,
                'stock': 0,  # 会根据卡密自动计算
                'is_active': True,
                'sort_order': 1,
            },
            {
                'name': 'Netflix 会员账号',
                'description': 'Netflix 高级会员账号，支持4K超清，有效期1个月',
                'price': 19.90,
                'stock': 0,
                'is_active': True,
                'sort_order': 2,
            },
            {
                'name': 'Spotify Premium 账号',
                'description': 'Spotify 高级会员账号，无广告，支持离线下载',
                'price': 15.90,
                'stock': 0,
                'is_active': True,
                'sort_order': 3,
            },
            {
                'name': 'ChatGPT Plus 账号',
                'description': 'ChatGPT Plus 会员账号，支持 GPT-4，有效期1个月',
                'price': 99.00,
                'stock': 0,
                'is_active': True,
                'sort_order': 4,
            },
            {
                'name': 'Adobe Creative Cloud 账号',
                'description': 'Adobe 创意云套件账号，包含 Photoshop、Premiere 等全套软件',
                'price': 199.00,
                'stock': 0,
                'is_active': True,
                'sort_order': 5,
            },
        ]

        products = []
        for p_data in products_data:
            product, created = Product.objects.get_or_create(
                name=p_data['name'],
                defaults=p_data
            )
            if not created:
                # 更新现有商品
                for key, value in p_data.items():
                    setattr(product, key, value)
                product.save()
            products.append(product)
            self.stdout.write(self.style.SUCCESS(f'  ✓ 商品: {product.name}'))

        # 为每个商品创建卡密
        self.stdout.write('创建卡密...')
        
        cards_data = {
            'Steam 游戏激活码': [
                ('STEAM-ABCD-EFGH-IJKL', ''),
                ('STEAM-MNOP-QRST-UVWX', ''),
                ('STEAM-YZ12-3456-7890', ''),
                ('STEAM-ABCD-1234-5678', ''),
                ('STEAM-EFGH-9012-3456', ''),
            ],
            'Netflix 会员账号': [
                ('netflix001@example.com', 'Pass123456'),
                ('netflix002@example.com', 'Pass123456'),
                ('netflix003@example.com', 'Pass123456'),
                ('netflix004@example.com', 'Pass123456'),
                ('netflix005@example.com', 'Pass123456'),
            ],
            'Spotify Premium 账号': [
                ('spotify001@example.com', 'Spotify123'),
                ('spotify002@example.com', 'Spotify123'),
                ('spotify003@example.com', 'Spotify123'),
                ('spotify004@example.com', 'Spotify123'),
                ('spotify005@example.com', 'Spotify123'),
            ],
            'ChatGPT Plus 账号': [
                ('chatgpt001@example.com', 'ChatGPT123'),
                ('chatgpt002@example.com', 'ChatGPT123'),
                ('chatgpt003@example.com', 'ChatGPT123'),
            ],
            'Adobe Creative Cloud 账号': [
                ('adobe001@example.com', 'Adobe123456'),
                ('adobe002@example.com', 'Adobe123456'),
            ],
        }

        total_cards = 0
        for product in products:
            if product.name in cards_data:
                for card_number, card_password in cards_data[product.name]:
                    card, created = Card.objects.get_or_create(
                        product=product,
                        card_number=card_number,
                        defaults={
                            'card_password': card_password,
                            'is_sold': False,
                        }
                    )
                    if created:
                        total_cards += 1

                # 更新商品库存
                product.stock = Card.objects.filter(product=product, is_sold=False).count()
                product.save()

        self.stdout.write(self.style.SUCCESS(f'  ✓ 创建卡密: {total_cards} 张'))

        self.stdout.write(self.style.SUCCESS('\n✅ 发卡网测试数据初始化完成！'))
        self.stdout.write(self.style.SUCCESS('💡 提示：访问 /shop 页面即可查看商品并测试购买功能'))

