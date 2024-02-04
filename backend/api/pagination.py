from rest_framework.pagination import PageNumberPagination

from foodgram import constants


class PageLimitPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = constants.PAGE_SIZE
    max_page_size = constants.NAX_PAGE_SIZE
