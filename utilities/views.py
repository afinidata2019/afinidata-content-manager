from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.views.generic import View
import re
from datetime import datetime
from dateutil.parser import parse
from dateutil import relativedelta
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
