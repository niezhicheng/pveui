"""通用分页器。

提供支持更大 page_size 的自定义分页器。
"""

from rest_framework.pagination import PageNumberPagination


class LargePageSizePagination(PageNumberPagination):
    """支持大页面大小的分页器。
    
    用于下拉选择等场景，需要一次性获取大量数据的接口。
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 10000  # 允许的最大页面大小


class StandardPagination(PageNumberPagination):
    """标准分页器。
    
    用于常规列表页面，限制最大页面大小以防止性能问题。
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100  # 标准最大页面大小

