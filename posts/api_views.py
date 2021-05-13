from django.core.exceptions import MultipleObjectsReturned
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from posts import models, serializers


class Pagination(PageNumberPagination):
    page_size = 100
    page_query_param = 'pagenumber'


class PostIntentViewSet(viewsets.ModelViewSet):

    queryset = models.Intent.objects.all()
    serializer_class = serializers.IntentPostSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['=id', '=intent_id']
    pagination_class = Pagination

    def get_queryset(self):

        qs = super().get_queryset()

        if self.request.query_params.get('id'):
            qs = qs.filter(id=self.request.query_params.get('id'))

        if self.request.query_params.get('post_id'):
            qs = qs.filter(post__id=self.request.query_params.get('post_id'))

        if self.request.query_params.get('intent_id'):
            qs = qs.filter(intent_id=self.request.query_params.get('intent_id'))

        if self.request.query_params.get('exclude_intent'):
            qs = qs.exclude(intent_id=self.request.query_params.get('exclude_intent'))

        return qs.order_by('-id')

    def create(self, request, pk=None):
        if 'intent_id' not in request.data or 'post' not in request.data:
            return Response({'request_status':500, 'error':'wrong parameters'})

        post = get_object_or_404(models.Post, pk=request.data['post'])
        
        try:
            intent, created = models.Intent.objects.get_or_create(post=post, intent_id=request.data['intent_id'])
        except MultipleObjectsReturned:
            intents = models.Intent.objects.filter(post=post, intent_id=request.data['intent_id'])
            intent = intents.first()
            intents.exclude(id=intent.id).delete()

        serializer = serializer.IntentSerializer(intent)
        return Response(serializer.data)


