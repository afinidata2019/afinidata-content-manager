from rest_framework import viewsets, permissions
from programs import models, serializers
from django.utils.decorators import method_decorator


class ProgramViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Program.objects.all()
    serializer_class = serializers.ProgramSerializer

    def list(self, request, *args, **kwargs):
        return super(ProgramViewSet, self).list(request, *args, **kwargs)


class AttributeTypeViewSet(viewsets.ModelViewSet):
    queryset = models.AttributeType.objects.all()
    serializer_class = serializers.AttributeTypeSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('program'):
            return qs.filter(program=self.request.query_params.get('program'))
        return qs

    def list(self, request, *args, **kwargs):
        return super(AttributeTypeViewSet, self).list(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return super(AttributeTypeViewSet, self).update(request, *args, **kwargs)


class AttributesViewSet(viewsets.ModelViewSet):
    queryset = models.Attributes.objects.all()
    serializer_class = serializers.AttributesSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('attribute_type'):
            return qs.filter(attribute_type=self.request.query_params.get('attribute_type'))
        return qs

    def list(self, request, *args, **kwargs):
        return super(AttributesViewSet, self).list(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return super(AttributesViewSet, self).update(request, *args, **kwargs)
