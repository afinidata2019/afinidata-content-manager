from datetime import datetime, timedelta, time
from django.db.models import Q
from rest_framework import viewsets, filters
from rest_framework.decorators import action
# from rest_framework.response import Response
# from django.utils.decorators import method_decorator
from rest_framework.pagination import PageNumberPagination
# from rest_framework import filters

from attributes.models import Attribute
from groups.models import ProgramAssignation, AssignationMessengerUser
from instances import models, serializers
from instances.models import AttributeValue
from messenger_users.models import User, UserData
from messenger_users.serializers import InstanceDetailSerializer
from utilities.views import PeopleFilterSearch


class InstanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Instance.objects.all().order_by('id')
    serializer_class = serializers.InstanceSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['=id', 'name']

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('id'):
            return qs.filter(id=self.request.query_params.get('id'))

        if self.request.query_params.get('user_id'):
            instances = models.InstanceAssociationUser.objects.values_list('instance', flat=True).all().filter(
                user=self.request.query_params.get('user_id'))

            if not instances:
                return []

            return qs.filter(id__in=instances)

        return qs

    @action(methods=['GET'], detail=True)
    def get_possible_values(self, request, pk=None):
        queryset = AttributeValue.objects.filter(attribute_id=pk).values('value').distinct()
        pagination = PageNumberPagination()
        pagination.page_size = 10
        pagination.page_query_param = 'pagenumber'
        qs = pagination.paginate_queryset(queryset, request)
        serializer = serializers.AttributeValueFilterPosibleVal(qs, many=True)
        return pagination.get_paginated_response(serializer.data)

    @action(methods=['POST'], detail=False)
    def advance_search(self, request):
        queryset = super().get_queryset()
        filtros = request.data['filtros']
        next_connector = None
        apply_filters = Q()
        
        people_search = PeopleFilterSearch()

        for idx, f in enumerate(filtros):
            data_key = f['data_key']
            value = f['data_value']
            condition = f['condition']
            search_by = f['search_by']
            check_attribute_type = 'USER'

            if search_by == 'attribute':
                attribute = Attribute.objects.get(pk=data_key)
                is_exact = attribute.type in ['numeric', 'category']

                # check if attribute belongs to user or instance, Priority to INSTANCES
                if attribute.entity_set.filter(id__in=[1, 2]).exists():
                    check_attribute_type = 'INSTANCE'

                if condition == 'is_set' or condition == 'not_set':
                    if condition == 'is_set':
                        # validar is set attribute
                        if check_attribute_type == 'USER':
                            users = User.objects.filter(Q(userdata__attribute_id=data_key))
                            q = Q(instanceassociationuser__user_id__in=users)
                            apply_filters = people_search.apply_connector(next_connector, apply_filters, q)
                        else:
                            q = Q(attributevalue__attribute_id=data_key)
                            apply_filters = people_search.apply_connector(next_connector, apply_filters, q)

                    if condition == 'not_set':
                        # validar not set attribute
                        if check_attribute_type == 'USER':
                            users = User.objects.filter(~Q(userdata__attribute_id=data_key))
                            q = Q(instanceassociationuser__user_id__in=users)
                            apply_filters = people_search.apply_connector(next_connector, apply_filters, q)
                        else:
                            q = ~Q(attributevalue__attribute_id=data_key)
                            apply_filters = people_search.apply_connector(next_connector, apply_filters, q)
                else:

                    if check_attribute_type == 'USER':
                        # filter by attribute user
                        last_attributes = people_search.get_last_attributes(data_key, model=UserData, type_id='user_id')

                        s = people_search.apply_filter('userdata__data_value', value, condition, exact=is_exact)
                        s = s & Q(userdata__id__in=last_attributes)
                        query_search = list(User.objects.filter(s).values_list('id',flat=True))
                        query = Q(instanceassociationuser__user_id__in=query_search)
                    else:
                        # filter by attribute instance
                        last_attributes = people_search.get_last_attributes(data_key, model=models.AttributeValue, type_id='instance_id')

                        query_search = people_search.apply_filter('attributevalue__value', value, condition, exact=is_exact)
                        query = query_search & Q(attributevalue__id__in=last_attributes)
                        
                    apply_filters = people_search.apply_connector(next_connector, apply_filters, query)

            elif search_by == 'bot':
                condition = condition if condition == 'is' else 'is_not'
                s = people_search.apply_filter('user__bot_id', value, condition, exact=True)
                qs = AssignationMessengerUser.objects.filter(s).values_list('user_id', flat=True).exclude(user_id__isnull=True).distinct()
                query = Q(instanceassociationuser__user_id__in=list(qs))
                apply_filters = people_search.apply_connector(next_connector, apply_filters, query)
            
            elif search_by == 'channel':
                # filter by channel
                s = people_search.apply_filter('channel_id', value, condition)
                qs = User.objects.filter(s).order_by('-id').values_list('id', flat=True)
                query = Q(instanceassociationuser__user_id__in=list(qs))
                apply_filters = people_search.apply_connector(next_connector, apply_filters, query)
            
            elif search_by == 'dates':
                # filter by dates
                date_from = datetime.combine(datetime.strptime(f['date_from'], '%Y-%m-%d'), time.min) - timedelta(days=1)
                date_to = datetime.combine(datetime.strptime(f['date_to'], '%Y-%m-%d'), time.max) - timedelta(days=1)
                if date_from and date_to:
                    if data_key == 'created_at':
                        queryset = queryset.filter(created_at__gte=date_from, created_at__lte=date_to)

            elif search_by == 'group':
                # filter by group
                s = people_search.apply_filter('group__id', value, condition, exact=True)
                qs = AssignationMessengerUser.objects.filter(s).values_list('user_id', flat=True).exclude(user_id__isnull=True).distinct()
                queryset = Q(instanceassociationuser__user_id__in=list(qs))
                apply_filters = people_search.apply_connector(next_connector, apply_filters, queryset)

            elif search_by == 'program':
                # filter by program
                s = people_search.apply_filter('program__id', value, condition, exact=True)
                qs = ProgramAssignation.objects.filter(s).values_list('user_id', flat=True).exclude(user_id__isnull=True)
                queryset = Q(instanceassociationuser__user_id__in=list(qs))
                apply_filters = people_search.apply_connector(next_connector, apply_filters, queryset)

            elif search_by == 'sequence':
                queryset = people_search.by_sequence(models.Instance, 'instanceassociationuser__user__id', next_connector, value, condition, queryset)
                if isinstance(queryset, bool):
                    return Response({'message':'subscribed API error'},status=HTTP_500_INTERNAL_SERVER_ERROR)
            
            next_connector = f['connector']

        if request.query_params.get('search'):
            # string search on datatable
            filter_search = Q()
            params = ['id', 'name']

            for x in params:
                filter_search |= Q(**{f"{x}__icontains": self.request.query_params.get('search')})
            queryset = queryset.filter(filter_search)

        queryset = queryset.filter(apply_filters)
        pagination = PageNumberPagination()
        qs = pagination.paginate_queryset(queryset, request)
        serializer = InstanceDetailSerializer(qs, many=True)
        return pagination.get_paginated_response(serializer.data)


class InstancesAttributeViewSet(viewsets.ModelViewSet):
    queryset = models.AttributeValue.objects.all().order_by('id')
    filter_backends = [filters.SearchFilter]
    search_fields = ("$attribute__name", "$value")

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.AttributeValueListSerializer

        return serializers.AttributeValueSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('id'):
            return qs.filter(id=self.request.query_params.get('id'))

        if self.request.query_params.get('attribute_id'):
            return qs.filter(attribute_id=self.request.query_params.get('attribute_id'))

        if self.request.query_params.get('instance_id'):
            return qs.filter(instance_id=self.request.query_params.get('instance_id'))

        return qs
