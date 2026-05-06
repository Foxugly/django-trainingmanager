from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Default DRF pagination + client-tunable page_size.

    `?page_size=N` lets the frontend ask for fewer or more results per page
    (capped at `max_page_size`). Useful for views that need either small
    pages (calendar month, ~15 items) or larger pages (admin export, dump).
    """

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200
