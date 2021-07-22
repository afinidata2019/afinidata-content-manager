from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView, RedirectView, TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from instances.models import Instance, AttributeValue, Response, ScoreTracking, Score
from django.shortcuts import get_object_or_404
from messenger_users.models import User, UserData
from user_sessions.models import Field, Interaction as SessionInteraction
from django.urls import reverse_lazy
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.utils import timezone
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from areas.models import Area
from languages.models import Language
from posts.models import Post, Interaction as PostInteraction
from instances import forms
from programs.models import Program, Level
from groups.models import Group, ProgramAssignation, MilestoneRisk
from django.shortcuts import redirect
import datetime
import calendar
from programs.models import Level
from django.db import connection
import math
# from datetime import datetime

class HomeView(PermissionRequiredMixin, ListView):
    permission_required = 'instances.view_all_instances'
    model = Instance
    paginate_by = 30
    login_url = reverse_lazy('static:login')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(HomeView, self).get_context_data()
        return context


class InstanceView(PermissionRequiredMixin, DetailView):
    permission_required = 'instances.view_instance'
    model = Instance
    pk_url_kwarg = 'id'
    login_url = reverse_lazy('static:login')

    def get_context_data(self, **kwargs):
        c = super(InstanceView, self).get_context_data()
        c['today'] = timezone.now()
        c['first_month'] = parse("%s-%s-%s" % (c['today'].year, c['today'].month, 1))
        c['interactions'] = self.object.get_time_interactions(c['first_month'], c['today'])
        c['feeds'] = self.object.get_time_feeds(c['first_month'], c['today'])
        c['posts'] = Post.objects.filter(id__in=[x.post_id for x in c['interactions']]).only('id', 'name', 'area_id')
        c['completed_activities'] = 0
        c['assigned_activities'] = 0
        c['areas'] = Area.objects.all()
        for area in c['areas']:
            area.assigned_activities = 0
            area.completed_activities = 0
            area.feeds = c['feeds'].filter(area=area).order_by('created_at')
            print(area.feeds)
        for post in c['posts']:
            post.last_assignation = post.get_user_last_dispatched_interaction(self.object, c['first_month'], c['today'])
            post.last_session = post.get_user_last_session_interaction(self.object, c['first_month'], c['today'])
            if post.last_session:
                c['completed_activities'] = c['completed_activities'] + 1
            if post.last_assignation:
                c['assigned_activities'] = c['assigned_activities'] + 1
            for area in c['areas']:
                if post.last_assignation:
                    if area.pk == post.area_id:
                        area.assigned_activities = area.assigned_activities + 1
                if post.last_session:
                    if area.pk == post.area_id:
                        area.completed_activities = area.completed_activities + 1

        c['labels'] = [parse("%s-%s-%s" %
                             (c['today'].year, c['today'].month, day)) for day in range(1, c['today'].day + 1)]
        quick_replies = []
        replies = SessionInteraction.objects.filter(instance_id=54510)
        for reply in replies:
            rep = dict()
            position = Field.objects.filter(id=reply.field_id).first().position - 1

            rep['attribute'] = 'Atributo'
            rep['question'] = 0
            rep['answer'] = 'Pregunta'
            rep['value'] = reply.value
            rep['response'] = AttributeValue.objects.filter(instance_id=54510).last().value
            quick_replies.append(rep)
        c['quick_replies'] = quick_replies
        return c


class InstanceReportView(DetailView):
    model = Instance
    pk_url_kwarg = 'instance_id'
    template_name = 'instances/instance_report.html'

    def get_context_data(self, **kwargs):
        c = super(InstanceReportView, self).get_context_data(**kwargs)
        instance_interactions = PostInteraction.objects. \
            filter(instance_id=self.object.id, type='session', value__gte=0,
                   created_at__gte=timezone.now() + datetime.timedelta(days=-4))
        interactions = list(instance_interactions)
        c['trabajo_motor'] = Post.objects.\
            filter(id__in=[x.post_id for x in interactions]).filter(area_id=2).count()
        c['trabajo_cognitivo'] = Post.objects.\
            filter(id__in=[x.post_id for x in interactions]).filter(area_id=1).count()
        c['trabajo_socio'] = Post.objects.\
            filter(id__in=[x.post_id for x in interactions]).filter(area_id=3).count()
        c['activities'] = [
            len(set([interaction.post_id for interaction in interactions])),
            len(set([interaction.post_id for interaction in interactions
                     if timezone.now() + datetime.timedelta(days=-4) <=
                     interaction.created_at <= timezone.now() + datetime.timedelta(days=-3)])),
            len(set([interaction.post_id for interaction in interactions
                     if timezone.now() + datetime.timedelta(days=-3) <=
                     interaction.created_at <= timezone.now() + datetime.timedelta(days=-2)])),
            len(set([interaction.post_id for interaction in interactions
                     if timezone.now() + datetime.timedelta(days=-2) <=
                     interaction.created_at <= timezone.now() + datetime.timedelta(days=-1)])),
            len(set([interaction.post_id for interaction in interactions
                     if timezone.now() + datetime.timedelta(days=-1) <=
                     interaction.created_at <= timezone.now() + datetime.timedelta(days=0)])),
            len(set([interaction.post_id for interaction in interactions
                     if timezone.now() + datetime.timedelta(days=0) <=
                     interaction.created_at <= timezone.now() + datetime.timedelta(days=1)]))
        ]
        try:
            objective = UserData.objects.filter(user=self.object.instanceassociationuser_set.last().user_id).\
                                            filter(data_key='tiempo_intensidad').last().data_value
            if objective == '10 min':
                c['objective'] = 1
            elif objective == '30 min':
                c['objective'] = 3
            else:
                c['objective'] = 6
        except:
            c['objective'] = 6
        try:
            age = relativedelta(datetime.datetime.now(), parse(self.object.get_attribute_values('birthday').value))
            months = 0
            if age.months:
                months = age.months
            if age.years:
                months = months + (age.years * 12)
        except:
            months = 0
        c['months'] = months
        levels = Program.objects.get(id=1).levels.filter(assign_min__lte=months, assign_max__gte=months)
        level = levels.first()
        lang = Language.objects.get(id=self.object.get_users().first().language_id).name
        c['image_name'] = 'images/'+level.image
        c['etapa'] = level.name
        if level.levellanguage_set.filter(language__name=lang).exists():
            c['etapa'] = level.levellanguage_set.filter(language__name=lang).first().name
        c['lang'] = lang
        return c


class NewInstanceView(PermissionRequiredMixin, CreateView):
    permission_required = 'instances.add_instance'
    model = Instance
    form_class = forms.InstanceModelForm
    login_url = reverse_lazy('static:login')

    def get_context_data(self, **kwargs):
        c = super(NewInstanceView, self).get_context_data()
        c['action'] = 'Create'
        return c

    def form_valid(self, form):
        users = User.objects.filter(id=form.cleaned_data['user_id'])
        if not users.count() > 0:
            form.add_error('user_id', 'User ID is not valid')
            messages.error(self.request, 'User ID is not valid')
            return super(NewInstanceView, self).form_invalid(form)

        return super(NewInstanceView, self).form_valid(form)

    def get_success_url(self):
        self.object.instanceassociationuser_set.create(user_id=self.request.POST['user_id'])
        messages.success(self.request, 'Instance with name: "%s" has been created.' % self.object.name)
        return reverse_lazy('instances:instance', kwargs={'id': self.object.pk})


class EditInstanceView(PermissionRequiredMixin, UpdateView):
    permission_required = 'instances.change_instance'
    model = Instance
    fields = ('name',)
    pk_url_kwarg = 'id'
    context_object_name = 'instance'
    login_url = reverse_lazy('static:login')

    def get_context_data(self, **kwargs):
        c = super(EditInstanceView, self).get_context_data()
        c['action'] = 'Edit'
        return c

    def get_success_url(self):
        messages.success(self.request, 'Instance with name "%s" has been updated.' % self.object.name)
        return reverse_lazy('instances:instance', kwargs={'id': self.object.pk})


class DeleteInstanceView(PermissionRequiredMixin, DeleteView):
    permission_required = 'instances.delete_instance'
    model = Instance
    template_name = 'instances/instance_form.html'
    pk_url_kwarg = 'id'
    success_url = reverse_lazy('instances:index')
    login_url = reverse_lazy('static:login')

    def get_context_data(self, **kwargs):
        c = super(DeleteInstanceView, self).get_context_data()
        c['action'] = 'Delete'
        c['delete_message'] = 'Are you sure to delete instance with name: "%s"?' % self.object.name
        return c

    def get_success_url(self):
        messages.success(self.request, 'Instance with name: "%s" has been deleted.' % self.object.name)
        return super(DeleteInstanceView, self).get_success_url()


class AddAttributeToInstanceView(PermissionRequiredMixin, CreateView):
    permission_required = 'instances.add_attributevalue'
    model = AttributeValue
    fields = ('attribute', 'value')

    def get_context_data(self, **kwargs):
        instance = Instance.objects.get(id=self.kwargs['instance_id'])
        c = super(AddAttributeToInstanceView, self).get_context_data()
        c['instance'] = instance
        c['action'] = 'Create'
        c['form'].fields['attribute'].queryset = instance.entity.attributes.all()
        return c

    def form_valid(self, form):
        form.instance.instance_id = self.kwargs['instance_id']
        return super(AddAttributeToInstanceView, self).form_valid(form)

    def get_success_url(self):
        messages.success(self.request, 'The value "%s" for attribute "%s" for instance: "%s" has been added' % (
            self.object.value, self.object.attribute.name, self.object.instance
        ))
        return reverse_lazy('instances:instance', kwargs={'id': self.object.instance.pk})


class AttributeValueEditView(PermissionRequiredMixin, UpdateView):
    permission_required = 'instances.change_attributevalue'
    template_name = 'instances/attributevalue_edit_form.html'
    model = AttributeValue
    fields = ('value',)
    pk_url_kwarg = 'attribute_id'
    login_url = reverse_lazy('static:login')

    def get_context_data(self, **kwargs):
        c = super(AttributeValueEditView, self).get_context_data()
        print(self.kwargs['instance_id'], self.object.instance.pk)
        c['action'] = 'Edit'
        return c

    def get_success_url(self):
        messages.success(self.request, 'The value "%s" for attribute "%s" for instance: "%s" has been updated' % (
            self.object.value, self.object.attribute.name, self.object.instance
        ))
        return reverse_lazy('instances:instance', kwargs={'id': self.object.instance.pk})


class ProgramInstanceReportView(DetailView):
    model = Instance
    pk_url_kwarg = 'instance_id'
    template_name = 'instances/new_program_report.html'
    context_object_name = 'instance'

    def calculate_months_instance(self, id, fecha):
        cumple = AttributeValue.objects.filter(attribute__name='birthday', instance_id=id).order_by('-id')
        if cumple.exists():
            cumple = cumple.first()
        else:
            return 0
        try:
            start_date = datetime.datetime.strptime(str(cumple.value[0:10]), '%Y-%m-%d')
            end_date = datetime.datetime.strptime(str(fecha[0:7]), '%Y-%m')
        except ValueError:
            try:
                start_date = datetime.datetime.strptime(str(cumple.value[0:10]), '%d/%m/%Y')
                end_date = datetime.datetime.strptime(str(fecha[3:10]), '%m/%Y')
            except ValueError:
                return 0
        return (12 * end_date.year + end_date.month) - (12 * start_date.year + start_date.month)

    def get_context_data(self, **kwargs):
        context = super(ProgramInstanceReportView, self).get_context_data(**kwargs)

        id = self.kwargs['instance_id']

        context['score'] = Score.objects.filter(instance_id=id)

        # dinamic data for chart
        cursor = connection.cursor()
        sql = """
        select  sum(value) as valor, date_format(created_at, '%%Y-%%m') as fecha
        from instances_scoretracking
        where instance_id= %s
        group by date_format(created_at, '%%Y-%%m')
        """
        cursor.execute(sql, [id])
        score_tracking = cursor.fetchall()

        data = []
        labels = []

        if(score_tracking):
            data.append(0)
            labels.append(0)
            for i, s in enumerate(score_tracking):
                data.append(int(math.ceil(s[0])))
                labels.append(self.calculate_months_instance(id,s[1]))

        context['data'] = data
        context['labels'] = labels
        meses = 0
        if self.object.get_months():
            meses = self.object.get_months()

        context['meses'] = meses

        niveles = Program.objects.get(id=1).levels.filter(assign_min__lte=meses, assign_max__gte=meses)

        context['nivel'] = niveles.first()
        context['overall'] = sum([ x.value for x in context['score']])

        context['sesiones_completadas'] = PostInteraction.objects.filter(
            value__gt=-1,
            instance_id=id,
            type="session"
        ).count()
        # Get the number of active (milestones) sessions to see if there are some remaining questions to answer
        context['active_sessions'] = self.object.response_set.filter(session__active=1).values('session').distinct().count()
        # Get the program
        user = self.object.get_users().first()
        group = Group.objects.filter(assignationmessengeruser__user_id=user.pk).first()
        program = group.programs.first()
        # Get the milestones texts that represent risks
        milestones_risks = self.object.get_risk_milestones_text(program)
        context['milestones_risks'] = len(milestones_risks)
        context.update(milestones_risks)
        return context
