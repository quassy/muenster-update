from django.utils import translation
from rest_framework.schemas.openapi import AutoSchema


class CamelizingAutoSchema(AutoSchema):
    # Via https://github.com/vbabiy/djangorestframework-camel-case/issues/79

    def get_operation(self, path, method):
        # Rest Framework translates the descriptions of its built-in
        # parameters (page, limit, id), keep them English like the rest of
        # the schema
        with translation.override("en"):
            return super().get_operation(path, method)

    def get_filter_parameters(self, path, method):
        # django-filter removed its schema generation, so build the query
        # parameters from the filterset like its former
        # DjangoFilterBackend.get_schema_operation_parameters did
        if not self.allows_filters(path, method):
            return []
        parameters = []
        for filter_backend in self.view.filter_backends:
            backend = filter_backend()
            if hasattr(backend, "get_schema_operation_parameters"):
                parameters += backend.get_schema_operation_parameters(
                    self.view
                )
                continue
            if not hasattr(backend, "get_filterset_class"):
                continue
            filterset_class = backend.get_filterset_class(
                self.view, self.view.get_queryset()
            )
            if filterset_class is None:
                continue
            for name, filter_ in filterset_class.base_filters.items():
                parameters.append(
                    {
                        "name": name,
                        "required": filter_.extra["required"],
                        "in": "query",
                        "description": str(
                            name if filter_.label is None else filter_.label
                        ),
                        "schema": {"type": "string"},
                    }
                )
        return parameters

    def map_serializer(self, serializer):
        result = super().map_serializer(serializer)
        camelized_properties = {
            self._to_camel_case(field_name): schema
            for field_name, schema in result["properties"].items()
        }
        new_result = {"type": "object", "properties": camelized_properties}
        new_result["required"] = list(
            map(self._to_camel_case, result.get("required", []))
        ) + [
            field
            for field, schema in new_result["properties"].items()
            if schema.get("readOnly")
        ]

        return new_result

    def _get_parameters(self, path, method):
        parameters = []
        parameters += self.get_path_parameters(path, method)
        parameters += self.get_pagination_parameters(path, method)
        parameters += self.get_filter_parameters(path, method)
        return [p["name"] for p in parameters]

    def get_responses(self, path, method):
        responses = super().get_responses(path, method)
        responses["200"]["description"] = "Success"
        # Rest Framework does not include error schemas (as their exception
        # handler is a simple view, not a serializer from which a schema could
        # be inferred)
        responses["400"] = {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            p: {"type": "array", "items": {"type": "string"}}
                            for p in self._get_parameters(path, method)
                        },
                    }
                }
            },
            "description": "Bad Request",
        }
        responses["404"] = {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"detail": {"type": "string"}},
                        "required": ["detail"],
                    }
                }
            },
            "description": "Not Found",
        }
        return responses
