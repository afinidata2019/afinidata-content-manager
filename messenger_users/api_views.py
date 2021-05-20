import json
import os
import re
import requests
import dateutil.parser
from datetime import datetime, timedelta, time
from django.db.models import Q, Exists, Prefetch
from django.db.models.aggregates import Max
from django.utils import timezone
from django.utils.decorators import method_decorator
from rest_framework import filters, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR

from messenger_users import models, serializers
from instances.models import Instance, AttributeValue as InstanceAttributeValue
from groups.models import ProgramAssignation, AssignationMessengerUser
from programs.models import Program
from attributes.models import Attribute
from utilities.views import PeopleFilterSearch


class UserViewSet(viewsets.ModelViewSet):
    queryset = models.User.objects.all().annotate(last_interaction=Max('userchannel__interaction__id')).order_by('-last_interaction')
    serializer_class = serializers.UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['=id', 'username', 'first_name', 'last_name', '=bot_id', '=channel_id', '$created_at']
    http_method_names = ['get', 'patch', 'options', 'head', 'post']

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('id'):
            return qs.filter(id=self.request.query_params.get('id'))

        return qs

    @action(methods=['GET'], detail=True)
    def get_possible_values(self, request, pk=None):
        queryset = models.UserData.objects.filter(attribute_id=pk).values('data_value').distinct()
        pagination = PageNumberPagination()
        pagination.page_size = 10
        pagination.page_query_param = 'pagenumber'
        qs = pagination.paginate_queryset(queryset, request)
        serializer = serializers.UserDataFilterPosibleVal(qs, many=True)
        return pagination.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False, url_path='last_seen', url_name='last_seen')
    def get_last_seen(self, request, *args, **kwgars):
        try:
            if 'user_channel_id' not in request.GET or 'bot_id' not in request.GET or 'bot_channel_id' not in request.GET:
                return Response({'request_status':400, 'error':'Wrong parameters'})

            user_channel = models.UserChannel.objects.filter(   bot_id=request.GET['bot_id'], 
                                                                bot_channel_id=request.GET['bot_channel_id'], 
                                                                user_channel_id=request.GET['user_channel_id'])

            if not user_channel.exists():
                return Response({'request_status':404, 'error':'Sender could not be found'})

            in_window = True if 'inwindow' in request.GET else False
            
            result = user_channel.last().get_last_user_message_date(check_window=in_window)
            
            return Response({'request_status':200, 'result':result})
        except Exception as err:
            return Response({'request_status':500, 'error':str(err)})

    @action(methods=['POST'], detail=False, url_path='update_interaction', url_name='update_interaction')
    def update_interaction(self, request, *args, **kwgars):
        try:
            if len(request.POST) > 0:
                data = request.POST.dict()
            else:
                data = json.loads(request.body)

            if ('user_channel_id' not in data or 'bot_id' not in data or 'bot_channel_id' not in data or
                'interactions' not in data or not data['interactions']):
                return Response({'request_status':400, 'error':'Wrong parameters'})

            user_channel = models.UserChannel.objects.filter(   bot_id=data['bot_id'], 
                                                                bot_channel_id=data['bot_channel_id'], 
                                                                user_channel_id=data['user_channel_id'])
            
            if user_channel.exists():
                for current_type in data['interactions']:
                    if current_type in ['user_message', 'reaction_interaction', 'referral_interaction',
                                        'postback_interaction']:
                        interaction_type = models.Interaction.LAST_USER_MESSAGE
                        user_channel.last().interaction_set.create(category=interaction_type)
                    elif current_type in ['channel_interaction', 'read_interaction', 'otn_interaction',
                                          'link_interaction']:
                        interaction_type = models.Interaction.LAST_CHANNEL_INTERACTION
                        user_channel.last().interaction_set.create(category=interaction_type)
                    else:
                        continue
                
                return Response({'request_status':200, 'updated': timezone.now()})

            return Response({'request_status':404, 'error':'user_channel could not be found'})
        
        except Exception as err:
            return Response({'request_status':500, 'error':str(err)})

    @action(methods=['POST'], detail=False)
    def advance_search(self, request):
        filtros = request.data['filtros']
        next_connector = None
        date_filter = Q()
        filter_search = Q()
        queryset = models.User.objects.all()
        people_search = PeopleFilterSearch()

        for idx, f in enumerate(filtros):
            data_key = f['data_key']
            value = f['data_value']
            condition = f['condition']
            search_by = f['search_by']
            check_attribute_type = 'INSTANCE'

            if search_by == 'attribute':
                attribute = Attribute.objects.get(pk=data_key)
                is_numeric = attribute.type == 'numeric'
                
                # check if attribute belongs to user or instance, Priority to USER
                if attribute.entity_set.filter(id__in=[4, 5]).exists():
                    check_attribute_type = 'USER'

                if condition == 'is_set' or condition == 'not_set':
                    if check_attribute_type == 'USER':
                        if condition == 'is_set':
                            # validar is set attribute
                            qs = models.User.objects.filter(userdata__attribute_id=data_key)
                            queryset = people_search.apply_connector(next_connector, queryset, qs)

                        if condition == 'not_set':
                            # validar not set attribute
                            qs = models.User.objects.exclude(userdata__attribute_id=data_key)
                            queryset = people_search.apply_connector(next_connector, queryset, qs)
                    else:
                        if condition == 'is_set':
                            qs = models.User.objects.filter(
                                instanceassociationuser__instance__attributevalue__attribute_id=data_key)

                        if condition == 'not_set':
                            qs = models.User.objects.exclude(
                                instanceassociationuser__instance__attributevalue__attribute_id=data_key)

                        queryset = people_search.apply_connector(next_connector, queryset, qs)

                else:
                    if check_attribute_type == 'INSTANCE':
                        # filter by attribute instance
                        last_attributes = people_search.get_last_attributes(data_key, model=InstanceAttributeValue, type_id='instance_id')
                        
                        s = Q(instanceassociationuser__instance__attributevalue__id__in=last_attributes) & \
                            people_search.apply_filter('instanceassociationuser__instance__attributevalue__value',
                                                        value, condition, numeric=is_numeric)
                    else:
                        # filter by attribute user
                        last_attributes = people_search.get_last_attributes(data_key, model=models.UserData, type_id='user_id')

                        s = Q(userdata__id__in=last_attributes) & \
                            people_search.apply_filter('userdata__data_value', value, condition, numeric=is_numeric)
                      
                    qs = models.User.objects.filter(s)
                    queryset = people_search.apply_connector(next_connector, queryset, qs)

            elif search_by == 'bot':
                condition = condition if condition == 'is' else 'is_not'
                s = people_search.apply_filter('bot_id', value, condition, numeric=True)
                qs = models.User.objects.filter(s)
                queryset = people_search.apply_connector(next_connector, queryset, qs)
            
            elif search_by == 'channel':
                # filter by channel
                s = people_search.apply_filter('userchannel__channel_id', value, condition, numeric=True)
                qs = models.User.objects.filter(s)
                queryset = people_search.apply_connector(next_connector, queryset, qs)
            
            elif search_by == 'dates':
                date_from = datetime.combine(datetime.strptime(f['date_from'], '%Y-%m-%d'), time.min) - timedelta(days=1)
                date_to = datetime.combine(datetime.strptime(f['date_to'], '%Y-%m-%d'), time.max) - timedelta(days=1)

                if date_from and date_to:
                    if data_key == 'created_at':
                        date_filter = Q(created_at__gte=date_from, created_at__lte=date_to)

                    if data_key == 'last_seen':
                        date_filter = Q(userchannel__interaction__created_at__gte=date_from,
                                        userchannel__interaction__created_at__lte=date_to)

                    if data_key == 'last_user_message':
                        date_filter = Q(userchannel__interaction__category=1,
                                        userchannel__interaction__created_at__gte=date_from,
                                        userchannel__interaction__created_at__lte=date_to)

                    if data_key == 'last_channel_interaction':
                        date_filter = Q(userchannel__interaction__category=2,
                                        userchannel__interaction__created_at__gte=date_from,
                                        userchannel__interaction__created_at__lte=date_to)

                if data_key == 'window':
                    date_filter = Q(userchannel__interaction__category=1,
                                    userchannel__interaction__created_at__gt=timezone.now() - timedelta(1))

            elif search_by == 'group':
                # filter by group and by parent group
                s = people_search.apply_filter('assignationmessengeruser__group_id', value, condition, numeric=True)
                s2 = people_search.apply_filter('assignationmessengeruser__group__parent_id',
                                                 value, condition, numeric=True)
                qs = models.User.objects.filter(s | s2)
                queryset = people_search.apply_connector(next_connector, queryset, qs)

            elif search_by == 'program':
                # filter by program
                s = people_search.apply_filter('assignationmessengeruser__group__programassignation__program_id',
                                                value, condition, numeric=True)
                qs = models.User.objects.filter(s)
                queryset = people_search.apply_connector(next_connector, queryset, qs)

            elif search_by == 'sequence':
                try:
                    url = "{0}/uhts/getSuscribedUsers/?sequence_id={1}".format(os.getenv('HOTTRIGGERS_API'), value)
                    response = requests.get(url).json()
                    suscribed_users = response['results'] if 'results' in response else list()
                    
                    if condition == 'is':
                        qs = models.User.objects.filter(id__in=suscribed_users)
                    else:
                        qs = models.User.objects.exclude(id__in=suscribed_users)
                    
                    queryset = people_search.apply_connector(next_connector, queryset, qs)
                except Exception as err:
                    return Response({'message':'subscribed API error'},status=HTTP_500_INTERNAL_SERVER_ERROR)

            next_connector = f['connector']

        if request.query_params.get("search"):
            # search by queryparams
            params = ['username','first_name','last_name','created_at']

            for x in params:
                filter_search |= Q(**{f"{x}__icontains": self.request.query_params.get('search')})
            if self.request.query_params.get('search').isnumeric():
                filter_search |= Q(id=self.request.query_params.get('search'))
                filter_search |= Q(bot_id=self.request.query_params.get('search'))
                filter_search |= Q(channel_id=self.request.query_params.get('search'))

        queryset = queryset.filter(date_filter).filter(filter_search).distinct()
        queryset = queryset.annotate(last_interaction=Max('userchannel__interaction__id')).order_by('-last_interaction')
        pagination = PageNumberPagination()
        qs = pagination.paginate_queryset(queryset, request)
        serializer = serializers.UserSerializer(qs, many=True)
        return pagination.get_paginated_response(serializer.data)

    @action(methods=['POST'], detail=False)
    def user_conversations(self, request):
        queryset = models.UserChannel.objects.all()

        # Filter by bot if necessary
        if request.query_params.get('bot_id'):
            queryset = queryset.filter(bot_id=self.request.query_params.get('bot_id')).distinct()
        
        if request.query_params.get('live_chat'):
            if self.request.query_params.get('live_chat').lower() == 'true':
                queryset = queryset.filter(live_chat=self.request.query_params.get('live_chat')).distinct()
            else:
                date = datetime.now() - timedelta(days=30)
                queryset = queryset.filter(livechat__created_at__gte=date).distinct()
       
        # Filter by name
        filter_search = Q()
        if request.query_params.get('search'):
            # search by queryparams
            params = ['user__username', 'user__first_name', 'user__last_name']
            for x in params:
                filter_search |= Q(**{f"{x}__icontains": self.request.query_params.get('search')})
            
            if self.request.query_params.get('search').isnumeric():
                filter_search |= Q(id=self.request.query_params.get('search'))
            queryset = queryset.filter(filter_search)
        
        queryset = queryset.annotate(last_user_message=Max('interaction__created_at', filter=Q(interaction__category=1)))
        queryset = queryset.annotate(last_channel_interaction=Max('interaction__created_at', filter=Q(interaction__category=2)))
        queryset = queryset.annotate(last_interaction=Max('interaction__created_at')).order_by('-last_interaction')
        
        pagination = PageNumberPagination()
        pagination.page_size = 20
        qs = pagination.paginate_queryset(queryset, request)
        
        serializer = serializers.UserChannelConversationSerializer(qs, many=True)
        return pagination.get_paginated_response(serializer.data)


class UserDataViewSet(viewsets.ModelViewSet):
    queryset = models.UserData.objects.all()
    serializer_class = serializers.UserDataSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ("$data_key", "$data_value")

    def paginate_queryset(self, queryset, view=None):

        if self.request.query_params.get('pagination') == 'off':
            return None

        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('id'):
            return qs.filter(id=self.request.query_params.get('id'))

        if self.request.query_params.get('user_id'):
            qs = qs.filter(user_id=self.request.query_params.get('user_id'))
            last_attributes = qs.values('attribute_id').annotate(max_id=Max('id'))
            qs = qs.filter(id__in=[x['max_id'] for x in last_attributes])

        if self.request.query_params.get('attribute_id'):
            qs = qs.filter(attribute_id=self.request.query_params.get('attribute_id'))

        if self.request.query_params.get('attribute_name'):
            qs = qs.filter(attribute__name=self.request.query_params.get('attribute_name'))

        return qs.order_by('-id')

    """
        return the value of the specific attribute
    """
    @action(methods=['GET'], detail=False, url_path='get_base_date', url_name='get_base_date')
    def base_date(self, request, *args, **kwgars):
        try:
            base_date = False
            qs = self.get_queryset()

            if qs.exists():
                base_date = qs.values_list('data_value', flat=True).first()
                try:
                    found = False
                    recognized_formats ={
                        '(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(\.\d+)?(?:Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])': '%Y-%m-%dT%H:%M:%S%Z',
                        '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?': '%Y-%m-%dT%H:%M:%S',
                        '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(\.\d+)?': '%Y-%m-%d %H:%M:%S',
                        '(\d{2})-(\d{2})-(\d{4})': '%d-%m-%Y',
                        '(\d{2})/(\d{2})/(\d{4})': '%d/%m/%Y',
                        '(\d{2})\.(\d{2})\.(\d{4})': '%d.%m.%Y'
                    }
                    
                    for pattern, date_format in recognized_formats.items():
                        match = re.search(pattern, base_date)
                        if match:
                            if date_format[-1].lower() == 'z':
                                base_date = dateutil.parser.isoparse(match.group())
                            else:
                                base_date = datetime.strptime(match.group(), date_format)
                            base_date = base_date.isoformat()
                            found = True
                            break

                    if found == False:
                       return Response({'ok':False, 'message':'value could not be parsed to datetime'})

                except ValueError:
                    return Response({'ok':False, 'message':'value could not be parsed to datetime'})

            return Response({'ok':True, 'base_date': base_date})
        except Exception as err:
            return Response({'ok':False, 'message':str(err)})

    # post parameters
    # required: user_id, attribute_name, value
    # optional: data_key, new (if true always creates a new entry)
    @action(methods=['POST'], detail=False, url_path='save_data', url_name='save_data')
    def save_data(self, request, *args, **kwgars):
        try:
            if len(request.POST) > 0:
                data = request.POST.dict()
            else:
                data = json.loads(request.body)

            if 'user_id' not in data and 'attribute_name' not in data and 'value' not in data:
                return Response({'request_status':500, 'error':'Wrong parameters'})
            
            # User must exist
            user = models.User.objects.all().filter(id=data['user_id'])
            if not user.exists():
                return Response({'request_status':404, 'error':'User not found'})
            
            user = user.last()
            
            data_key = data['data_key'] if 'data_key' in data else data['attribute_name']
            attribute, created = Attribute.objects.get_or_create(name=data['attribute_name'])
            user_data = models.UserData.objects.filter(user=user, attribute=attribute, data_key=data_key)

            if user_data.exists() and ('new' not in data or not data['new']):
                user_data = user_data.last()
                user_data.data_value = data['value']
                user_data.save()
            else:
                models.UserData.objects.create(user=user, attribute=attribute, data_key=data_key, data_value=data['value'])

            return Response({'request_status':200})
        except Exception as err:
            return Response({'request_status':500, 'error':str(err)})


class UserChannelSet(viewsets.ModelViewSet):
    queryset = models.UserChannel.objects.all().order_by('-id')
    serializer_class = serializers.UserChannelSerializer
    http_method_names = ['get', 'post', 'patch', 'options', 'head']

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.query_params.get('detail'):
            self.serializer_class = serializers.DetailedUserChannelSerializer

        if self.request.query_params.get('id'):
            return qs.filter(id=self.request.query_params.get('id'))

        if self.request.query_params.get('user_channel_id'):
            qs = qs.filter(user_channel_id=self.request.query_params.get('user_channel_id'))

        if self.request.query_params.get('bot_id'):
            qs = qs.filter(bot_id=self.request.query_params.get('bot_id'))

        if self.request.query_params.get('channel_id'):
            qs = qs.filter(channel_id=self.request.query_params.get('channel_id'))

        if self.request.query_params.get('bot_channel_id'):
            qs = qs.filter(bot_channel_id=self.request.query_params.get('bot_channel_id'))

        return qs

    def create(self, request, *args, **kwargs):
        created = super(UserChannelSet, self).create(request, *args, **kwargs)
        created_user_channel = models.UserChannel.objects.get(id=created.data['id'])
        created_user_channel.interaction_set.create(category=models.Interaction.LAST_USER_MESSAGE)
        created_user_channel.interaction_set.create(category=models.Interaction.LAST_CHANNEL_INTERACTION)
        return Response({'request_status': 'done', 'data': created.data})
