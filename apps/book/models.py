from django.db import models


from django.db import models
from apps.common.models import BaseAuditModel

class Book(BaseAuditModel):
    # 自动生成的业务模型
    # 说明：继承 BaseAuditModel，包含审计与归属字段（created_by/updated_by/owner_organization）。
    # 可按需调整字段、添加索引/约束，或补充 __str__/Meta 配置。
    title = models.CharField(max_length=128, verbose_name='书名')
    author = models.CharField(max_length=64, null=True, blank=True, verbose_name='作者')
    isbn = models.CharField(max_length=32, null=True, blank=True, unique=True, verbose_name='ISBN')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0, verbose_name='价格')
    published_date = models.DateField(null=True, blank=True, verbose_name='出版日期')
    is_available = models.BooleanField(null=True, blank=True, default=True, verbose_name='是否可借阅')

    class Meta:
        verbose_name = 'Book'
        verbose_name_plural = 'Book'

    def __str__(self) -> str:
        return str(self.title)
