import json
import os
import requests
import urllib.parse
from django.db.models import F, Count, Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST

from entities.models import Entity
from instances.models import AttributeValue
from messenger_users.models import UserData
from user_sessions import models, serializers, forms

import logging
logger = logging.getLogger(__name__)


class Pagination(PageNumberPagination):
    page_size = 25
    page_query_param = 'page'

    def __init__(self, page_size = False, page_query_param = False):  
        if page_size:
            self.page_size = page_size
        if page_query_param:
            self.page_query_param = page_query_param


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Session.objects.all().order_by('-id')
    serializer_class = serializers.SessionSerializer
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('id'):
            return qs.filter(id=self.request.query_params.get('id'))
        return qs

    def list(self, request, *args, **kwargs):
        return super(SessionViewSet, self).list(request, *args, **kwargs)

        
class SessionsRepliesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Reply.objects.all()
    serializer_class = serializers.ReplySerializer
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('id'):
            return qs.filter(id=self.request.query_params.get('id'))

        if self.request.query_params.get('label'):
            self.serializer_class = serializers.ReplyLabelSerializer
            label = urllib.parse.unquote(self.request.query_params.get('label'))
            qs = qs.filter(label__iexact=label)

        return qs.order_by('-id')


class BotSessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.BotSessions.objects.all().order_by('-id')
    serializer_class = serializers.BotSessionsSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('id'):
            return qs.filter(id=self.request.query_params.get('id'))

        if self.request.query_params.get('bot_id'):
            qs = qs.filter(bot_id=self.request.query_params.get('bot_id'))

        if self.request.query_params.get('session_type'):
            qs = qs.filter(session_type=self.request.query_params.get('session_type'))

        return qs


class InteractionViewSet(viewsets.ModelViewSet):
    queryset = models.Interaction.objects.all()
    serializer_class = serializers.InteractionSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['=id', '=field__id','text', 'user__first_name', 'user__last_name']
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('id'):
            return qs.filter(id=self.request.query_params.get('id'))

        return qs.order_by('-id')

    @action(methods=['GET'], detail=False)
    def get_unrecognized(self, request, pk=None):
        # only unrecognized interactions 
        queryset = super().get_queryset().filter(type='quick_reply').exclude(text__isnull=True)\
                                         .exclude(field__isnull=True).exclude(text__contains='(NLU-ignore)')\
                                         .exclude(text__contains='(NLU-intent)')
        
        # only interactions that have replies text is not among any labels
        queryset = queryset.annotate(replies=Count('field__reply__id')).exclude(replies__lt=1)
        queryset = queryset.annotate(valid=Count('field__reply__id', filter=Q(text=F('field__reply__label')))).exclude(valid__gt=0)

        # search filter
        queryset =  self.filter_queryset(queryset).order_by('-created_at')
        
        # Pagination
        pagination = Pagination(page_size = 10)
        qs = pagination.paginate_queryset(queryset, request)
        
        serializer = serializers.InteractionReplySerializer(qs, many=True)
        return pagination.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False)
    def unrecognized(self, request, *args, **kwargs):
        if 'id' not in request.GET:
            return Response(dict(error='wrong parameters'))

        interaction = get_object_or_404(models.Interaction, id=request.GET['id'])
        serializer = serializers.InteractionReplyCorrectionSerializer(interaction)
        return Response(dict(result=serializer.data))

    @action(methods=['POST'], detail=False)
    def correct_unrecognized(self, request, *args, **kwargs):
        try:
            data = request.POST.dict() if len(request.POST) > 0 else json.loads(request.body)
            form = forms.InteractionCorrectForm(data)
            if not form.is_valid():
                return Response({'Fail': form.errors}, status=HTTP_400_BAD_REQUEST)

            data = form.cleaned_data
            interaction = data['interaction']
            new_text = interaction.text
            
            #fetch all quick reply interactions that have the same text and do not match any label
            all_interactions = models.Interaction.objects.filter(type='quick_reply', text=interaction.text)\
                                                         .exclude(text__contains='(NLU-ignore)').exclude(text__contains='(NLU-intent)')
            all_interactions = all_interactions.annotate(valid=Count('field__reply__id', filter=Q(text=F('field__reply__label'))))\
                                                        .exclude(valid__gt=0)

            if data['ignore']:
                new_text += ' (NLU-ignore)'
                # since it might be just a test or an especific case, we search only for this field
                all_interactions = all_interactions.filter(field=interaction.field)
            else:
                # update values for the NLU
                try:
                    if data['intent']:
                        new_text += ' (NLU-intent)'
                        service_url = '{0}/trainingtext/'.format(os.getenv('NLU_API'))
                        requests.post(service_url, json=dict(text=interaction.text, intent=[data['intent']])) 
                    
                    elif data['reply']:
                        new_text = data['reply'].label
                        service_url = '{0}/quick_replies_trainingtext/'.format(os.getenv('NLU_API'))
                        requests.post(service_url, json=dict(quick_reply=data['reply'].label, text=interaction.text))

                        # correct attribute saved in user or instance
                        if data['reply'].attribute:
                            attribute = data['reply'].attribute
                            user_attribute = attribute.entity_set.all().filter(id__in=[4,5]).exists()
                            instance_attribute = attribute.entity_set.all().filter(id__in=[1,2]).exists()
                            
                            # since the same text might have been entered for a different quickreply
                            # which might have different attribute and value associated, we search only for this field
                            all_interactions = all_interactions.filter(field=interaction.field)
                            for i in all_interactions:
                                if i.user and user_attribute:
                                    UserData.objects.create(user_id=i.user.id,
                                                            attribute_id=attribute.id,
                                                            data_key=attribute.name,
                                                            data_value=data['reply'].value)
                                
                                if i.instance and instance_attribute:
                                    AttributeValue.objects.create(instance_id=i.instance.id,
                                                                attribute_id=attribute.id,
                                                                value=data['reply'].value)

                except Exception as e:
                    pass

            # correct text
            all_interactions.update(text=new_text)
            
            return Response({'Success': True})
        except Exception as e:
            return Response({'Fail': str(e)}, status=HTTP_500_INTERNAL_SERVER_ERROR)
