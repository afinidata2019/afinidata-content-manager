from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework.decorators import api_view
from rest_framework_bulk import (
    BulkListSerializer,
    BulkSerializerMixin,
    ListBulkCreateAPIView,
)
from messenger_users.models import User, Child, ChildData, UserData, Referral, UserActivity
from django.utils.decorators import method_decorator
from posts.models import Interaction
from .serializers import UserDataSerializer, UserSerializer, ChildSerializer, ChildDataSerializer
from rest_framework import viewsets
from django.http import JsonResponse, Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.defaultfilters import slugify
from django.db import connections
from django.db.models import Count
from licences.models import License
from languages.models import Language
from entities.models import Entity
from attributes.models import Attribute
from bots.models import UserInteraction as BotInteraction
from dateutil.relativedelta import relativedelta


import logging
logger = logging.getLogger(__name__)

## FIXME: convert to django rest views.


@csrf_exempt
def new_user(request):
    '''Creates user from a request.'''

    if request.method != 'POST':
        logger.error("New user only POST valid.")
        raise Http404('Not auth')

    ### TODO: Split in functions, should be named smth like refresh session (?)

    try:
        mess_id = request.POST['messenger_user_id']
        logger.info('attempting fetch for user id: {}'.format(mess_id))
        try:
            found_user = User.objects.get(last_channel_id=mess_id)
            logger.info('user id found')
            return JsonResponse(dict(
                set_attributes=dict(
                    hasLoggedIn=True,
                    username=found_user.username,
                    user_id=found_user.id
                ),
                messages=[]
            ))
        except User.DoesNotExist:
            logger.warning('user could not be found from user id given')

            logger.info('Creating New User')
            user = dict(bot_id=None, last_channel_id=None, backup_key=None, entity=None, license=None, language=None)

            fname = request.POST.get('first_name', "no{}".format(mess_id))[:20]
            lname = request.POST.get('last_name', "no{}".format(mess_id))[:20]

            user['last_channel_id'] = mess_id

            uname = slugify(fname + lname)+mess_id[-8::]
            user['username'] = uname
            user['backup_key'] = uname[:50]
            user['bot_id'] = request.POST['bot_id']
            user_to_save = User(**user)
            user_to_save.entity = Entity.objects.get(id=4)
            user_to_save.license = License.objects.get(id=1)
            user_to_save.language = Language.objects.get(id=1)
            user_to_save.save()
            UserData.objects.create(user=user_to_save, data_key='channel_first_name', data_value=fname,
                                    attribute=Attribute.objects.get(name='channel_first_name'))
            UserData.objects.create(user=user_to_save, data_key='channel_last_name', data_value=lname,
                                    attribute=Attribute.objects.get(name='channel_last_name'))

            logger.info("Created user")
            logger.info(user_to_save)

            return JsonResponse(dict(
                set_attributes=dict(
                    username=user_to_save.username,
                    backup_key=user['backup_key'],
                    user_id=user_to_save.pk
                ),
                messages=[]
            ))

    except MultiValueDictKeyError:
        logger.error("impossible to get without argument messenger_user_id")
        logger.error("post data includes: {}".format(request.POST))

        return 500


@csrf_exempt
def add_attribute(request, channel_id):

    users = User.objects.filter(channel_id=channel_id)
    user = None
    if users:
        user = users[0]
    else:
        users = User.objects.filter(last_channel_id=channel_id)
        if users:
            user = users[0]

    if request.method == 'POST':
        if not user:
            return JsonResponse(dict(status="error", error="User not exists with channel id: {}".format(channel_id)))
        else:
            results = []
            for param in request.POST:
                attribute = Attribute.objects.filter(name=str(param))
                if attribute.exists():
                    UserData.objects.create(
                        user=user,
                        data_key=str(param),
                        attribute=attribute.first(),
                        data_value=str(request.POST[param])
                    )
                else:
                    UserData.objects.create(
                        user=user,
                        data_key=str(param),
                        data_value=str(request.POST[param])
                    )
                results.append(dict(attribute=param, value=request.POST[param]))
            print(request.POST)
            return JsonResponse(dict(status="finished", data=dict(user_id=user.pk, added_attributes=results)))
    else:
        return JsonResponse(dict(hello='world'))


@csrf_exempt
def last_interacted(request, id=None):
    def fetch_interactionz(cursor):
        "Return all rows from a cursor as a dict"
        columns = [col[0] for col in cursor.description]
        intz = {}
        roz = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        for r in roz:
            kval = r['type']+"_last_h"
            intz[kval] = str(r["last"])

        return intz

    def get_user(r_dict):
        usr = None
        uname = r_dict.get('username')
        if not uname:
            usr = User.objects.get(id=int(id))
        else:
            usr = User.objects.get(username=uname)
        return usr

    user = get_user(request.POST)

    interact_type = request.POST.get("interaction_type")
    if interact_type:
        i = Interaction.objects.order_by("-created_at").get(user_id=user.pk, type=interact_type)
        time = i.created_at
        return JsonResponse(dict(set_attributes=dict(interaction_type=interact_type), messages=[]))

    with connections['default'].cursor() as cursor:
        cursor.execute("SELECT type, TIMESTAMPDIFF(HOUR, MAX(created_at), NOW()) last FROM CM_BD.posts_interaction"
                       " WHERE user_id = %s GROUP BY type ORDER BY created_at desc ;", [user.id])
        results = fetch_interactionz(cursor)
        return JsonResponse(dict(set_attributes=results,
                                 messages=[]))

    return JsonResponse(dict(status="error"))





@csrf_exempt
def by_username(request, username):
    logger.info("running by_username")
    if request.method != 'POST':
        return JsonResponse(dict(status='error', error='Invalid method'))

    try:
        user = User.objects.get(username=username)
        logger.warning("user found: {}", format(user))

        attrs = dict(
            set_attributes=dict(
                user_id=user.pk
            ),
            messages=[]
        )
        return JsonResponse(attrs)
    except Exception as e:
        logger.error("No username")
        return JsonResponse(dict(status='error', error=str(e)))


@csrf_exempt
def set_referral(request):
    """Makes a ref from a username and a ref value with user- prefixed username."""
    try:
        username = request.POST['username']
        ref = request.POST['ref']

        blacklist = ["ad id", "Welcome", "Greet", "Piecitos", "Email", "limitation"]

        for non_user in blacklist:
            if ref.startswith(non_user):
                logger.warning("ref user is not user value")
                return 200
                # return JsonResponse(dict(status='error', error="invalid_ref"))
        user = User.objects.get(username=username)
        ref_user = None

        if ref.startswith("ref-"):
            stripd_user = ref[4::]
            logger.info("attempt ref with ref prefix {}".format(stripd_user))
            ref_user = User.objects.get(username=stripd_user)
        if ref.startswith("user-"):
            stripd_user = ref[5::]
            logger.info("attempt ref with username prefix {}".format(stripd_user))
            ref_user = User.objects.get(username=stripd_user)
        else:
            logger.info("attempt ref without username prefix")
            ref_user = User.objects.get(username=ref)

        if not ref_user:
            return JsonResponse(dict(status='error', error="no-ref"))

        logger.info("user that referred obtained")

        ref_obj = Referral(user_shared=ref_user, user_opened=user, ref_type="ref")
        ref_obj.save()

        attrs = dict(
            set_attributes=dict(
                ref_id=ref_obj.pk
            ),
            messages=[]
        )
        return JsonResponse(attrs)
    except Exception as e:
        logger.exception("No username ")
        return JsonResponse(dict(status='error', error=str(e)))


@csrf_exempt
def get_referrals_count(request, username):
    try:
        user = User.objects.get(username=username)
        count = Referral.objects.filter(user_shared=user).count()

        attrs = dict(
            set_attributes=dict(
                ref_count=count
            ),
            messages=[]
        )
        return JsonResponse(attrs)

    except Exception as e:
        logger.exception("fail counting refs")
        return JsonResponse(dict(status='error', error=str(e)))


@csrf_exempt
def user_interaction(request):
    if request.method == 'GET':
        return JsonResponse(dict(status='error', error='Invalid method.'))
    value = 0
    ref_type = ''

    logger.info('setting interaction')

    try:
        ref_type = request.POST['interaction_type']
        username = request.POST['username']
        user = User.objects.get(username=username)
    except Exception as e:
        logger.error(e)
        return JsonResponse(dict(status='error', error='Invalid params.'))

    try:
        value = request.POST['value']
    except Exception as e:
        logger.warning("no value set")
        logger.warning(e)
        value = 0

    interaction = Interaction.objects.create(
        type=ref_type,
        channel_id=user.last_channel_id,
        username=user.username,
        user_id=user.pk,
        value=value
    )
    return JsonResponse(dict(status='done', data=dict(
        interaction=dict(
            id=interaction.pk
        )
    )))


class ChildViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Child.objects.all()
    serializer_class = ChildSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


@method_decorator(csrf_exempt, name='dispatch')
class UserDataViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = UserData.objects.all()
    serializer_class = UserDataSerializer

    def create(self, request):
        serializer = UserDataSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.get(id=request.data['user'])
            attribute = Attribute.objects.filter(name=str(request.data['data_key']))
            if attribute.exists():
                userdata = UserData.objects.create(user=user, data_key=request.data['data_key'],
                                                   attribute=attribute.first(), data_value=request.data['data_value'])
            else:
                userdata = UserData.objects.create(user=user, data_key=request.data['data_key'],
                                                   data_value=request.data['data_value'])
            if request.data['data_key'] == 'tipo_de_licencia':
                user.license = License.objects.get(name=request.data['data_value'])
                user.save()
            if request.data['data_key'] == 'language':
                user.language = Language.objects.get(name=request.data['data_value'])
                user.save()
            if request.data['data_key'] == 'user_type':
                user.entity = Entity.objects.get(name=request.data['data_value'])
                user.save()
            return JsonResponse({'userdata': userdata.pk, 'user': request.data['user'],
                                 'data_key': request.data['data_key'], 'data_value': request.data['data_value']})
        else:
            return JsonResponse(dict(status='error', error='Invalid params.'))


class ChildDataViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = ChildData.objects.all()
    serializer_class = ChildDataSerializer


@method_decorator(csrf_exempt, name='dispatch')
def get_last_action(request, user_id, *args, **kwargs):
    pass


@api_view(['POST'])
def set_user_action(request, user_id, action, *args, **kwargs):
    resp = dict()

    try:
        ua = UserActivity.objects.get(user_id=int(user_id))
    except UserActivity.DoesNotExist:
        logger.info("no machine for user, let's make one")
        ua = UserActivity(user_id=int(user_id))

    if hasattr(ua, action):
        transition_call = getattr(ua, action)
    else:
        logger.exception("error on setting action")
        return JsonResponse({"error": "invalid action"})

    if not callable(transition_call):
        return JsonResponse({"error": "invalid action call"})

    logger.info("calling")
    if len(request.POST) > 0:
        transition_call(**request.POST)
    else:
        transition_call()
    ua.save()

    resp['set_variable'] = ua.state
    return JsonResponse(resp)



@api_view()
def get_user_activity_status(request, user_id, *args, **kwargs):
    ua = UserActivity.objects.get(user_id=int(user_id))
    return JsonResponse({"status": ua.state})


class UserDataListSerializer(BulkSerializerMixin, UserDataSerializer):
    class Meta(object):
        model = UserData
        list_serializer_class = BulkListSerializer
        fields = '__all__'


class UserDataBulkView(ListBulkCreateAPIView):
    queryset = UserData.objects.all()
    serializer_class = UserDataListSerializer


@csrf_exempt
def child_interaction(request):
    pass


@csrf_exempt
def childId_from_user_Id(request, user_id):
    pass


@csrf_exempt
def user_last_interaction(request, user_id):
    if user_id:
        if 'interaction_type' in request.GET:
            qs = Interaction.objects.filter(user_id=user_id, type=request.GET['interaction_type']).order_by('-id')
            if qs.exists():
                r = qs.first()
                delta = timezone.now() - r.created_at
                r_prop = 'last_%s_interaction' % request.GET['interaction_type']
                return JsonResponse(dict(set_attributes={r_prop: delta.days}))
            else:
                return JsonResponse(dict(set_attributes={'request_error': 'User has not interaction %s' %
                                                                          request.GET['interaction_type']}))

    return JsonResponse(dict(set_attributes=dict(request_error='Invalid params')))
