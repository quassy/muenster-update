from rest_framework.pagination import PageNumberPagination


class PageNumberAndSizePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "limit"

    def get_paginated_response_schema(self, schema):
        response_schema = super().get_paginated_response_schema(schema)
        # Rest Framework marks count and results as required since 3.15,
        # keep the schema (and the generated frontend client) as before
        response_schema.pop("required", None)
        return response_schema
