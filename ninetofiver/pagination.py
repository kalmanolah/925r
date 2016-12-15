from rest_framework import pagination


class CustomizablePageNumberPagination(pagination.PageNumberPagination):

    """Page number pagination which allows for customization of page sizes."""

    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 1000
