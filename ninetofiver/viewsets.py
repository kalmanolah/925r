from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response


class GenericHierarchicalReadOnlyViewSet(ReadOnlyModelViewSet):
    """
    API endpoint that allows models implementing model inheritance to be viewed.
    """
    serializer_classes = {}

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        data = page if page is not None else queryset

        # For each element of the resulting dataset, resolve to descendant model
        # and try to use the corresponding serializer to serialize.
        # If no serializers can be found, fall back to the default.
        for k, instance in enumerate(data):
            serializer_class = self._resolve_model_serializer(instance)

            x = serializer_class(instance, context={'request': request}).data
            data[k] = x

        if page is not None:
            return self.get_paginated_response(data)

        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer_class = self._resolve_model_serializer(instance)
        data = serializer_class(instance, context={'request': request}).data

        return Response(data)

    def _resolve_model_serializer(self, obj):
        """Attempt to find and return a serializer to use for a given model."""
        if obj.__class__ in self.serializer_classes:
            return self.serializer_classes[obj.__class__]

        return self.serializer_class
