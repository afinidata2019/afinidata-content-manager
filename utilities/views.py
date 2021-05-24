import os
import re
import requests
from datetime import datetime
from dateutil import relativedelta
from dateutil.parser import parse
from django.db.models import Q
from django.db.models.aggregates import Max
from django.http import JsonResponse, HttpResponse, Http404
from django.views.generic import View, UpdateView, CreateView
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.decorators import method_decorator
from requests.auth import HTTPBasicAuth

from articles.models import Interaction
from instances.models import Response
from messenger_users.models import User

import logging
logger = logging.getLogger(__name__)


@csrf_exempt
def check_valid_date(request):
    if request.method == 'GET':
        date = None

        try:
            date = request.GET['date']
        except Exception as e:
            logger.error('invalid date')
            return JsonResponse(dict(status='error', error='param date not defined'))

        new_date = parse(date)
        day = int(str(new_date)[8:10])
        if day > 12:
            UpdateChildDOB = 'no'
        else:
            UpdateChildDOB = 'si'

        result = re.match("[\d]{1,2}/[\d]{1,2}/[\d]{1,4}", request.GET['date'])
        second_result = re.match("[\d]{1,2}-[\d]{1,2}-[\d]{1,4}", request.GET['date'])
        if result or second_result:
            UpdateChildDOB = 'si'

        if UpdateChildDOB == 'si':
            update_date = parse(date, dayfirst=True)
        else:
            update_date = new_date

        return JsonResponse(dict(
            set_attributes=dict(
                UpdateChildDOB=UpdateChildDOB,
                UpdateChildDOBDate=update_date
            ),
            messages=[]
        ))


@csrf_exempt
def change_kids_date(request):

    if request.method == 'GET':

        first_value = None
        second_value = None
        comparative = None

        try:
            first_value = request.GET['childDOB']
            second_value = request.GET['UpdateChildDOBDate']
            comparative = request.GET['UpdateChildDOB']
        except:
            return JsonResponse(dict(status='error', error='invalid parameters'))

        if comparative == 'si':
            return JsonResponse(dict(
                set_attributes=dict(
                    childDOB=second_value,
                    DOBerroneo=first_value
                ),
                messages=[]
            ))
        else:
            return JsonResponse(dict(
                set_attributes=dict(),
                messages=[]
            ))


@csrf_exempt
def fix_date(request):
    if request.method == 'GET':
        date = None
        attr = None

        try:
            date = request.GET['date']
            attr = request.GET['attr']
        except:
            return JsonResponse(dict(status='error', error='not date or attr parameter'))

        ref_date = str(date)[0:10]
        new_date = ref_date[5:7] + '-' + ref_date[8:10] + '-' + ref_date[0:4]
        print(date)
        print(new_date)
        return_date = parse(new_date, dayfirst=True)

        return JsonResponse(dict(
            set_attributes={
                attr: return_date
            },
            messages=[]
        ))

@csrf_exempt
def validates_date(request):

    print(request)

    if request.method == 'GET':
        try:
            if request.GET['date']:
                result = re.match("[\d]{1,2}/[\d]{1,2}/[\d]{1,4}", request.GET['date'])
                second_result = re.match("[\d]{1,2}%2F[\d]{1,2}%2F[\d]{1,4}", request.GET['date'])
                print(request.GET['date'])

                if result:
                    print('first here')
                    split_date = request.GET['date'].split('/', 3)
                    day = int(split_date[0])
                    month = int(split_date[1])
                    year = int(split_date[2])

                    if \
                            not day <= 31 or \
                            not day > 0 or \
                            not month <= 12 or \
                            not month > 0 or \
                            not year >= 1900 or \
                            not year <= datetime.now().year:
                        print('not valid')
                        return JsonResponse(
                            dict(
                                set_attributes=dict(
                                    isDateValid=False
                                ),
                                messages=[]
                            )
                        )

                if second_result:
                    print('second here!')
                    split_date = request.GET['date'].split('%2F', 3)
                    print(request.GET['date'])
                    print(split_date)
                    day = int(split_date[0])
                    month = int(split_date[1])
                    year = int(split_date[2])
                    print(day, month, year)

                if result or second_result:
                    return JsonResponse(
                        dict(
                            set_attributes=dict(
                                isDateValid=True,
                                parentDOB=parse(request.GET['date'], dayfirst=True)
                            ),
                            messages=[]
                        )
                    )
                else:
                    print('not match')
                    return JsonResponse(
                        dict(
                            set_attributes=dict(
                                isDateValid=False
                            ),
                            messages=[]
                        )
                    )

        except Exception as e:
            return JsonResponse(
                dict(
                    set_attributes=dict(
                        isDateValid=False
                    ),
                    messages=[]
                )
            )


@csrf_exempt
def validates_kids_date(request):

    print(request)

    if request.method == 'GET':
        try:
            if request.GET['date']:
                result = re.match("[\d]{1,2}/[\d]{1,2}/[\d]{1,4}", request.GET['date'])
                second_result = re.match("[\d]{1,2}%2F[\d]{1,2}%2F[\d]{1,4}", request.GET['date'])
                print(request.GET['date'])

                if result:
                    print('first here')
                    split_date = request.GET['date'].split('/', 3)
                    day = int(split_date[0])
                    month = int(split_date[1])
                    year = int(split_date[2])

                    if \
                            not day <= 31 or \
                            not day > 0 or \
                            not month <= 12 or \
                            not month > 0 or \
                            not year >= datetime.now().year - 15 or \
                            not year <= datetime.now().year:
                        print('not valid')
                        return JsonResponse(
                            dict(
                                set_attributes=dict(
                                    isDateValid=False
                                ),
                                messages=[]
                            )
                        )
                    #also validate if date is future (not just next year but next months)
                    date = parse(request.GET['date'], dayfirst=True)
                    rel = relativedelta.relativedelta(datetime.now(), date)
                    child_months = (rel.years * 12) + rel.months
                    if child_months < 0:
                        return JsonResponse(
                            dict(
                                set_attributes=dict(
                                    isDateValid=False
                                ),
                                messages=[]
                            )
                        )

                if second_result:
                    print('second here!')
                    split_date = request.GET['date'].split('%2F', 3)
                    print(request.GET['date'])
                    print(split_date)
                    day = int(split_date[0])
                    month = int(split_date[1])
                    year = int(split_date[2])
                    print(day, month, year)

                if result or second_result:
                    return JsonResponse(
                        dict(
                            set_attributes=dict(
                                isDateValid=True,
                                childDOB=parse(request.GET['date'], dayfirst=True)
                            ),
                            messages=[]
                        )
                    )
                else:
                    print('not match')
                    return JsonResponse(
                        dict(
                            set_attributes=dict(
                                isDateValid=False
                            ),
                            messages=[]
                        )
                    )

        except Exception as e:
            return JsonResponse(
                dict(
                    set_attributes=dict(
                        isDateValid=False
                    ),
                    messages=[]
                )
            )


@csrf_exempt
def set_new_broadcast(request, broadcast_id, variable):

    return JsonResponse(
        dict(
            set_attributes={
                variable: int(broadcast_id) + 1
            },
            messages=[]
        )
    )


@csrf_exempt
def set_chatfuel_variable(request):

    if request.method == 'POST':
        return JsonResponse(dict(status='error', error='Invalid method.'))

    try:
        variable = request.GET['variable']
        value = request.GET['value']
    except Exception as e:
        return JsonResponse(dict(status='error', error=str(e)))

    return JsonResponse(dict(
        set_attributes={
            variable: value
        },
        messages=[]
    ))


@csrf_exempt
def get_user_id_by_username(request):

    if request.method == 'POST':
        return JsonResponse(dict(status='error', error='Invalid method.'))

    try:
        username = request.GET['username']
        user = User.objects.get(username=username)
    except Exception as e:
        return JsonResponse(dict(status='error', error='Invalid params.'))

    return JsonResponse(dict(
        set_attributes=dict(
            bot_user_id=user.pk
        ),
        messages=[]
    ))


@method_decorator(csrf_exempt, name='dispatch')
class GetMonthsView(View):

    def get(self, request, *args, **kwargs):
        try:
            date = parse(request.GET['date'], dayfirst=True)
            rel = relativedelta.relativedelta(datetime.now(), date)
            logger.info(rel)
            child_months = (rel.years * 12) + rel.months
            if child_months < 0:
                logger.warning("Child months calculated below 0")
            return JsonResponse(dict(set_attributes=dict(childMonths=child_months), messages=[]))
        except:
            logger.exception("Invalid Date")
            return JsonResponse(dict(set_attributes=dict(childMonthsError=True), messages=[]))


@method_decorator(csrf_exempt, name='dispatch')
class EnGetMonthsView(View):
    '''FIXME(ale)'''
    def get(self, request, *args, **kwargs):
        try:
            date = parse(request.GET['date'], dayfirst=False)
            rel = relativedelta.relativedelta(datetime.now(), date)
            logger.info(rel)
            child_months = (rel.years * 12) + rel.months
            if child_months < 0:
                logger.warning("Child months calculated below 0")
            return JsonResponse(dict(set_attributes=dict(childMonths=child_months), messages=[]))
        except:
            logger.exception("Invalid Date")
            return JsonResponse(dict(set_attributes=dict(childMonthsError=True), messages=[]))


@method_decorator(csrf_exempt, name='dispatch')
class AddMinuteForArticleInteraction(UpdateView):
    model = Interaction
    pk_url_kwarg = 'interaction_id'
    fields = ('value',)

    def form_valid(self, form):
        r = form.save()
        return JsonResponse(dict(request_status='done', request_id=r.pk))


@method_decorator(csrf_exempt, name='dispatch')
class CreateResponseView(CreateView):
    model = Response
    fields = ('instance', 'milestone', 'response')

    def form_valid(self, form):
        form.instance.created_at = datetime.now()
        register = form.save()
        return JsonResponse(dict(status='done', data=dict(milestone_id=register.milestone_id, register_id=register.pk,
                                                          response=register.response)))


@method_decorator(csrf_exempt, name='dispatch')
class CompleteTrialView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not Found')

    def post(self, request, *args, **kwargs):
        url = "%s/api/v1/experiments/trials/%s" % (os.getenv("RECOMMENDER_URL"), request.POST['trial'])
        req = requests.put(url=url, auth=HTTPBasicAuth(os.getenv('RECOMMENDER_USR'), os.getenv('RECOMMENDER_PSW')),
                           json=dict(id=request.POST['trial'], success='true', completed_at="%s" % timezone.now()),
                           headers={'Content-type': 'application/json', 'Accept': 'text/plain'})
        if req.status_code == 200:
            print(req.json())
            return JsonResponse(dict(status='done'))
        return JsonResponse(dict(status='error'))


class PeopleFilterSearch():
    
    def apply_connector(self, connector, filters, query):
        if connector is None:
            filters = query
        else:
            if connector == 'and':
                filters &= query
            else:
                filters |= query

        return filters

    def apply_filter(self, field, value, condition, exact=False):
        # apply condition to search
        if condition == 'is':
            if exact:
                query_search = Q(**{f"{field}": value})
            else:
                query_search = Q(**{f"{field}__icontains": value})
        elif condition == 'is_not':
            if exact:
                query_search = ~Q(**{f"{field}": value})
            else:
                query_search = ~Q(**{f"{field}__icontains": value})
        elif condition == 'startswith':
            if exact:
                query_search = Q(**{f"{field}": value})
            else:
                query_search = Q(**{f"{field}__startswith": value})
        elif condition == 'gt':
            query_search = Q(**{f"{field}__gt": value})
        elif condition == 'lt':
            query_search = Q(**{f"{field}__lt": value})
        
        return query_search

    def get_last_attributes(self, data_key, model, type_id):
        last_attributes = model.objects.filter(attribute_id=data_key)
        last_attributes = last_attributes.values(type_id, 'attribute_id').annotate(max_id=Max('id'))
        
        return list(last_attributes.values_list('max_id', flat=True).distinct())

    def by_sequence(self, model, model_field, next_connector, value, condition, queryset):
        try:
            active = 0 if condition in ['was', 'was_not'] else 1
            url = '{0}/uhts/getSuscribedUsers/?sequence_id={1}&active={2}'.format(os.getenv('HOTTRIGGERS_API'), value, active)
            response = requests.get(url).json()
            suscribed_users = response['results'] if 'results' in response else list()
            
            if active:
                qs = model.objects.filter(Q(**{f"{model_field}__in": suscribed_users}))
            else:
                qs = model.objects.exclude(Q(**{f"{model_field}__in": suscribed_users}))

            return self.apply_connector(next_connector, queryset, qs)
        except Exception as err:
            return False

