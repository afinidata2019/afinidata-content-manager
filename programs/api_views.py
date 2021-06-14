from rest_framework import viewsets, permissions, filters
from programs import models, serializers
from django.db.models import Q
from django.utils.decorators import method_decorator


class ProgramViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Program.objects.all()
    serializer_class = serializers.ProgramSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ('name', 'description')
    ordering_fields = ['name', 'description']


    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.query_params.get('options'):
            pagination_class = None
            
        if self.request.query_params.get('id'):
            return qs.filter(id=self.request.query_params.get('id'))
        
        return qs.order_by('-id')

    def list(self, request, *args, **kwargs):
        return super(ProgramViewSet, self).list(request, *args, **kwargs)


# 
class AttributeTypeViewSet(viewsets.ModelViewSet):
    queryset = models.AttributeType.objects.all().order_by('-program')
    serializer_class = serializers.AttributeTypeSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        if(self.request.query_params.get('detail') and self.request.query_params.get('detail') == 'true'):
            self.serializer_class = serializers.DetailedAttributeTypeSerializer
        
        if self.request.query_params.get('id'):
            return qs.filter(id=self.request.query_params.get('id'))

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

        if(self.request.query_params.get('detail') and self.request.query_params.get('detail') == 'true'):
            self.serializer_class = serializers.DetailedAttributesSerializer

        if self.request.query_params.get('id'):
            return qs.filter(id=self.request.query_params.get('id'))

        if self.request.query_params.get('attribute_type'):
            return qs.filter(attribute_type=self.request.query_params.get('attribute_type'))

        return qs

    def list(self, request, *args, **kwargs):
        return super(AttributesViewSet, self).list(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return super(AttributesViewSet, self).update(request, *args, **kwargs)
