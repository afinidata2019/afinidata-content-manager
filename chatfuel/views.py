from articles.models import Article, Interaction as ArticleInteraction, ArticleFeedback, Intent as ArticleIntent, Missing as MissingArticles
from attributes.models import Attribute
from bots.models import Interaction as BotInteraction, UserInteraction
from entities.models import Entity
from groups import forms as group_forms
from groups.models import Code, AssignationMessengerUser, Group, MilestoneRisk
from instances.models import InstanceAssociationUser, Instance, AttributeValue, PostInteraction, Response
from languages.models import Language, MilestoneTranslation
from licences.models import License
from messenger_users.models import User as MessengerUser, LiveChat, UserChannel
from messenger_users.models import User, UserData
from milestones.models import Milestone
from programs.models import Program, Attributes as ProgramAttributes
from user_sessions.models import Session, Interaction as SessionInteraction, Reply, Field, Lang
from django.utils import timezone
from django.utils.http import is_safe_url
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.db.models.aggregates import Max
from django.views.generic import View, CreateView, TemplateView, UpdateView
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, Http404
from requests.auth import HTTPBasicAuth
from dateutil import relativedelta, parser
from datetime import datetime, timedelta
from chatfuel import forms
import requests
import pytz
import json
import random
import boto3
import os
import re


''' MESSENGER USERS VIEWS '''


@method_decorator(csrf_exempt, name='dispatch')
class CreateMessengerUserView(CreateView):
    model = User
    form_class = forms.CreateUserForm

    def form_valid(self, form):
        group = None
        code = None
        if 'ref' in form.cleaned_data:
            # Si el ref es para reasignar al usuario (?ref=user_id_123456)
            if len(form.cleaned_data['ref']) > 8 and form.cleaned_data['ref'][:8] == 'user_id_':
                user_id = form.cleaned_data['ref'][8:]
                user = MessengerUser.objects.filter(id=user_id)
                if user.exists():
                    user = user.last()
                    for user_channel in UserChannel.objects.filter(user_channel_id=form.data['channel_id']):
                        user_channel.user = user
                        user_channel.save()
                    # Enviar al usuario a una session en especifico
                    save_json_attributes(dict(set_attributes=dict(session=898,
                                                                  position=0,
                                                                  reply_id=0,
                                                                  field_id=0,
                                                                  session_finish=False,
                                                                  save_user_input=False,
                                                                  save_text_reply=False)), None, user)
                    return JsonResponse(dict(set_attributes=dict(user_id=user.pk, request_status='done',
                                                                 username=user.username,
                                                                 service_name='Create User', user_reg='unregistered')))

            # Si el ref es para asignar a un grupo
            code_filter = Code.objects.filter(code=form.cleaned_data['ref'])
            if code_filter.exists():
                code = code_filter.first()
                group = code_filter.first().group
                print(group)

        form.instance.last_channel_id = form.data['channel_id']
        form.instance.username = form.data['channel_id']
        form.instance.backup_key = form.data['channel_id']
        user = form.save()
        user.entity = Entity.objects.get(id=4)  # Encargado
        user.license = License.objects.get(id=1)  # free
        user.language = Language.objects.get(id=1)  # es
        user.save()
        user.userdata_set.create(data_key='user_reg', data_value='unregistered', attribute_id='210')
        user.userdata_set.create(data_key='user_id', data_value=user.id, attribute_id='318')
        if group:
            exchange = AssignationMessengerUser.objects.create(messenger_user_id=user.pk, group=group,
                                                               user_id=user.pk, code=code)
            response = dict(set_attributes=dict(user_id=user.pk, request_status='done',
                                                username=user.username,
                                                service_name='Create User', user_reg='unregistered',
                                                request_code=code.code, request_code_group=group.name))
            if code.group.country:
                user.userdata_set.create(data_key='Pais', data_value=group.country,
                                         attribute_id=Attribute.objects.get(name='Pais').id)
                response['set_attributes']['Pais'] = group.country
            if code.group.region:
                user.userdata_set.create(data_key='Región', data_value=group.region,
                                         attribute_id=Attribute.objects.get(name='Región').id)
                response['set_attributes']['Región'] = group.region
            if group.license:
                user.license = group.license
                user.save()
            return JsonResponse(response)
        return JsonResponse(dict(set_attributes=dict(user_id=user.pk, request_status='done',
                                                     username=user.username,
                                                     service_name='Create User', user_reg='unregistered')))

    def form_invalid(self, form):
        user_set = User.objects.filter(channel_id=form.data['channel_id'])
        if user_set.exists():
            group = None
            code = None
            if 'ref' in form.cleaned_data:
                # Si el ref es para reasignar al usuario (?ref=user_id_123456)
                if len(form.cleaned_data['ref']) > 8 and form.cleaned_data['ref'][:8] == 'user_id_':
                    user_id = form.cleaned_data['ref'][8:]
                    user = MessengerUser.objects.filter(id=user_id)
                    if user.exists():
                        user = user.last()
                        for user_channel in UserChannel.objects.filter(user_channel_id=form.data['channel_id']):
                            user_channel.user = user
                            user_channel.save()
                            # Enviar al usuario a una session en especifico
                        save_json_attributes(dict(set_attributes=dict(session=898,
                                                                      position=0,
                                                                      reply_id=0,
                                                                      field_id=0,
                                                                      session_finish=False,
                                                                      save_user_input=False,
                                                                      save_text_reply=False)), None, user)
                        return JsonResponse(dict(set_attributes=dict(user_id=user.pk,
                                                                     username=user.username,
                                                                     request_status='error',
                                                                     request_error='User exists',
                                                                     service_name='Create User')))

                # Si el ref es para asignar a un grupo
                code_filter = Code.objects.filter(code=form.cleaned_data['ref'])
                if code_filter.exists():
                    code = code_filter.first()
                    group = code_filter.first().group
                    print(group)
            user = user_set.first()
            if group:
                assignations = AssignationMessengerUser.objects.filter(user_id=user.pk)
                print(assignations)
                for a in assignations:
                    a.delete()
                exchange = AssignationMessengerUser.objects.create(messenger_user_id=user.pk, group=group,
                                                                   user_id=user.pk, code=code)
                response = dict(set_attributes=dict(user_id=user.pk, request_status='done',
                                                    username=user.username,
                                                    service_name='Create User', user_reg='unregistered',
                                                    request_code=code.code, request_code_group=group.name))
                if code.group.country:
                    user.userdata_set.create(data_key='Pais', data_value=group.country,
                                             attribute_id=Attribute.objects.get(name='Pais').id)
                    response['set_attributes']['Pais'] = group.country
                if code.group.region:
                    user.userdata_set.create(data_key='Región', data_value=group.region,
                                             attribute_id=Attribute.objects.get(name='Región').id)
                    response['set_attributes']['Región'] = group.region
                if group.license:
                    user.license = group.license
                    user.save()
                return JsonResponse(response)
            return JsonResponse(dict(set_attributes=dict(user_id=user_set.last().pk,
                                                         username=user.username,
                                                         request_status='error', request_error='User exists',
                                                         service_name='Create User')))

        return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid params',
                                                     service_name='Create User')))


@method_decorator(csrf_exempt, name='dispatch')
class VerifyMessengerUserView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request):
        post_data = self.request.POST if len(self.request.POST) > 0 else json.loads(self.request.body)
        form = forms.MessengerUserForm(post_data)

        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='done', user_exist='false',
                                                         service_name='Verify User')))

        user = form.cleaned_data['user']

        return JsonResponse(dict(set_attributes=dict(request_status='done', user_exist='true', user_id=user.pk,
                                                     service_name='Verify User')))


@method_decorator(csrf_exempt, name='dispatch')
class ReplaceUserInfoView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request):
        post_data = self.request.POST if len(self.request.POST) > 0 else json.loads(self.request.body)
        form = forms.ReplaceUserForm(post_data)
        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Incomplete params.',
                                                         service_name='Replace Info User')))

        users = User.objects.filter(id=form.data['id'])
        if not users.count() > 0:
            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                         request_error='User with ID %s not exist.' % form.data['id'],
                                                         service_name='Replace Info User')))
        user = users.first()
        user.first_name = form.data['first_name']
        user.last_name = form.data['last_name']
        user.channel_id = form.data['channel_id']
        user.last_channel_id = form.data['channel_id']
        user.username = form.data['channel_id']
        user.save()
        return JsonResponse(dict(set_attributes=dict(request_status='done', service_name='Replace Info User')))


@method_decorator(csrf_exempt, name='dispatch')
class ChangeBotUserView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.ChangeBotUserForm(post_data)

        if form.is_valid():
            user = form.cleaned_data['user']
            user.bot_id = form.data['bot']
            user.save()
            print(user.pk, user.bot_id)
            return JsonResponse(dict(set_attributes=dict(changed_bot='changed')))

        return JsonResponse(dict(set_attributes=dict(changed_bot='not changed')))


@method_decorator(csrf_exempt, name='dispatch')
class ChangeBotChannelUserView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body) 
        if not ('user_id' in post_data and 'temp_user_id' in post_data):
            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                         request_error='Invalid params',
                                                         service_name='Change User BotChannel')))
        try:
            user_id = int(post_data['user_id'])
            temp_user_id = int(post_data['temp_user_id'])
        except ValueError:
            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                         request_error='User id not valid',
                                                         service_name='Change User BotChannel')))
        user = MessengerUser.objects.filter(id=user_id)
        if user.exists():
            user = user.last()
            for user_channel in UserChannel.objects.filter(user_id=temp_user_id):
                user_channel.user = user
                user_channel.save()
                # Enviar al usuario a una session en especifico
            save_json_attributes(dict(set_attributes=dict(session=898,
                                                          position=0,
                                                          reply_id=0,
                                                          field_id=0,
                                                          session_finish=False,
                                                          save_user_input=False,
                                                          save_text_reply=False)), None, user)
            return JsonResponse(dict(set_attributes=dict(user_id=user.pk,
                                                         username=user.username,
                                                         request_status='done',
                                                         service_name='Change User BotChannel')))
        return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                     request_error='User with ID %s does not exist.' % user_id,
                                                     service_name='Change User BotChannel')))


@method_decorator(csrf_exempt, name='dispatch')
class StopBotUserView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.StopBotUserForm(post_data)

        if form.is_valid():
            user = form.cleaned_data['user_id']
            bot_id = form.cleaned_data['bot_id']
            stop = form.data['stop']

            user_channel = user.userchannel_set.filter(bot_id=bot_id)
            if user_channel.exists():
                user_channel = user_channel.last()
                user_channel.live_chat = stop
                historic = LiveChat(user_channel=user_channel, live_chat=stop)
                historic.save()
                user_channel.save()
            return JsonResponse(dict(set_attributes=dict(live_chat=stop)))

        return JsonResponse(dict(set_attributes=dict(live_chat='not changed')))


@method_decorator(csrf_exempt, name='dispatch')
class CreateMessengerUserDataView(CreateView):
    model = UserData
    fields = ('user', 'data_key', 'data_value', 'attribute')

    def form_valid(self, form):
        form.save()
        if form.data['data_key'] == 'tipo_de_licencia':
            user = User.objects.get(id=form.data['user'])
            user.license = License.objects.get(name=form.data['data_value'])
            user.save()
            return JsonResponse(dict(set_attributes=dict(request_status='done', service_name='Update user license')))
        if form.data['data_key'] == 'language':
            user = User.objects.get(id=form.data['user'])
            user.language = Language.objects.get(name=form.data['data_value'])
            user.save()
            return JsonResponse(dict(set_attributes=dict(request_status='done', service_name='Update user language')))
        if form.data['data_key'] == 'user_type':
            user = User.objects.get(id=form.data['user'])
            user.entity = Entity.objects.get(name=form.data['data_value'])
            user.save()
            return JsonResponse(dict(set_attributes=dict(request_status='done', service_name='Update user entity')))
        return JsonResponse(dict(set_attributes=dict(request_status='done', service_name=form.data['data_key'])))

    def form_invalid(self, form):
        return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid params',
                                                     service_name='Create User Data')))


@method_decorator(csrf_exempt, name='dispatch')
class GetInitialUserData(View):

    def get(self, request, *args, **kwargs):
        return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid Method',
                                                     service_name='Get Initial User Data')))

    def post(self, request):
        form = forms.UserForm(request.POST)

        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid data.',
                                                         service_name='Get Initial User Data')))

        attributes = dict()

        for item in form.cleaned_data['user_id'].userdata_set.all():
            attributes[item.data_key] = item.data_value

        return JsonResponse(dict(set_attributes=attributes))


@method_decorator(csrf_exempt, name='dispatch')
class GetUserPreviousField(View):

    def get(self, request, *args, **kwargs):
        return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid Method',
                                                     service_name='Get User Previous Field')))

    def post(self, request):
        try:
            post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
            form = forms.UserForm(pot_data)

            if not form.is_valid():
                return JsonResponse(dict(request_status='error', request_error='Invalid data', service_name='Get User Previous Field'))
            
            user = form.cleaned_data['user_id']
            response = dict(request_status=200, field=False)

            attribute = user.userdata_set.filter(attribute__name='previous_field_id')
            if attribute.exists() and attribute.last().data_value:
                response['field'] = Field.objects.values('id', 'field_type').filter(id=attribute.last().data_value).first()
                response['replies'] = list(Reply.objects.values_list('label', flat=True).filter(field_id=int(response['field']['id'])))
        
        except Exception as e:
            response = dict(request_status='error', request_error=str(e), service_name='Get User Previous Field')

        return JsonResponse(response)


''' INSTANCES VIEWS '''


@method_decorator(csrf_exempt, name='dispatch')
class GetInstancesByUserView(View):

    def get(self, request, *args, **kwargs):
        return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid Method',
                                                     service_name='Get Instances')))

    def post(self, request):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.GetInstancesForm(post_data)

        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid data.',
                                                         service_name='Get Instances')))

        label = "Choice your instance: "
        try:
            if form.data['label']:
                label = form.data['label']
        except:
            pass
        user = MessengerUser.objects.get(id=int(form.data['user']))
        replies = [dict(title=item.name, set_attributes=dict(instance=item.pk, instance_name=item.name)) for item in
                   user.get_instances()]

        return JsonResponse(dict(
            set_attributes=dict(request_status='done', service_name='Get Instances'),
            messages=[
                dict(
                    text=label,
                    quick_replies=replies
                )
            ]
        ))


@method_decorator(csrf_exempt, name='dispatch')
class GuessInstanceByUserView(View):

    def get(self, request, *args, **kwargs):
        return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid Method',
                                                     service_name='Get Instances')))

    def post(self, request):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.GuessInstanceForm(post_data)

        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid data.',
                                                         service_name='Get Instances')))

        user_response = str(form.data['name'])
        user = MessengerUser.objects.get(id=int(form.data['user']))
        instances = [dict(instance_id=item.pk, instance_name=item.name) for item in user.get_instances()]
        instances_correlation = [0] * len(instances)
        for i in range(len(instances)):
            for name in instances[i]['instance_name'].split(" "):
                for word in user_response.split(" "):
                    if len(name) > 0 and len(word) > 0:
                        a = name.lower()
                        b = word.lower()
                        n = 0
                        for j in range(min(len(a), len(b))):
                            if a[j] == b[j]:
                                n = n + 10
                        instances_correlation[i] = instances_correlation[i] + n / max(len(a), len(b))
            instances_correlation[i] = instances_correlation[i] / len(instances[i])

        m = round(max(instances_correlation), 6)
        index = min([i for i, j in enumerate(instances_correlation) if round(j, 6) == m])

        return JsonResponse(dict(set_attributes=dict(instance=instances[index]['instance_id'],
                                                     instance_name=instances[index]['instance_name'])))


@csrf_exempt
def create_instance(request):

    if request.method == 'GET':
        return JsonResponse(dict(
            set_attributes=dict(request_status='error', request_error='Invalid Method',
                                service_name='Create Instance')))

    post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
    form = forms.InstanceModelForm(post_data)

    if not form.is_valid():
        return JsonResponse(dict(
            set_attributes=dict(request_status='error', request_error='Invalid Params',
                                service_name='Create Instance')))

    new_instance = form.save()
    assignation = InstanceAssociationUser.objects.create(user_id=form.data['user_id'], instance=new_instance)
    assignation.user.userdata_set.create(data_key='instance', data_value=new_instance.id, attribute_id=330)

    return JsonResponse(dict(
        set_attributes=dict(
            request_status='done',
            instance=new_instance.pk,
            instance_name=new_instance.name,
            instance_assignation_id=assignation.pk,
            service_name='Create Instance'
        )))


@method_decorator(csrf_exempt, name='dispatch')
class GetInstanceAttributeView(TemplateView):
    template_name = 'chatfuel/form.html'

    def get_context_data(self, **kwargs):
        c = super(GetInstanceAttributeView, self).get_context_data()
        c['form'] = forms.GetInstanceAttributeValue(None)
        return c

    def post(self, request, *args, **kwargs):
        post_data = self.request.POST if len(self.request.POST) > 0 else json.loads(self.request.body)
        form = forms.GetInstanceAttributeValue([post_data])

        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid params',
                                                         service_name='Get Instance Attribute')))

        instance = Instance.objects.get(id=form.data['instance'])
        attributes = instance.entity.attributes.filter(name=form.data['attribute'])

        if not attributes.count() > 0:
            return JsonResponse(dict(set_attributes=dict(
                request_status='error',
                request_error='Entity of instance has not attribute with name %s.' % form.data['attribute'],
                service_name='Get Instance Attribute')))

        attribute = Attribute.objects.get(name=form.data['attribute'])
        instance_attributes = AttributeValue.objects.filter(attribute=attribute, instance=instance)

        if not instance_attributes.count() > 0:
            return JsonResponse(dict(set_attributes=dict(
                request_status='error',
                request_error='Instance has not values with attribute: %s.' % form.data['attribute'],
                service_name='Get Instance Attribute')))

        return JsonResponse(
            dict(set_attributes={
                'request_status': 'done',
                form.data['attribute']: instance_attributes.last().value,
                'service_name': 'Get Instance Attribute'
            })
        )


@method_decorator(csrf_exempt, name='dispatch')
class ChangeInstanceNameView(TemplateView):
    template_name = 'chatfuel/form.html'

    def get_context_data(self, **kwargs):
        c = super(ChangeInstanceNameView, self).get_context_data()
        c['form'] = forms.ChangeNameForm(None)
        print(c['form'])
        return c

    def post(self, request, *args, **kwargs):
        post_data = self.request.POST if len(self.request.POST) > 0 else json.loads(self.request.body)
        form = forms.ChangeNameForm(post_data)

        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(
                request_status='error',
                request_error='Invalid Params.',
                service_name='Change Instance Name'
            )))

        instance = Instance.objects.get(id=form.data['instance'])
        instance.name = form.data['name']
        response = instance.save()

        return JsonResponse(dict(set_attributes=dict(
            request_status='done',
            request_message="name for instance has been changed.",
            instance_name=instance.name,
            service_name='Change Instance Name'
        ), messages=[]))


''' CODE VIEWS '''


@method_decorator(csrf_exempt, name='dispatch')
class VerifyCodeView(View):

    def get(self, request, *args, **kwargs):
        return JsonResponse(dict(request_status='error', request_error='Invalid Method',
                                 service_name='Verify Code'))

    def post(self, request):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.VerifyCodeForm(post_data)
        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid params',
                                                         service_name='Verify Code')))

        code = Code.objects.get(code=form.data['code'])

        return JsonResponse(dict(set_attributes=dict(request_status='done', request_code=code.code,
                                                     request_code_group=code.group.name, service_name='Verify Code')))


@method_decorator(csrf_exempt, name='dispatch')
class ExchangeCodeView(TemplateView):
    template_name = 'groups/code_form.html'

    def get(self, request, *args, **kwargs):
        raise Http404

    def post(self, request, *args, **kwargs):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = group_forms.ExchangeCodeForm(post_data)

        if form.is_valid():
            user = form.cleaned_data['messenger_user_id']
            code = form.cleaned_data['code']
            changes = AssignationMessengerUser.objects.filter(messenger_user_id=user.pk, group_id=code.group_id)
            print(changes)
            if not changes.count() > 0:
                exchange = AssignationMessengerUser.objects.create(messenger_user_id=user.pk, group=code.group,
                                                                   user_id=user.pk, code=code)
                code.exchange()
                if code.group.country:
                    user.userdata_set.create(data_key='Pais', data_value=code.group.country,
                                             attribute_id=Attribute.objects.get(name='Pais').id)
                if code.group.region:
                    user.userdata_set.create(data_key='Región', data_value=code.group.region,
                                             attribute_id=Attribute.objects.get(name='Región').id)
                return JsonResponse(dict(set_attributes=dict(request_status='done', service_name='Exchange Code')))
            else:
                return JsonResponse(dict(set_attributes=dict(request_status='done',
                                                             service_name='Exchange Code')))
        else:
            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                         request_error='User ID or code wrong',
                                                         service_name='Exchange Code')))


@method_decorator(csrf_exempt, name='dispatch')
class CreateInstanceAttributeView(CreateView):
    model = AttributeValue
    template_name = 'chatfuel/form.html'
    fields = ('instance', 'value', 'attribute')

    def get(self, request, *args, **kwargs):
        raise Http404

    def get_form(self, form_class=None):
        form = super(CreateInstanceAttributeView, self).get_form(form_class=None)
        form.fields['attribute'].to_field_name = 'name'
        return form

    def form_valid(self, form):

        if not form.instance.instance.entity.attributes.filter(id=form.instance.attribute.pk):
            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                         request_error='Attribute not in instance',
                                                         service_name='Create Instance Attribute')))

        attribute_value = form.save()

        return JsonResponse(dict(set_attributes=dict(request_status='done', request_attribute_value_id=attribute_value.pk,
                                                     service_name='Create Instance Attribute')))

    def form_invalid(self, form):
        return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                     request_error='Invalid params'), messages=[]))

    def get(self, request, *args):
        raise Http404


''' INTERACTION VIEWS '''


@method_decorator(csrf_exempt, name='dispatch')
class CreateInstanceInteractionView(CreateView):
    template_name = 'chatfuel/form.html'
    form_class = forms.InstanceInteractionForm

    def form_valid(self, form):
        form.instance.post_id = form.data['post_id']
        form.instance.created_at = datetime.now()
        interaction = form.save()

        if not interaction:
            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                         request_error='Invalid params'), messages=[]))

        return JsonResponse(dict(set_attributes=dict(request_status='done',
                                                     request_interaction_id=interaction.pk),
                                 messages=[]))

    def form_invalid(self, form):
        return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                     request_error='Invalid params'), messages=[]))


''' CHILDREN '''

# FIX LATER, maybe not necessary in a future


@method_decorator(csrf_exempt, name='dispatch')
class GetFavoriteChildView(View):

    def get(self, request, *args, **kwargs):
        raise Http404

    def post(self, request, *args, **kwargs):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.UserForm(post_data)
        day_first = True

        if 'en' in form.data:
            if form.data['en'] == 'true':
                day_first = False

        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                         request_error='Invalid params',
                                                         favorite_request_error='invalid params'), messages=[]))

        user = form.cleaned_data['user_id']
        instances = user.get_instances()
        children = instances.filter(entity_id=1)

        if not children.count() > 0:
            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                         request_error='User has not children',
                                                         favorite_request_error='User has not children'), messages=[]))

        if children.count() == 1:
            birthdays = children.first().attributevalue_set.filter(attribute__name='birthday')
            birth = None

            if not birthdays.count() > 0:
                return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                             request_error='Unique child has not birthday',
                                                             favorite_request_error='Unique child has not birthday'),
                                         messages=[]))

            birth = birthdays.last().value

            return JsonResponse(dict(set_attributes=dict(request_status='done',
                                                         favorite_instance=children.first().pk,
                                                         favorite_instance_name=children.first().name,
                                                         favorite_birthday=birth), messages=[]))
        dates = set()
        for child in children:
            child_birthdays = child.attributevalue_set.filter(attribute__name='birthday')
            if child_birthdays.count() > 0:
                dates.add(child_birthdays.last().pk)

        print(dates)

        if not len(dates) > 0:
            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                         request_error='Neither child has birthday property',
                                                         favorite_request_error='Neither child has birthday property'),
                                     messages=[]))

        registers = AttributeValue.objects.filter(id__in=dates)

        favorite = dict(id=registers.first().instance_id, value=parser.parse(registers.first().value,
                                                                             dayfirst=day_first))

        for register in registers:
            print(register.value)
            register.value = parser.parse(register.value, dayfirst=day_first)
            print(register.value)
            if register.value > favorite['value']:
                favorite = dict(id=register.instance_id, value=register.value)

        attributes= dict(
                request_status='done',
                favorite_instace=favorite['id'],
                favorite_instance_name=Instance.objects.get(id=favorite['id']).name,
                favorite_birthday=favorite['value'].strftime('%d/%m/%Y')\
                    if day_first else favorite['value'].strftime('%m/%d/%Y')
            )

        return JsonResponse(dict(
            set_attributes=attributes,
            messages=[]
        ))


@method_decorator(csrf_exempt, name='dispatch')
class GetLastChildView(View):

    def get(self, request, *args, **kwargs):
        raise Http404

    def post(self, request, *args, **kwargs):
        post_data = self.request.POST if len(self.request.POST) > 0 else json.loads(self.request.body)
        form = forms.UserForm(post_data)
        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(
                request_status='error',
                request_error='Invalid params.'
            ), messages=[]))

        instances = form.cleaned_data['user_id'].get_instances()
        children = instances.filter(entity_id=1).order_by('id')

        if not children.count() > 0:
            return JsonResponse(dict(set_attributes=dict(
                request_status='error',
                request_error='User has not children.'
            ), messages=[]))

        attributes = dict(
            instance=children.last().pk,
            instance_name=children.last().name,
            favorite_instance=children.last().pk,
            favorite_instance_name=children.last().name,
            request_status='done'
        )

        if children.last().attributevalue_set.filter(attribute__name='birthday'):
            attributes['birthday'] = children.last().attributevalue_set.filter(attribute__name='birthday').\
                last().value
            attributes['favorite_birthday'] = children.last().attributevalue_set.filter(attribute__name='birthday'). \
                last().value

        return JsonResponse(dict(set_attributes=attributes, messages=[]))


''' ARTICLES '''


@method_decorator(csrf_exempt, name='dispatch')
class GetArticleView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request, *args, **kwargs):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.UserArticleForm(post_data)
        user = User.objects.get(id=form.data['user_id'])
        print(user)
        set_attributes = dict(
                request_status='done',
                article_instance="false",
                article_instance_name="false"
            )

        if 'article' in form.data:
            articles = Article.objects.filter(id=form.data['article'])\
                .only('id', 'name', 'min', 'max', 'preview', 'thumbnail')
            article = articles.first()
            new_interaction = ArticleInteraction.objects \
                .create(user_id=form.data['user_id'], article=article, type='dispatched')

            set_attributes['article_id'] = article.pk
            set_attributes['article_name'] = article.name
            set_attributes['article_content'] = "%s/articles/%s/?user_id=%s" % (os.getenv('CONTENT_MANAGER_DOMAIN'), article.pk, user.pk)
            set_attributes['article_preview'] = article.preview
            set_attributes['article_thumbail'] = article.thumbnail

            if 'instance' in form.data:
                new_interaction.instance_id = form.data['instance']
                new_interaction.save()
                set_attributes['article_content'] = "%s%s" % (set_attributes['article_content'], 
                                                              "&instance=%s" % post_data['instance'])

            return JsonResponse(dict(set_attributes=set_attributes))

        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(status='error', error='Invalid params.')))

        instance = Instance.objects.get(id=form.data['instance'])
        
        if instance.entity_id == 1:
            months = instance.get_months()
            if not months:
                return JsonResponse(dict(set_attributes=dict(status='error', error='Instance has not a valid birthday')))

            articles = Article.objects.filter(min__lte=months, max__gte=months).order_by('?')
            if not articles.exists():
                return JsonResponse(dict(set_attributes=dict(status='error', error='Instance has not articles to view')))

        if instance.entity_id == 2:
            weeks = instance.get_weeks()
            print(weeks)
            if not weeks:
                return JsonResponse(dict(set_attributes=dict(status='error', error='Instance has not a pregnancy weeks')))

            articles = Article.objects.filter(min__lte=weeks, max__gte=weeks).order_by('?')
            if not articles.exists():
                return JsonResponse(dict(set_attributes=dict(status='error', error='Instance has not articles to view')))

        user_interactions = ArticleInteraction.objects.filter(user_id=user.pk, type='dispatched')
        filter_articles = articles.exclude(id__in=[x.article_id for x in user_interactions]).order_by('?')

        if not filter_articles.exists():
                return JsonResponse(dict(set_attributes=dict(status='error', error='Instance has not articles to view')))
        article = filter_articles.first()
        new_interaction = ArticleInteraction.objects \
                .create(user_id=form.data['user_id'], article=article, type='dispatched')
        if 'instance' in form.data:
                new_interaction.instance_id = form.data['instance']
                new_interaction.save()
        
        set_attributes['article_id'] = article.pk
        set_attributes['article_name'] = article.name
        set_attributes['article_content'] = "%s/articles/%s/?user_id=%s&instance_id=%s" % (os.getenv('CONTENT_MANAGER_DOMAIN'), 
                                                                                           article.pk, user.pk, instance.pk)
        set_attributes['article_preview'] = article.preview
        set_attributes['article_thumbail'] = article.thumbnail
        set_attributes['article_instance'] = instance.pk
        set_attributes['article_instance_name'] = instance.name

        return JsonResponse(dict(set_attributes=set_attributes))


@method_decorator(csrf_exempt, name='dispatch')
class GetRecomendedArticleView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request, *args, **kwargs):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.UserArticleForm(post_data)
        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(status='error', error='Invalid params.')))
        
        trial = False
        params_404 = list()
        applied_filters = 0
        data = form.cleaned_data
        user_id = data['user_id'].id
        
        # article pool
        articles = Article.objects.all()
        
        # filter by intent if there is an intent
        last_intent = UserData.objects.filter(user__id=user_id, data_key='last_intent')
        if last_intent.exists() and last_intent.last() and last_intent.last().data_value:
            intent_id = last_intent.last().data_value
            params_404.append('intent: {0}'.format(intent_id))
            article_subset = ArticleIntent.objects.filter(intent_id=intent_id).values_list('article_id', flat=True)
            article_subset = articles.filter(id__in=list(article_subset))
            # set artilce pool and remove previous intent 
            if article_subset.exists():
                applied_filters += 1
                articles = article_subset
                last_intent.update(data_value='')
        
        # filter by instance: Pregnant == 2, Child == 1
        if data['instance'].entity.id in [ 1, 2 ]:
            if data['instance'].entity.id == 2:  # Pregnant
                min_val = -72
                max_val = -1
                if data['instance'].get_weeks():
                    min_val = max_val = data['instance'].get_weeks()
            else:  # Child
                min_val = 0
                max_val = 72
                if data['instance'].get_months():
                    min_val = max_val = data['instance'].get_months()
            
            params_404.append('entity: {0}, min:{1}, max:{2}'.format(data['instance'].entity.name, min_val, max_val))
            article_subset = articles.filter(min__lte=min_val, max__gte=max_val).order_by('?')
            if article_subset.exists():
                applied_filters += 1
                articles = article_subset      

        # filter by type of article
        if data['type']:
            article_subset = articles.filter(type_id=data['type'].id)
            params_404.append('type: {0}'.format(data['type'].name))
            if article_subset.exists():
                applied_filters += 1
                articles = article_subset

        # Exclude articles the user has already seen
        seen = ArticleInteraction.objects.filter(user_id=user_id).filter(article__in=list(articles.values_list('id', flat=True)))
        seen = list(seen.values_list('article_id', flat=True).distinct())
        articles = articles.exclude(id__in=seen)
        
        # select article from filtered pool
        if not articles.exists() or applied_filters < 1:
            url = '{0}/api/v1/experiments/2/resource/{1}'.format(os.getenv('RECOMMENDER_URL'), form.data['instance'])
            req = requests.post(url=url, auth=HTTPBasicAuth(os.getenv('RECOMMENDER_USR'), os.getenv('RECOMMENDER_PSW')),
                                json=dict(experiment_id=2, resource_id=form.data['instance']),
                                headers={'Content-type': 'application/json', 'Accept': 'text/plain'})
            if req.status_code != 200:
                if not articles.exists():
                    if seen:
                        applied_filters -= 1
                        articles = Article.objects.all().filter(id=seen[0])
                    else:
                        return JsonResponse(dict(set_attributes=dict(status='error', error='Invalid params.')))
            else:
                res = req.json()
                article = res['data'][0]
                trial = res['trial']
                articles = Article.objects.all().filter(id=article['id'])
        
        article = articles.first()
        
        # create response based on selected article
        attributes = dict(  article_id=article.id, article_name=article.name,
                            article_preview=article.preview,
                            article_instance=form.data['instance'],
                            article_content='{0}/articles/{1}/?user_id={2}&instance={3}'.format(  os.getenv('CONTENT_MANAGER_DOMAIN'), 
                                                                                                article.id, 
                                                                                                user_id,
                                                                                                form.data['instance']))
        if trial:
            attributes['trial'] = trial['id']
            attributes[article_content] += '&trial={0}'.format(trial['id'])
        
        # Save interaction 
        ArticleInteraction.objects.create(user_id=user_id, article_id=article.id,
                                        type='dispatched', instance_id=form.data['instance'])

        # check if all parameters could be applied, +1 because we always test for seen but we don't add it to params_404
        if len(params_404) > applied_filters:
            MissingArticles.objects.create( filter_params=' | '.join(params_404), 
                                            seen_count=len(seen), 
                                            seen='articles ids: {0}'.format(','.join(str(s) for s in seen)))
        
        return JsonResponse(dict(set_attributes=attributes))


@method_decorator(csrf_exempt, name='dispatch')
class GetArticleTextView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request, *args, **kwargs):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.ArticleForm(post_data)
        if not form.is_valid():
            return JsonResponse(dict(request_status='error', request_error='Article not exist.'))
        split_content = form.cleaned_data['article'].text_content.split('|')
        messages = [dict(text=content) for content in split_content]
        return JsonResponse(dict(messages=messages))


@method_decorator(csrf_exempt, name='dispatch')
class GetArticleImageView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request, *args, **kwargs):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.ArticleForm(post_data)
        if not form.is_valid():
            return JsonResponse(dict(request_status='error', request_error='Article not exist.'))

        if not form.cleaned_data['article'].thumbnail:
            return JsonResponse(dict(request_status='error', request_error='Article has not image.'))

        return JsonResponse(dict(set_attributes=dict(),
            messages=[
            dict(
                attachment=dict(
                    type='image',
                    payload=dict(url=form.cleaned_data['article'].thumbnail)
                )
            )
        ]))


@method_decorator(csrf_exempt, name='dispatch')
class AddFeedbackToArticleView(CreateView):
    model = ArticleFeedback
    fields = ('user', 'value', 'article')

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def form_valid(self, form):
        new_feedback = form.save()
        return JsonResponse(dict(set_attributes=dict(request_status='done', request_feedback_id=new_feedback.pk)))

    def form_invalid(self, form):
        return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid params',
                                                     service_name='Add feedback to article')))


''' MILESTONES UTILITIES '''


@method_decorator(csrf_exempt, name='dispatch')
class GetMilestoneView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request, *args, **kwargs):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.InstanceForm(post_data)
        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid params.')))

        instance = form.cleaned_data['instance']
        months = 0
        if instance.get_months():
            months = instance.get_months()
        print(months)
        day_range = (datetime.now() - timedelta(days=1))
        responses = instance.response_set.filter(created_at__gte=day_range)
        milestones = Milestone.objects.filter(max__gte=months, min__lte=months, source__in=['CDC', '1', 'Credi'])\
            .exclude(id__in=[i.milestone_id for i in responses])

        if not milestones.exists():
            return JsonResponse(dict(set_attributes=dict(request_status='done',
                                                         request_response='Instance has no milestones to do.',
                                                         all_range_milestones_dispatched='true',
                                                         all_level_milestones_dispatched='true')))

        filtered_milestones = []
        for m in milestones:
            responses = instance.response_set.filter(milestone_id=m.pk)
            if not responses.exists():
                filtered_milestones.append(m.pk)
            else:
                if responses.last().response != 'done':
                    filtered_milestones.append(m.pk)
        print(filtered_milestones)

        filtered_milestones = milestones.filter(id__in=filtered_milestones)
        act_range = 'false'

        if filtered_milestones.exists():
            milestone = filtered_milestones.order_by('secondary_value').first()
            if filtered_milestones.count() < 2:
                act_range = 'true'
        else:
            milestone = milestones.exclude(id__in=[m.pk for m in filtered_milestones]).order_by('secondary_value')\
                .first()

        lang = 'es'
        if 'user_id' in form.data:
            lang = form.cleaned_data['user_id'].get_language()

        language = Language.objects.get(name=lang)

        translations = MilestoneTranslation.objects.filter(milestone=milestone, language=language)
        if translations.exists():
            milestone_text = translations.first().name
        else:
            milestone_text = milestone.milestonetranslation_set.first().name
            #region = os.getenv('region')
            #translate = boto3.client(service_name='translate', region_name=region, use_ssl=True)
            #result = translate.translate_text(Text=milestone.milestonetranslation_set.first().name,
            #                                  SourceLanguageCode="auto", TargetLanguageCode=language.name)
            #new_translation = MilestoneTranslation.objects.create(
            #    milestone=milestone, language=language, name=result['TranslatedText'],
            #    description=result['TranslatedText'])
            #milestone_text = new_translation.name

        return JsonResponse(dict(set_attributes=dict(request_status='done',
                                                     milestone=milestone.pk,
                                                     milestone_text=milestone_text,
                                                     all_level_milestones_dispatched='false',
                                                     all_range_milestones_dispatched=act_range)))


@method_decorator(csrf_exempt, name='dispatch')
class GetProgramMilestoneView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request, *args, **kwargs):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.InstanceForm(post_data)
        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid params.')))

        instance = form.cleaned_data['instance']
        months = 0
        if instance.get_months():
            months = instance.get_months()
        user = instance.get_users().first()
        group = Group.objects.filter(assignationmessengeruser__user_id=user.pk).first()
        program = group.programs.first()
        # Get milestone question
        if program.name == 'Afini Botnar':
            risks = MilestoneRisk.objects.filter(program=program)
            data = instance.get_program_milestone(program, risks)
            if (not data['session'].active) or ('milestone' not in data):
                # Get max scores of instance
                scores = instance.score_set.all().values('area__name').annotate(score=Max('value'))
                response = dict(request_status='done',
                                request_response='Instance has no milestones to do.',
                                all_range_milestones_dispatched='true',
                                all_level_milestones_dispatched='true',
                                total_score=sum([x['score'] for x in scores]))
                # Attach scores per area to the response
                response.update(dict([(x['area__name'], x['score']) for x in scores]))
                # Verify if instance has risks
                response['risks'] = (len(instance.get_risk_milestones_text(program)) > 0)
                return JsonResponse(dict(set_attributes=response))
            milestone = data['milestone']
            act_range = 'false'
        else:
            m_ids = set(m.milestone_id for m in program.programmilestonevalue_set.filter(min__lte=months, max__gte=months))
            day_range = (datetime.now() - timedelta(days=1))
            milestones = Milestone.objects.filter(id__in=m_ids)\
                .exclude(id__in=[i.milestone_id for i in instance.response_set.filter(created_at__gte=day_range)])

            if not milestones.exists():
                return JsonResponse(dict(set_attributes=dict(request_status='done',
                                                             request_response='Instance has no milestones to do.',
                                                             all_range_milestones_dispatched='true',
                                                             all_level_milestones_dispatched='true')))

            filtered_milestones = []
            for m in milestones:
                responses = instance.response_set.filter(milestone_id=m.pk)
                if not responses.exists():
                    filtered_milestones.append(m.pk)
                else:
                    if responses.last().response != 'done':
                        filtered_milestones.append(m.pk)
            print(filtered_milestones)

            filtered_milestones = milestones.filter(id__in=filtered_milestones)
            act_range = 'false'

            if filtered_milestones.exists():
                milestone = filtered_milestones.order_by('secondary_value').first()
                if filtered_milestones.count() < 2:
                    act_range = 'true'
            else:
                milestone = milestones.exclude(id__in=[m.pk for m in filtered_milestones]).order_by('secondary_value')\
                    .first()


        lang = 'es'
        if 'user_id' in form.data:
            lang = form.cleaned_data['user_id'].get_language()

        language = Language.objects.get(name=lang)

        translations = MilestoneTranslation.objects.filter(milestone=milestone, language=language)
        if translations.exists():
            milestone_text = translations.first().name
        else:
            milestone_text = milestone.milestonetranslation_set.first().name
            #region = os.getenv('region')
            #translate = boto3.client(service_name='translate', region_name=region, use_ssl=True)
            #result = translate.translate_text(Text=milestone.milestonetranslation_set.first().name,
            #                                  SourceLanguageCode="auto", TargetLanguageCode=language.name)
            #new_translation = MilestoneTranslation.objects.create(
            #    milestone=milestone, language=language, name=result['TranslatedText'],
            #    description=result['TranslatedText'])
            #milestone_text = new_translation.name

        return JsonResponse(dict(set_attributes=dict(request_status='done',
                                                     milestone=milestone.pk,
                                                     milestone_text=milestone_text,
                                                     all_level_milestones_dispatched='false',
                                                     all_range_milestones_dispatched=act_range)))


@method_decorator(csrf_exempt, name='dispatch')
class GetProgramRisksMilestoneView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request, *args, **kwargs):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.InstanceForm(post_data)
        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid params.')))

        instance = form.cleaned_data['instance']
        user = instance.get_users().first()
        group = Group.objects.filter(assignationmessengeruser__user_id=user.pk).first()
        program = group.programs.first()
        response = instance.get_risk_milestones_text(program)
        for key in response:
            response[key] = "\n\n".join(response[key])
        response['request_status'] = 'done'
        return JsonResponse(dict(set_attributes=response))


@method_decorator(csrf_exempt, name='dispatch')
class GetInstanceMilestoneView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request, *args, **kwargs):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.InstanceForm(post_data)

        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid params.')))

        instance = form.cleaned_data['instance']

        birth = instance.get_attribute_values('birthday')
        if not birth:
            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                         request_error='Instance has not birthday.')))
        try:
            date = parser.parse(birth.value)
            print(date)
        except:
            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                         request_error='Instance has not a valid date in birthday.')))

        months = instance.get_months()
        user = instance.get_users().first()
        groups = Group.objects.filter(assignationmessengeruser__user_id=user.pk)
        if groups.exists():
            group = groups.first()
            programs = group.programs.all()
        else:
            programs = None
        if programs and programs.exists():
            program = programs.first()
        else:
            # Programa Afini por default
            program = Program.objects.get(id=1)

        associations = set(i.milestone_id for i in
                           program.programmilestonevalue_set.filter(min__lte=months, max__gte=months))
        print(associations)

        milestones = Milestone.objects.filter(id__in=[i.milestone_id for i
                                                      in program.programmilestonevalue_set.filter(min__lte=months,
                                                                                                  max__gte=months)])
        available = 0
        completed = 0
        print(milestones.count())
        for m in milestones:
            print(m.name)
            responses = instance.response_set.filter(milestone_id=m.pk)
            if responses.exists():
                if responses.last().response == 'done':
                    completed = completed + 1
                else:
                    available = available + 1
            else:
                available = available + 1

        code = ''
        second_code = ''
        secondary_value = 0
        responses = Response.objects.filter(instance=instance, response='done')
        if responses.exists():
            response_milestone = responses.order_by('-milestone__secondary_value')[0].milestone
            code = response_milestone.code
            second_code = response_milestone.second_code
            secondary_value = response_milestone.secondary_value

        return JsonResponse(dict(
            set_attributes=dict(
                all_level_milestones=milestones.count(),
                all_range_milestones=milestones.count(),
                level_milestones_available=available,
                range_milestones_available=available,
                level_milestones_completed=completed,
                range_milestones_completed=completed,
                code=code,
                second_code=second_code,
                secondary_value=secondary_value
            )
        ))


@method_decorator(csrf_exempt, name='dispatch')
class CreateResponseView(CreateView):
    model = Response
    fields = ('instance', 'milestone', 'response')

    def form_valid(self, form):
        form.instance.created_at = datetime.now()
        r = form.save()
        instance = Instance.objects.get(id=r.instance.id)
        if r.response not in ['done', 'dont-know', 'failed']:
            if r.response.lower() in ['si', 'sí', 'yes', 'done']:
                r.response = 'done'
            elif r.response.lower() in ['no sé', 'no se', 'dont know', 'dont-know']:
                r.response = 'dont-know'
            else:
                r.response = 'failed'
        r.save()
        # Save question response
        new_response = False
        if r.response == 'done':
            new_response = instance.question_milestone_complete(r.milestone.id)
        elif r.response in ['dont-know', 'failed']:
            new_response = instance.question_milestone_fail(r.milestone.id)
        if new_response:
            r.delete()
            r = new_response
        return JsonResponse(dict(set_attributes=dict(request_status='done', request_transaction_id=r.pk)))

    def form_invalid(self, form):
        return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid params.')))


''' SESSIONS UTILITIES '''

@method_decorator(csrf_exempt, name='dispatch')
def get_session(cleaned_data, data, position=0):
    user = cleaned_data['user_id']
    session = None
    # If Session is type=Register
    if cleaned_data['Type'].exists() and cleaned_data['Type'].first().name == 'Register':
        session = Session.objects.filter(session_type__in=cleaned_data['Type']).first()
    # If requested a specific session
    if cleaned_data['session']:
        session = cleaned_data['session']
    if session:
        save_json_attributes(dict(set_attributes=dict(session=session.pk,
                                                      position=position,
                                                      reply_id=0,
                                                      field_id=0,
                                                      session_finish=False,
                                                      save_user_input=False,
                                                      save_text_reply=False)), None, user)
        return dict(set_attributes=dict(session=session.pk, position=position,
                                        request_status='done', session_finish='false'))
    if cleaned_data['instance']:
        instance = cleaned_data['instance']
    else:
        if user.userdata_set.filter(attribute__name='instance').exists():
            instance = Instance.objects.get(id=user.userdata_set.
                                            filter(attribute__name='instance').last().data_value)
        else:
            instance = None
    if instance:
        instance_id = instance.id
        if instance.entity_id == 2:  # Pregnant
            weeks = instance.get_attribute_values('pregnant_weeks')
            if weeks:
                age = weeks.value
            else:
                age = -1
        else:
            birth = instance.get_attribute_values('birthday')
            if not birth:
                age = None
                #return dict(set_attributes=dict(request_status='error', request_error='Instance has not birthday.'))
            else:
                try:
                    date = parser.parse(birth.value)
                    rd = relativedelta.relativedelta(datetime.now(), date)
                    age = rd.months
                    if rd.years:
                        age = age + (rd.years * 12)
                except:
                    age = None
                    #return dict(set_attributes=dict(request_status='error', request_error='Instance has not a valid date in birthday.'))
    else:
        age = None
        instance_id = None

    if age is None:
        # Filter by language and license and type 'Info General'
        sessions = Session.objects.filter(session_type__name='Info General',
                                          lang__language_id=user.language.id,
                                          licences=user.license)
    else:
        # Filter by age, language and license
        sessions = Session.objects.filter(min__lte=age, max__gte=age,
                                          lang__language_id=user.language.id,
                                          licences=user.license)

    if instance:  # Filter by entity o user and/or instance
        sessions = sessions.filter(entities__in=[user.entity, instance.entity]).distinct()
    else:
        sessions = sessions.filter(entities=user.entity)

    if user.assignationmessengeruser_set.exists():  # If user has a group, hence a program, filter by program
        sessions = sessions.filter(programs__group__assignationmessengeruser__messenger_user_id=user.id
                                   ).distinct()

    if cleaned_data['Type'].exists():  # Filter by type of session
        sessions = sessions.filter(session_type__in=cleaned_data['Type'])

    interactions = SessionInteraction.objects.filter(user_id=data['user_id'],
                                                     instance_id=instance_id,
                                                     type='session_init',
                                                     session__in=sessions)

    sessions_new = sessions.exclude(id__in=[interaction.session_id for interaction in interactions])
    if not sessions_new.exists():
        if not sessions.exists():
            return dict(set_attributes=dict(request_status='error',
                                            request_error='Instance has not sessions.'))
        else:
            session = sessions.last()
    else:
        session = sessions_new.first()
    save_json_attributes(dict(set_attributes=dict(session=session.pk,
                                                  position=position,
                                                  reply_id=0,
                                                  field_id=0,
                                                  session_finish=False,
                                                  save_user_input=False,
                                                  save_text_reply=False)), instance, user)
    return dict(set_attributes=dict(session=session.pk, position=position, request_status='done', session_finish='false'))


@method_decorator(csrf_exempt, name='dispatch')
class GetSessionView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request, *args, **kwargs):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.SessionForm(post_data)

        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid params.')))
        response = get_session(form.cleaned_data, form.data)
        return JsonResponse(response)


@method_decorator(csrf_exempt, name='dispatch')
class SendSessionView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request, *args, **kwargs):

        if len(request.POST) > 0:
            data = request.POST.dict()
        else:
            data = json.loads(request.body)

        form = forms.SessionForm(data)

        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid params.')))

        # check if user is in the 24hr windows
        in_window = UserChannel.objects.filter( bot_id=data['bot_id'], 
                                                bot_channel_id=data['bot_channel_id'], 
                                                user_channel_id=data['user_channel_id'])
        if in_window.exists():
            in_window = in_window.last().get_last_user_message_date(check_window=True)                               
            if 'tags' not in data and not in_window:
                return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='No se asignó la sesión, \n Usuario fuera de la ventanda de 24hrs')))
        else:
            msg = 'No se encontró el user_channel \n  bot_id: {0}, user_channel_id:{1}'.format( data['bot_id'], 
                                                                                                data['user_channel_id'])
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_error=msg)))
        
        position = 0
        if 'position' in data:
            position = data['position']
        response = get_session(form.cleaned_data, form.data, position)
        
        if response['set_attributes']['request_status'] == 'done':
            try:
                service_url = '{0}/bots/{1}/channel/{2}/send_message/'.format(os.getenv('WEBHOOK_DOMAIN'),
                                                                    data['bot_id'],
                                                                    data['bot_channel_id'])
                service_params = dict(user_channel_id=data['user_channel_id'],
                                    message='hot_trigger_start_session')

                if 'tags' in data:
                    service_params['tags'] = data['tags']

                service_response = requests.post(service_url, json=service_params)
                response_json = service_response.json()

                return JsonResponse(response_json)
            except Exception as e:
                return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                         request_error=str(e), type="Send session")))
        
        return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                         request_error='Failed to set session to user')))


@method_decorator(csrf_exempt, name='dispatch')
class GetSessionFieldView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request, *args, **kwargs):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.SessionFieldForm(post_data)
        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid params.')))
        
        try:
            # user data check attribute session finished
            user = form.cleaned_data['user_id']
            if user.userdata_set.filter(attribute__name='session_finish').exists():
                session_finish = user.userdata_set.filter(attribute__name='session_finish').last().data_value
                if session_finish == 'true':
                    return JsonResponse(dict(set_attributes=dict(session_finish=session_finish)))
            
            # user data check for instance
            if form.cleaned_data['instance']:
                instance = form.cleaned_data['instance']
            else:
                if user.userdata_set.filter(attribute__name='instance').exists():
                    instance = Instance.objects.get(id=user.userdata_set.
                                                    filter(attribute__name='instance').last().data_value)
                else:
                    instance = None
            instance_id = None
            if instance:
                instance_id = instance.id
            
            # user data  get current session
            if form.cleaned_data['session']:
                session = form.cleaned_data['session']
            else:
                if user.userdata_set.filter(attribute__name='session').exists():
                    session = Session.objects.get(id=user.userdata_set.filter(attribute__name='session').last().data_value)
                else:
                    return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                                request_error='User has no session')))
            # user attribute positon
            if form.cleaned_data['position']:
                position = form.cleaned_data['position']
            else:
                if user.userdata_set.filter(attribute__name='position').exists():
                    position = user.userdata_set.filter(attribute__name='position').last().data_value
                else:
                    position = 0
            field = session.field_set.filter(position=int(position))
            response = dict()
            attributes = dict()

            if not field.exists():
                return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Field doesn\'t exists.')))

            field = field.first()
            fields = session.field_set.all().order_by('position')
            attributes['previous_field_id'] = field.id
            finish = 'false'
            response_field = field.position + 1
            if field.position == 0:
                attributes['previous_field_id'] = False
                # Guardar interaccion
                SessionInteraction.objects.create(user_id=user.id,
                                                instance_id=instance_id,
                                                type='broadcast_init',
                                                session=session)
                # Guardar atributos de riesgo en chatfuel
                interactions = SessionInteraction.objects.filter(instance_id=instance_id)
                for program_attribute in ProgramAttributes.objects.filter(attribute__entity__in=[1, 2]):# child or pregnant
                    a = AttributeValue.objects.filter(instance_id=instance_id,
                                                    attribute=program_attribute.attribute).order_by('id')
                    if a.exists():
                        reply = Reply.objects.filter(attribute=program_attribute.attribute.id,
                                                    value=a.last().value,
                                                    field_id__in=[x.field_id for x in interactions])
                        if reply.exists():
                            attributes[program_attribute.attribute.name] = reply.last().label
                        else:
                            reply = Reply.objects.filter(attribute=program_attribute.attribute.id,
                                                        value=a.last().value)
                            if reply.exists():
                                attributes[program_attribute.attribute.name] = reply.last().label
                            else:
                                attributes[program_attribute.attribute.name] = a.last().value
                for program_attribute in ProgramAttributes.objects.filter(attribute__entity__in=[4, 5]):# caregiver/professional
                    a = UserData.objects.filter(user=user, attribute=program_attribute.attribute).order_by('id')
                    if a.exists():
                        reply = Reply.objects.filter(attribute=program_attribute.attribute.id,
                                                    value=a.last().data_value,
                                                    field_id__in=[x.field_id for x in interactions])
                        if reply.exists():
                            attributes[program_attribute.attribute.name] = reply.last().label
                        else:
                            reply = Reply.objects.filter(attribute=program_attribute.attribute.id,
                                                        value=a.last().data_value)
                            if reply.exists():
                                attributes[program_attribute.attribute.name] = reply.last().label
                            else:
                                attributes[program_attribute.attribute.name] = a.last().data_value
            if field.field_type == 'redirect_session':
                session = field.redirectsession.session
                attributes['session'] = session.id
                field = session.field_set.filter(position=int(field.redirectsession.position)).first()
                fields = session.field_set.all().order_by('position')
                response_field = field.position + 1

            attributes['save_text_reply'] = False
            attributes['save_user_input'] = False
            messages = []

            if field.field_type == 'consume_service':
                rta = replace_text_attributes(field.service.available_service.url, instance, user)
                if rta['status'] == 'error':
                    return JsonResponse(dict(set_attributes=dict(request_status='error', request_error=rta['response'])))
                service_url = rta['response']
                whitelist = os.getenv('CONSUME_SERVICE_URLS').split(',')
                if is_safe_url(service_url, allowed_hosts={*whitelist}, require_https=False):
                    service_params = {}
                    for param in field.service.serviceparam_set.all():
                        rta = replace_text_attributes(param.value, instance, user)
                        if rta['status'] == 'error':
                            return JsonResponse(
                                dict(set_attributes=dict(request_status='error', request_error=rta['response'])))
                        service_params[param.parameter] = rta['response']
                    if field.service.available_service.request_type == 'get':
                        service_response = requests.get(service_url, params=service_params)
                    else:
                        service_response = requests.post(service_url, data=service_params)
                    response_json = service_response.json()
                    if 'set_attributes' not in response_json:
                        response_json['set_attributes'] = dict()
                    if 'session_finish' not in response_json['set_attributes']:
                        response_json['set_attributes']['session_finish'] = finish
                    if 'position' not in response_json['set_attributes']:
                        response_json['set_attributes']['position'] = response_field
                    if 'save_text_reply' not in response_json['set_attributes']:
                        response_json['set_attributes']['save_text_reply'] = False
                    if 'save_user_input' not in response_json['set_attributes']:
                        response_json['set_attributes']['save_user_input'] = False
                    if 'session' not in response_json['set_attributes']:
                        response_json['set_attributes']['session'] = session.id
                    # If service returns quick replies
                    if 'messages' in response_json:
                        service_replies = False
                        for message in response_json['messages']:
                            if 'quick_replies' in message:
                                message['quick_reply_options'] = dict(process_text_by_ai=False, text_attribute_name='last_reply')
                                messages.append(message)
                                service_replies = True
                        if service_replies:
                            response['messages'] = messages
                            attributes['save_text_reply'] = True
                            attributes['field_id'] = field.id
                            attributes['session_finish'] = finish
                            attributes['position'] = response_field
                            save_json_attributes(dict(set_attributes=attributes), instance, user)
                            response['set_attributes'] = attributes
                            return JsonResponse(response)
                    save_json_attributes(response_json, instance, user)
                    return JsonResponse(response_json)
                return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='URL not safe')))

            elif field.field_type == 'assign_sequence':
                service_url = "%s/assign_to_sequence/" % os.getenv('HOTTRIGGERS_DOMAIN')
                service_params = dict(data=[dict(user_id=x.user_id,
                                                bot_id=x.bot_id,
                                                channel_id=x.channel_id,
                                                user_channel_id=x.user_channel_id,
                                                bot_channel_id=x.bot_channel_id) for x in user.userchannel_set.all()],
                                    sequence_id=field.assignsequence.sequence_id,
                                    start_position=field.assignsequence.start_position)
                service_response = requests.post(service_url, json=service_params)
                #response_json = service_response.json()
                #if response_json.status_code != 200:
                #    return JsonResponse(dict(set_attributes=dict(request_status='error',
                #                                                 request_error='Failed to assign to sequence')))

            elif field.field_type == 'unsubscribe_sequence':
                service_url = "%s/unsubscribe_sequence/" % os.getenv('HOTTRIGGERS_DOMAIN')
                service_params = dict(data=[dict(user_id=x.user_id,
                                                bot_id=x.bot_id) for x in user.userchannel_set.all()],
                                    sequence_id=field.unsubscribesequence.sequence_id)
                service_response = requests.post(service_url, json=service_params)

            elif field.field_type == 'set_attributes':
                for a in field.setattribute_set.all():
                    rta = replace_text_attributes(a.value, instance, user)
                    if rta['status'] == 'error':
                        return JsonResponse(
                            dict(set_attributes=dict(request_status='error', request_error=rta['response'])))
                    attribute_value = rta['response']
                    try:
                        attribute_value = eval(attribute_value)
                    except (SyntaxError, NameError, TypeError, ZeroDivisionError):
                        pass
                    attributes[a.attribute.name] = attribute_value
                    # Guardar atributo instancia o embarazo
                    if Entity.objects.get(id=1).attributes.filter(name=a.attribute.name).exists() \
                            or Entity.objects.get(id=2).attributes.filter(name=a.attribute.name).exists():
                        attribute = Attribute.objects.filter(name=a.attribute.name)
                        if attribute.exists():
                            AttributeValue.objects.create(instance=instance, attribute=attribute.first(),
                                                        value=attribute_value)
                        else:
                            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                                        request_error='Attribute does not exist')))
                    # Guardar atributo usuario
                    if Entity.objects.get(id=4).attributes.filter(name=a.attribute.name).exists() \
                            or Entity.objects.get(id=5).attributes.filter(name=a.attribute.name).exists():
                        UserData.objects.create(user=user, data_key=a.attribute.name, attribute=a.attribute,
                                                data_value=attribute_value)
                    if a.attribute.name == 'tipo_de_licencia':
                        if License.objects.filter(name=attribute_value).count() == 1:
                            user.license = License.objects.get(name=attribute_value)
                            user.save()
                        else:
                            valid_licences = ','.join([x.name for x in License.objects.all()])
                            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                                        request_error='tipo_de_licencia not valid. Must be a valid License (%s)' % valid_licences)))
                    if a.attribute.name == 'language':
                        if Language.objects.filter(name=attribute_value).count() == 1:
                            user.language = Language.objects.get(name=attribute_value)
                            user.save()
                        else:
                            valid_language = ','.join([x.name for x in Language.objects.all()])
                            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                                        request_error='language not valid. Must be a valid Language (%s)' % valid_language)))
                    if a.attribute.name == 'user_type':
                        if Entity.objects.filter(name=attribute_value).count() == 1:
                            user.entity = Entity.objects.get(name=attribute_value)
                            user.save()
                        else:
                            valid_entities = ','.join([x.name for x in Entity.objects.all()])
                            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                                        request_error='user_type not valid. Must be a valid Entity (%s)' % valid_entities)))

            elif field.field_type == 'text' or field.field_type == 'one_time_notification':
                for m in field.message_set.all():
                    rta = replace_text_attributes(m.text, instance, user)
                    if rta['status'] == 'error':
                        return JsonResponse(
                            dict(set_attributes=dict(request_status='error', request_error=rta['response'])))
                    new_text = rta['response']
                    if session.field_set.filter(field_type='buttons', position=field.position + 1).exists():
                        buttons = []
                        for b in session.field_set.\
                                filter(field_type='buttons', position=field.position + 1).first().button_set.all():
                            if b.button_type == 'show_block':
                                rta = replace_text_attributes(b.block_names, instance, user)
                                if rta['status'] == 'error':
                                    return JsonResponse(
                                        dict(set_attributes=dict(request_status='error', request_error=rta['response'])))
                                block_names = rta['response']
                                rta = replace_text_attributes(b.title, instance, user)
                                if rta['status'] == 'error':
                                    return JsonResponse(
                                        dict(set_attributes=dict(request_status='error', request_error=rta['response'])))
                                title = rta['response']
                                buttons.append(dict(type=b.button_type,
                                                    block_names=[block_names],
                                                    title=title))
                            else:
                                rta = replace_text_attributes(b.url, instance, user)
                                if rta['status'] == 'error':
                                    return JsonResponse(
                                        dict(set_attributes=dict(request_status='error', request_error=rta['response'])))
                                url = rta['response']
                                rta = replace_text_attributes(b.title, instance, user)
                                if rta['status'] == 'error':
                                    return JsonResponse(
                                        dict(set_attributes=dict(request_status='error', request_error=rta['response'])))
                                title = rta['response']
                                buttons.append(dict(type=b.button_type,
                                                    url=url,
                                                    title=title))
                        messages.append(dict(attachment=dict(type="template",
                                                            payload=dict(template_type="button",
                                                                        text=new_text,
                                                                        buttons=buttons))))
                        response_field = response_field + 1
                    else:
                        messages.append(dict(text=new_text))
                    
                    if field.field_type == 'one_time_notification':
                        messages[-1]['OTN'] = True

            elif field.field_type == 'image':
                m = field.message_set.first()
                if session.field_set.filter(field_type='buttons', position=field.position + 1).exists():
                    buttons = []
                    for b in session.field_set. \
                            filter(field_type='buttons', position=field.position + 1).first().button_set.all():
                        if b.button_type == 'show_block':
                            rta = replace_text_attributes(b.block_names, instance, user)
                            if rta['status'] == 'error':
                                return JsonResponse(
                                    dict(set_attributes=dict(request_status='error', request_error=rta['response'])))
                            block_names = rta['response']
                            rta = replace_text_attributes(b.title, instance, user)
                            if rta['status'] == 'error':
                                return JsonResponse(
                                    dict(set_attributes=dict(request_status='error', request_error=rta['response'])))
                            title = rta['response']
                            buttons.append(dict(type=b.button_type,
                                                block_names=[block_names],
                                                title=title))
                        else:
                            rta = replace_text_attributes(b.url, instance, user)
                            if rta['status'] == 'error':
                                return JsonResponse(
                                    dict(set_attributes=dict(request_status='error', request_error=rta['response'])))
                            url = rta['response']
                            rta = replace_text_attributes(b.title, instance, user)
                            if rta['status'] == 'error':
                                return JsonResponse(
                                    dict(set_attributes=dict(request_status='error', request_error=rta['response'])))
                            title = rta['response']
                            buttons.append(dict(type=b.button_type,
                                                url=url,
                                                title=title))
                    rta = replace_text_attributes(m.text, instance, user)
                    if rta['status'] == 'error':
                        return JsonResponse(
                            dict(set_attributes=dict(request_status='error', request_error=rta['response'])))
                    messages.append(
                        dict(attachment=
                            dict(type="template",
                                payload=dict(template_type="media",
                                            elements=[dict(media_type="image",
                                                            url=rta['response'],
                                                            buttons=buttons)]))))
                    response_field = response_field + 1
                else:
                    rta = replace_text_attributes(m.text, instance, user)
                    if rta['status'] == 'error':
                        return JsonResponse(
                            dict(set_attributes=dict(request_status='error', request_error=rta['response'])))
                    messages.append(
                        dict(attachment=
                            dict(type='image',
                                payload=dict(url=rta['response']))))

            elif field.field_type == 'quick_replies':
                message = dict(text='Responde: ', quick_replies=[])
                save_attribute = True
                for r in field.reply_set.all():
                    rta = replace_text_attributes(r.label, instance, user)
                    if rta['status'] == 'error':
                        return JsonResponse(
                            dict(set_attributes=dict(request_status='error', request_error=rta['response'])))
                    rep = dict(title=rta['response'])
                    message['quick_replies'].append(rep)
                    if r.attribute or r.redirect_block or r.session:
                        save_attribute = True
                        if r.value:
                            rep['set_attributes'] = {'last_reply': r.value, 'reply_id': r.id}
                        else:
                            rep['set_attributes'] = {'last_reply': '', 'reply_id': r.id}
                message['quick_reply_options'] = dict(process_text_by_ai=False, text_attribute_name='last_reply')
                attributes['save_text_reply'] = save_attribute
                messages.append(message)
                attributes['field_id'] = field.id

            elif field.field_type == 'save_values_block':
                response['redirect_to_blocks'] = [field.redirectblock.block]

            elif field.field_type == 'live_chat':
                user_channel = user.userchannel_set.filter(bot_id=user.bot_id)
                if user_channel.exists():
                    user_channel = user_channel.last()
                    user_channel.live_chat = True
                    historic = LiveChat(user_channel=user_channel, live_chat=True)
                    historic.save()
                    user_channel.save()

            elif field.field_type == 'user_input':
                attributes['save_user_input'] = True
                # The first decimal of 'position' represents the number of times the user failed the validation
                # For example: position = 1.2 means that the field position is 1, but the user has failed the validation
                #               2 times, so the following text is the third text
                # Here I just extract the decimal part to get the correct text
                user_input_try = round((float(position)*10 - int(position)*10))
                user_input_text = field.userinput_set.all().order_by('id')[user_input_try].text
                rta = replace_text_attributes(user_input_text, instance, user)
                if rta['status'] == 'error':
                    return JsonResponse(
                        dict(set_attributes=dict(request_status='error', request_error=rta['response'])))
                attributes['user_input_text'] = rta['response']
                attributes['field_id'] = field.id

            elif field.field_type == 'condition':
                satisfies_conditions = True
                # Revisar que todas las condiciones se cumplan
                for condition in field.condition_set.all():

                    # Revisar que el atributo existe, por defecto asumo que no
                    is_attribute_set = False
                    
                    # Revisar si el attributo es una secuencia
                    attribute_sequence = Attribute.objects.filter(name='sequence')
                    if attribute_sequence.exists() and condition.attribute == attribute_sequence.first():
                        #fetch names of suscribed sequences
                        ht_url = "{0}/api/0.1/uhts/getSequences/?user_id={1}".format(os.getenv('HOTTRIGGERS_DOMAIN'), user.id)
                        ht_response = requests.get(ht_url).json()
                        suscribed_to = ht_response['results'] if 'results' in ht_response else list()
                        
                        is_attribute_set = condition.value.strip() in suscribed_to
                        
                    # Reviso si el atributo es de instancia/embarazo
                    elif condition.attribute.entity_set.filter(id__in=[1, 2]).exists():
                        attribute = AttributeValue.objects.filter(attribute=condition.attribute,
                                                                instance=instance).order_by('id')
                        if attribute.exists():
                            is_attribute_set = True
                            attribute = attribute.last()
                        elif condition.condition != 'is_not_set':
                            satisfies_conditions = False
                    # Reviso si el atributo es de encargado/profesional
                    elif condition.attribute.entity_set.filter(id__in=[4, 5]).exists():
                        attribute = UserData.objects.filter(attribute=condition.attribute,
                                                            user=user).order_by('id')
                        if attribute.exists():
                            is_attribute_set = True
                            attribute = attribute.last()
                            attribute.value = attribute.data_value
                        elif condition.condition != 'is_not_set':
                            satisfies_conditions = False
                    # Si no existe el atributo, no satisface las condiciones (a menos que la condicion sea is not set)
                    elif condition.condition != 'is_not_set':
                        satisfies_conditions = False
                    # Revisar la condicion
                    if condition.condition == 'is_set':
                        satisfies_conditions = satisfies_conditions and is_attribute_set
                    elif condition.condition == 'is_not_set':
                        satisfies_conditions = satisfies_conditions and not is_attribute_set
                    elif condition.condition == 'equal':
                        satisfies_conditions = satisfies_conditions and (attribute.value == condition.value)
                    elif condition.condition == 'not_equal':
                        satisfies_conditions = satisfies_conditions and (attribute.value != condition.value)
                    elif condition.condition == 'in':
                        satisfies_conditions = satisfies_conditions and (attribute.value in condition.value.split(","))
                    elif condition.condition == 'lt':
                        try:
                            satisfies_conditions = satisfies_conditions \
                                                and (float(attribute.value) < float(condition.value))
                        except:
                            satisfies_conditions = False
                    elif condition.condition == 'gt':
                        try:
                            satisfies_conditions = satisfies_conditions \
                                                and (float(attribute.value) > float(condition.value))
                        except:
                            satisfies_conditions = False
                    elif condition.condition == 'lte':
                        try:
                            satisfies_conditions = satisfies_conditions \
                                                and (float(attribute.value) <= float(condition.value))
                        except:
                            satisfies_conditions = False
                    elif condition.condition == 'gte':
                        try:
                            satisfies_conditions = satisfies_conditions \
                                                and (float(attribute.value) >= float(condition.value))
                        except:
                            satisfies_conditions = False
                if not satisfies_conditions:
                    response_field = response_field + 1

            elif field.field_type == 'activate_ai' or field.field_type == 'deactivate_ai':
                attributes['AI_active'] = '' if field.field_type == 'deactivate_ai' else 1

            if fields.last().position < response_field:
                finish = 'true'
                response_field = 0
                # Guardar interaccion
                SessionInteraction.objects.create(user_id=user.id,
                                                instance_id=instance_id,
                                                type='session_finish',
                                                field=field,
                                                session=session)
            attributes['session_finish'] = finish
            attributes['position'] = response_field
            response['set_attributes'] = attributes
            response['messages'] = messages
            save_attributes = dict()
            for key_name in ['session', 'position', 'session_finish', 'save_user_input', 'save_text_reply', 'field_id', 'previous_field_id', 'AI_active']:
                if key_name in attributes:
                    save_attributes[key_name] = attributes[key_name]
            save_json_attributes(dict(set_attributes=save_attributes), instance, user)

        except Exception as e:
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_error=str(e))))
        return JsonResponse(response)


@method_decorator(csrf_exempt, name='dispatch')
class SaveLastReplyView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request, *args, **kwargs):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.SessionFieldReplyForm(post_data)
        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid params.')))
        
        user = form.cleaned_data['user_id']
        if user.userdata_set.filter(attribute__name='save_text_reply').exists()\
                and user.userdata_set.filter(attribute__name='save_user_input').exists():
            save_text_reply = user.userdata_set.filter(attribute__name='save_text_reply').last().data_value
            save_user_input = user.userdata_set.filter(attribute__name='save_user_input').last().data_value
            if save_text_reply == 'False' and save_user_input == 'False':
                return JsonResponse(dict(set_attributes=dict(session_finish=save_text_reply)))
        
        if form.cleaned_data['instance']:
            instance = form.cleaned_data['instance']
        else:
            if user.userdata_set.filter(attribute__name='instance').exists():
                instance = Instance.objects.get(id=user.userdata_set.
                                                filter(attribute__name='instance').last().data_value)
            else:
                instance = None
        
        instance_id = None
        is_input_valid = True
        attributes = dict()
        response = dict()
        if instance:
            instance_id = instance.id
        # field 
        if form.cleaned_data['field_id']:
            field = form.cleaned_data['field_id']
        else:
            if user.userdata_set.filter(attribute__name='field_id').exists():
                field = Field.objects.get(id=user.userdata_set.filter(attribute__name='field_id').last().data_value)
            else:
                return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                             request_error='User has no field')))
        # position
        if form.cleaned_data['position']:
            position = form.cleaned_data['position']
        else:
            if user.userdata_set.filter(attribute__name='position').exists():
                position = user.userdata_set.filter(attribute__name='position').last().data_value
            else:
                position = 0
        
        # Specific actions by field type
        if field.field_type == 'user_input':
            user_input_try = round((float(position)*10 - int(position)*10))
            user_input = field.userinput_set.all().order_by('id')[user_input_try]
            attribute_name = user_input.attribute.name
            reply_type = 'user_input'
            reply_value = None
            reply_text = form.data['last_reply']
            chatfuel_value = form.data['last_reply']
            if user_input.validation:
                is_input_valid = False
            else:
                is_input_valid = True
            if user_input.validation == 'date':
                date_variant = 'true'
                if user.userdata_set.filter(attribute__name='date_variant').exists():
                    date_variant = user.userdata_set.filter(attribute__name='date_variant').last().data_value
                validation_response = is_valid_date(reply_text, user.language.name, date_variant)
                if validation_response['set_attributes']['request_status'] == 'done':
                    is_input_valid = True
                    reply_text = validation_response['set_attributes']['childDOB']
                    chatfuel_value = validation_response['set_attributes']['childDOB']
                    attributes = validation_response['set_attributes']
                    save_json_attributes(validation_response, instance, user)
            if user_input.validation == 'number':
                is_input_valid = is_valid_number(str(reply_text))
            if user_input.validation == 'phone':
                is_input_valid = is_valid_phone(str(reply_text))
            if user_input.validation == 'email':
                is_input_valid = is_valid_email(str(reply_text))
            if user_input.validation and not is_input_valid:
                if user_input.session:
                    attributes['session_finish'] = 'false'
                    attributes['session'] = user_input.session.id
                    attributes['position'] = user_input.position
                # If it is the first failure of validation
                elif float(position) == 0 or int(position) == field.position+1:
                    attributes['position'] = float(field.position) + 0.1
                elif field.userinput_set.all().count() > user_input_try + 1:  # If it has more validations to make
                    attributes['position'] = float(position) + 0.1
                elif field.userinput_set.all().order_by('id').last().session:
                    attributes['session_finish'] = 'false'
                    attributes['session'] = field.userinput_set.all().order_by('id').last().session.id
                    attributes['position'] = field.userinput_set.all().order_by('id').last().position
        
        elif field.field_type == 'quick_replies':
            reply_value = None
            attribute_name = False
            reply_type = 'quick_reply'
            reply = field.reply_set.all().filter(
                Q(value=form.data['last_reply']) | Q(label__iexact=form.data['last_reply']))
            
            if reply.exists():
                reply_text = None
                r = reply.first()
                chatfuel_value = r.label
                if r.value:
                    try:
                        reply_value = int(r.value)
                        chatfuel_value = reply_value
                    except ValueError:
                        reply_text = r.value
                
                if r.attribute:
                    attribute_name = r.attribute.name

                if r.redirect_block:
                    response['redirect_to_blocks'] = [r.redirect_block]
                elif r.session:
                    attributes['session_finish'] = 'false'
                    attributes['session'] = r.session.id
                    attributes['position'] = r.position
            else:
                reply_text = form.data['last_reply']
                chatfuel_value = form.data['last_reply']
                if field.reply_set.first().attribute:
                    attribute_name = field.reply_set.first().attribute.name

        elif field.field_type == 'consume_service':
            reply_type = 'consume_service'
            reply_value = None
            reply_text = form.data['last_reply']
            attribute_name = 'last_reply'
            chatfuel_value = form.data['last_reply']

        # bot
        if form.data['bot_id']:
            bot_id = form.data['bot_id']
        else:
            bot_id = 0
        
        interactions = SessionInteraction.objects.filter(user_id=user.id,
                                                         instance_id=instance_id,
                                                         type='session_init',
                                                         session=field.session)
        if interactions.count() == 0:
            # Guardar interaccion
            SessionInteraction.objects.create(user_id=user.id,
                                              instance_id=instance_id,
                                              type='session_init',
                                              bot_id=int(bot_id),
                                              field=field,
                                              session=field.session)
        # Guardar interaccion
        SessionInteraction.objects.create(user_id=user.id,
                                          instance_id=instance_id,
                                          bot_id=int(bot_id),
                                          type=reply_type,
                                          value=reply_value,
                                          text=reply_text,
                                          field=field,
                                          session=field.session)
        
        if is_input_valid and attribute_name:
            # Guardar atributo instancia o embarazo

            if Entity.objects.get(id=1).attributes.filter(name=attribute_name).exists() \
                    or Entity.objects.get(id=2).attributes.filter(name=attribute_name).exists():
                attribute = Attribute.objects.filter(name=attribute_name)
                AttributeValue.objects.create(instance=instance, attribute=attribute.first(),
                                              value=chatfuel_value)
            # Guardar atributo usuario
            if Entity.objects.get(id=4).attributes.filter(name=attribute_name).exists() \
                    or Entity.objects.get(id=5).attributes.filter(name=attribute_name).exists():
                attribute = Attribute.objects.filter(name=attribute_name)
                UserData.objects.create(user=user, data_key=attribute_name, attribute=attribute.first(),
                                        data_value=chatfuel_value)
            if attribute_name == 'tipo_de_licencia':
                user.license = License.objects.get(name=chatfuel_value)
                user.save()
            if attribute_name == 'language':
                user.language = Language.objects.get(name=chatfuel_value)
                user.save()
            if attribute_name == 'user_type':
                user.entity = Entity.objects.get(name=chatfuel_value)
                user.save()
            # Si crea la instancia con fecha de nacimiento entonces terminó el registro
            if attribute_name == 'birthday':
                # Crear interaccion de fin de registro
                bot_interaction = BotInteraction.objects.get(name='finish_registration')
                UserInteraction.objects.create(bot_id=bot_id, user_id=user.id,
                                               interaction=bot_interaction, value=instance_id,
                                               created_at=datetime.now(), updated_at=datetime.now())
                if user.userdata_set.filter(data_key='user_reg', attribute_id='210').exists():
                    a = user.userdata_set.filter(data_key='user_reg', attribute_id='210').last()
                    a.data_value = 'registered'
                    a.save()
                else:
                    user.userdata_set.create(data_key='user_reg', data_value='registered', attribute_id='210')
                user.save()
        
        # consolidate response
        if attribute_name:
            attributes[attribute_name] = chatfuel_value
        attributes['save_text_reply'] = False
        response['set_attributes'] = attributes
        response['messages'] = []
        save_json_attributes(response, instance, user)
        return JsonResponse(response)


''' REMINDERS DATETIME '''

@method_decorator(csrf_exempt, name='dispatch')
class SaveReminderDateTimeView(View):

    def get(self, request, *args, **kwargs):
        return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid Method',
                                                     service_name='Get Reminder Datetime')))

    def post(self, request):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        input_attribute_name = post_data['attribute_name']
        user = MessengerUser.objects.all().filter(id=int(post_data['user_id']))
        
        if not user.exists() or not input_attribute_name:
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_error='Invalid data.',
                                                         service_name='Save Reminder Datetime')))
        user = user.first()
        country = str(post_data['country']).lower().strip() if 'country' in post_data else 'guatemala'
        input_time = str(post_data['time']).lower().strip() if 'time' in post_data else 'noche'
        input_day = str(post_data['week_day']).lower().strip() if 'week_day' in post_data else 'viernes'
        
        try:
            # Timezone
            user_timezone = pytz.country_timezones['GT'][0]
            identifiable_timezones = {
                'GT': 'guate|guatemala|salvador|honduras|costa rica|costa|nicaragua|mexico',
                'US': 'usa',
                'CO': 'colombia|peru',
                'VE': 'venezuela',
                'BR': 'brazil|brasil',
                'CL': 'chile',
            }
            for country_code, pattern in identifiable_timezones.items():
                if re.search(pattern, country):
                    user_timezone = pytz.country_timezones[country_code][0]
                    break
            reminder_datetime = timezone.localtime(timezone=pytz.timezone(user_timezone))
            
            # while there is no NLU we will handle it manually, using datetime format having monday as 0
            week_day = 0
            identifiable_week_days = {
                '0': 'monday|lunes|montag|segunda-feira|segunda feira',
                '1': 'tuesday|martes|dienstag|terça-feira|terça feira|terca-feira|terca feira',
                '2': 'wednsday|miercoles|miércoles|mittwoch|quarta-feira|quarta feira',
                '3': 'thursday|jueves|donnerstag|quinta-feira|quinta feira',
                '4': 'friday|viernes|freitag|sexta-feira|sexta feira',
                '5': 'saturday|sabado|sábado',
                '6': 'sunday|domingo'
            }
            for day, pattern in identifiable_week_days.items():
                if re.search(pattern, input_day):
                    week_day = int(day)
                    break
            reminder_datetime +=  timedelta(days=(week_day - reminder_datetime.weekday() ) % 7)

            # hour
            hour = 9
            identifiable_hours = {
                '9':  'morning|mañana|maniana|morgen|manhã|manha',
                '13': 'afternoon|tarde|mittag',
                '20': 'night|noche|nacht|noite',
            }
            for hour, pattern in identifiable_hours.items():
                if re.search(pattern, input_time):
                    hours = int(hour)
                    break
            reminder_datetime = reminder_datetime.replace(hour=hours, minute=0)
            
            # create attributes and userdata 
            input_attribute, new = Attribute.objects.get_or_create(name=input_attribute_name)
            user_data = UserData.objects.all().filter(user=user, attribute=input_attribute, data_key=input_attribute_name)
            
            if user_data.exists():
                user_data.update(data_value=reminder_datetime.isoformat())
            else:
                UserData.objects.update_or_create(user=user, attribute=input_attribute, data_key=input_attribute_name, data_value=reminder_datetime.isoformat())

        except Exception as e:
            return dict(set_attributes=dict(request_status='error', request_message=str(e)))
        
        return JsonResponse(dict(set_attributes=dict(request_status='done')))


''' CHATFUEL UTILITIES '''


@method_decorator(csrf_exempt, name='dispatch')
class BlockRedirectView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request, *args, **kwargs):
        post_data = self.request.POST if len(self.request.POST) > 0 else json.loads(self.request.body)
        form = forms.BlockRedirectForm(post_data or None)
        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='Error',
                                                         request_error='Next field not found.'),
                                     messages=[]))

        return JsonResponse(dict(
            redirect_to_blocks=[form.cleaned_data['next']]
        ))


@method_decorator(csrf_exempt, name='dispatch')
class ValidatesDateView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.ValidatesDateForm(post_data)
        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='error', request_message='Invalid params')))

        return JsonResponse(is_valid_date(form.data['date'], form.data['locale'][0:2], form.data['variant']))


@method_decorator(csrf_exempt, name='dispatch')
class CalculateWeeksView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.SingleDateForm(post_data)
        if not form.is_valid():
            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                         request_error='Invalid params')))

        return JsonResponse(dict(set_attributes=dict(Semanas_Embarazo="-%s" % (int(form.data['months']) * 4))))


@method_decorator(csrf_exempt, name='dispatch')
class DefaultDateValuesView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request):
        ps = Program.objects.filter(id=1)
        if not ps.exists():
            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                         request_error='Program not exists.')))
        levels = ps.first().levels.filter(assign_min__gte=0, assign_min__lte=31).order_by('assign_min')[:11]
        replies = []
        for l in levels:
            replies.append(dict(title="%s - %s" % (l.assign_min, l.assign_max), set_attributes=dict(level_number=l.pk)))
        print(replies)
        return JsonResponse(dict(messages=[dict(text='?', quick_replies=replies,
                                                quick_reply_options=dict(process_text_by_ai=False,
                                                                         text_attribute_name='level_number'))]))


@method_decorator(csrf_exempt, name='dispatch')
class SetDefaultDateValueView(View):

    def get(self, request, *args, **kwargs):
        raise Http404('Not found')

    def post(self, request):
        post_data = request.POST if len(request.POST) > 0 else json.loads(request.body)
        form = forms.SetDefaultDateValueForm(post_data)
        if not form.is_valid() or not form.data['level_number']:
            return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                         request_error='Invalid params.')))
        if form.data['level_number'].isdigit():
            levels = Program.objects.get(id=1).levels.filter(id=form.data['level_number'])
            if levels.exists():
                level = levels.first()
            else:
                return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                             request_error='Level id does not exist')))
        else:
            if form.data['level_number'].find('-') == -1:
                return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                             request_error='Level not found')))
            months = form.data['level_number'].split('-')
            assign_min = int(months[0])
            assign_max = int(months[1])
            levels = Program.objects.get(id=1).levels.filter(assign_min=assign_min, assign_max=assign_max)
            if levels.exists():
                level = levels.first()
            else:
                return JsonResponse(dict(set_attributes=dict(request_status='error',
                                                             request_error='Level with that range of months does not exist')))
        instance = form.cleaned_data['instance']
        today = datetime.now()
        limit = (level.assign_min + 1.5) * 30
        assign = today - timedelta(days=limit)
        attr = instance.attributevalue_set.create(attribute=Attribute.objects.get(name='birthday'), value=assign)
        gattr = instance.attributevalue_set.create(attribute=Attribute.objects.get(name='generic_birthday'),
                                                   value='true')
        print(gattr)
        return JsonResponse(dict(set_attributes=dict(
            request_status='done',
            birthday=attr.value,
            generic_birthday='true'
        )))


def is_valid_number(s):
    return s.replace(',', '', 1).isdigit() or s.replace('.', '', 1).isdigit()


def is_valid_phone(s):
    return s.isdigit()


def is_valid_email(s):
    return True


def is_valid_date(date, lang='es', variant='true'):
    months = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october',
              'november', 'december']
    # -----------------------------------------------------------------------------------------------------
    # Temporary translation while boto3 is not fixed
    translated_months = dict(january='enero', february='febrero', march='marzo', april='abril', may='mayo',
                             june='junio', july='julio', august='agosto', september='septiembre',
                             october='octubre', november='noviembre', december='diciembre')
    # Translate from spanish to english to be recognizable by parser
    date = date.replace('del', 'of')
    date = date.replace('de', 'of')
    for key in translated_months:
        date = date.replace(translated_months[key], key)
    region = os.getenv('region')
    #translate = boto3.client(service_name='translate', region_name=region, use_ssl=True)
    #result = translate.translate_text(Text=date,
    #                                  SourceLanguageCode="auto", TargetLanguageCode="en")
    try:
        if variant == 'true':
            date = parser.parse(date) #parser.parse(result.get('TranslatedText'))
        else:
            date = parser.parse(date, dayfirst=True) #parser.parse(result.get('TranslatedText'), dayfirst=True)
    except Exception as e:
        print(e)
        return dict(set_attributes=dict(request_status='error', request_message='Not a valid string date'))

    rel = relativedelta.relativedelta(datetime.now(), date)
    child_months = (rel.years * 12) + rel.months

    month = months[date.month - 1]
    locale_date = "%s de %s del %s" % (date.day, translated_months[month], date.year)
    #date_result = translate.translate_text(Text="%s %s, %s" % (month, date.day, date.year), SourceLanguageCode="en",
    #                                       TargetLanguageCode=lang)
    #locale_date = date_result.get('TranslatedText')
    # -----------------------------------------------------------------------------------------------------
    return dict(set_attributes=dict(
        childDOB=date,
        locale_date=locale_date,
        childMonths=child_months,
        request_status='done',
        childYears=rel.years,
        childExceedMonths=rel.months if rel.years > 0 else 0
    ))


# Replaces {{attribute_name}} by the actual value on a text
def replace_text_attributes(original_text, instance, user):
    cut_message = splitkeep(original_text, '}}')
    new_text = ""
    for c in cut_message:
        first_search = re.search(".*{{.*}}*", c)
        if first_search:
            idx = c.index('}')
            exc = c[(idx + 2):]
            attribute_name = c[c.find('{') + 2:idx]
            attribute_value = '-' + attribute_name + '-'
            if attribute_name == 'name':
                if instance is None:
                    return dict(status='error',
                                response='User has no instance for attribute {{%s}}' % attribute_name)
                attribute_value = instance.name
            elif attribute_name == 'username':
                attribute_value = user.username
            elif attribute_name == 'first_name':
                attribute_value = user.first_name
            elif attribute_name == 'last_name':
                attribute_value = user.last_name
            elif attribute_name == 'user_id' or attribute_name == 'user':
                attribute_value = str(user.id)
            elif attribute_name == 'instance_id':
                if instance is None:
                    return dict(status='error', response='User has no instance for attribute {{%s}}' % attribute_name)
                attribute_value = str(instance.id)
            elif attribute_name == 'licence_id':
                attribute_value = str(user.license_id)
            elif attribute_name == 'licence':
                if user.license is None:
                    return dict(status='error', response='User has no license')
                attribute_value = user.license.name
            elif attribute_name == 'entity_id':
                attribute_value = str(user.entity_id)
            elif attribute_name == 'entity':
                if user.entity is None:
                    return dict(status='error', response='User has no entity')
                attribute_value = user.entity.name
            elif attribute_name == 'language_id':
                attribute_value = str(user.language_id)
            elif attribute_name == 'language' or attribute_name == 'lang':
                if user.language is None:
                    return dict(status='error', response='User has no language')
                attribute_value = user.language.name
            elif attribute_name == 'bot_id' or attribute_name == 'bot':
                attribute_value = str(user.bot_id)
            elif attribute_name == 'program_id':
                if instance is None:
                    return dict(status='error', response='User has no instance for attribute {{%s}}' % attribute_name)
                attribute_value = str(instance.program_id)
            else:
                if Attribute.objects.filter(name=attribute_name, entity__in=[1, 2]).exists():
                    if instance is None:
                        return dict(status='error',
                                    response='User has no instance for attribute {{%s}}' % attribute_name)
                    attribute_value = instance.attributevalue_set.filter(attribute__name=attribute_name).order_by('id')
                    if attribute_value.exists():
                        attribute_value = attribute_value.last().value
                    else:
                        return dict(status='error',
                                    response='Instance %s has no attribute {{%s}}' % (instance.id, attribute_name))
                elif Attribute.objects.filter(name=attribute_name, entity__in=[4, 5]).exists():
                    attribute_value = user.userdata_set.filter(attribute__name=attribute_name).order_by('id')
                    if attribute_value.exists():
                        attribute_value = attribute_value.last().data_value
                    else:
                        return dict(status='error',
                                    response='User %s has no attribute %s' % (user.id, attribute_name))
                elif Attribute.objects.filter(name=attribute_name).exists():
                    return dict(status='error', response='Attribute {{%s}} is not assigned to Entity' % attribute_name)
                else:
                    return dict(status='error', response='Attribute {{%s}} does not exist' % attribute_name)
            text = c[:c.find('{')] + attribute_value + exc
            new_text = new_text + text
        else:
            new_text = new_text + c
    return dict(status='done', response=new_text)


# Split string but keep the delimiter
def splitkeep(s, delimiter):
    split = s.split(delimiter)
    return [substr + delimiter for substr in split[:-1]] + [split[-1]]


# Save attributes returned by services
def save_json_attributes(obj, instance, user):
    if 'set_attributes' in obj:
        for attribute_name in obj['set_attributes']:
            attribute = Attribute.objects.filter(name=attribute_name)
            if attribute.exists():
                attribute = attribute.last()
            else:
                attribute = Attribute.objects.create(name=attribute_name, type='string')
                Entity.objects.get(id=4).attributes.add(attribute)# Agregar atributo al usuario

            user_attribute = UserData.objects.filter(data_key=attribute_name, user_id=user.id)
            if user_attribute.exists():
                user_attribute = user_attribute.last()
                user_attribute.data_value = obj['set_attributes'][attribute_name]
                user_attribute.attribute_id = attribute.id
                user_attribute.save()
            else:
                UserData.objects.create(data_key=attribute_name,
                                        user_id=user.id,
                                        data_value=obj['set_attributes'][attribute_name],
                                        attribute_id=attribute.id)
    return True
