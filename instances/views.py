from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView, RedirectView
from django.contrib.auth.mixins import PermissionRequiredMixin
from instances.models import Instance, AttributeValue, Response
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
from posts.models import Post
from instances import forms
from programs.models import Program
from milestones.models import Milestone
import datetime
import calendar


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
        c['trabajo_motor'] = self.object.get_activities_area(2, timezone.now() + datetime.timedelta(days=-4),
                                                                timezone.now() + datetime.timedelta(days=1)
                                                             ).count()
        c['trabajo_cognitivo'] = self.object.get_activities_area(1, timezone.now() + datetime.timedelta(days=-4),
                                                                timezone.now() + datetime.timedelta(days=1)
                                                                 ).count()
        c['trabajo_socio'] = self.object.get_activities_area(3, timezone.now() + datetime.timedelta(days=-4),
                                                                timezone.now() + datetime.timedelta(days=1)
                                                             ).count()
        c['activities'] = [
            self.object.get_activities_area(0,  timezone.now() + datetime.timedelta(days=-4),
                                                timezone.now() + datetime.timedelta(days=1)).count(),
            self.object.get_activities_area(0,  timezone.now() + datetime.timedelta(days=-4),
                                                timezone.now() + datetime.timedelta(days=-3)).count(),
            self.object.get_activities_area(0,  timezone.now() + datetime.timedelta(days=-3),
                                                timezone.now() + datetime.timedelta(days=-2)).count(),
            self.object.get_activities_area(0,  timezone.now() + datetime.timedelta(days=-2),
                                                timezone.now() + datetime.timedelta(days=-1)).count(),
            self.object.get_activities_area(0,  timezone.now() + datetime.timedelta(days=-1),
                                                timezone.now() + datetime.timedelta(days=0)).count(),
            self.object.get_activities_area(0,  timezone.now() + datetime.timedelta(days=0),
                                                timezone.now() + datetime.timedelta(days=1)).count()
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
            age = relativedelta(timezone.now(), parse(self.object.get_attribute_values('birthday').value))
            months = 0
            if age.months:
                months = age.months
            if age.years:
                months = months + (age.years * 12)
        except:
            months = 0
        c['months'] = months
        return c


class InstanceMilestonesView(DetailView):
    model = Instance
    pk_url_kwarg = 'instance_id'
    template_name = 'instances/instance_milestones.html'

    def get_context_data(self, **kwargs):
        c = super(InstanceMilestonesView, self).get_context_data(**kwargs)
        months = 0
        if self.object.get_months():
            months = self.object.get_months()
        c['months'] = months
        levels = Program.objects.get(id=1).level_set.filter(assign_min__lte=months, assign_max__gte=months)
        responses = self.object.response_set.all()
        for area in Area.objects.filter(topic_id=1):
            c['trabajo_' + str(area.id)] = 0
            c['trabajo_' + str(area.id)+'_total'] = 0
            if levels.exists():
                print(levels.first().milestones.all().filter(areas__in=[area]))
                milestones = levels.first().milestones.filter(areas__in=[area]).order_by('value')
                for m in milestones:
                    m_responses = responses.filter(milestone_id=m.pk, response='done')
                    if m_responses.exists():
                        c['trabajo_'+str(area.id)] += 1
                    c['trabajo_'+str(area.id)+'_total'] += 1
        c['activities'] = self.object.get_completed_activities('session').count()
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


class InstanceMilestonesListView(DetailView):
    model = Instance
    pk_url_kwarg = 'instance_id'
    template_name = 'instances/milestones_list.html'

    def get_context_data(self, **kwargs):
        c = super(InstanceMilestonesListView, self).get_context_data()
        user = None
        months = 0
        if self.object.get_months():
            months = self.object.get_months()
        levels = Program.objects.get(id=1).level_set.filter(assign_min__lte=months, assign_max__gte=months)
        if 'key' in self.request.GET:
            fu = User.objects.filter(last_channel_id=self.request.GET['key'])
            if fu.exists():
                user = fu.first()
        print(user)

        responses = self.object.response_set.all()
        if levels.exists():
            c['level'] = levels.first()
            c['milestones'] = c['level'].milestones.all().order_by('value')
            for m in c['milestones']:
                m_responses = responses.filter(milestone_id=m.pk, response='done')
                m.label = m.milestonetranslation_set.get(language__name='es').name
                if user:
                    if user.get_language():
                        translations = m.milestonetranslation_set.filter(language__name=user.get_language())
                        if translations.exists():
                            m.label = translations.last().name
                if m_responses.exists():
                    m.finished = True
                else:
                    m.finished = False
        return c


class CompleteMilestoneView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        new_response = Response.objects.create(milestone_id=kwargs['milestone_id'], instance_id=kwargs['instance_id'],
                                               response='done', created_at=timezone.now())
        print(new_response)
        messages.success(self.request, 'Se han realizado los cambios.')
        return reverse_lazy('instances:milestones_list', kwargs=dict(instance_id=kwargs['instance_id']))


class ReverseMilestoneView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        responses = Response.objects.filter(instance_id=kwargs['instance_id'], milestone_id=kwargs['milestone_id'],
                                            response='done')
        for r in responses:
            r.delete()
        messages.success(self.request, 'Se han realizado los cambios.')
        return reverse_lazy('instances:milestones_list', kwargs=dict(instance_id=kwargs['instance_id']))