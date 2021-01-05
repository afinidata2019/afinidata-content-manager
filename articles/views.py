from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import PermissionRequiredMixin
from messenger_users.models import User
from django.urls import reverse_lazy
from django.contrib import messages
from topics.models import Topic
from articles import models
import os


class ArticleInfoDetailView(DetailView):
    model = models.Article
    pk_url_kwarg = 'article_id'
    template_name = 'articles/article_info_detail.html'


class ArticleDetailView(DetailView):
    model = models.Article
    pk_url_kwarg = 'article_id'

    def get_context_data(self, **kwargs):
        c = super(ArticleDetailView, self).get_context_data()

        if 'user_id' in self.request.GET:
            instance = None
            default_license = 'free'
            user = User.objects.get(id=self.request.GET['user_id'])
            licenses = user.userdata_set.filter(data_key='tipo_de_licencia')
            if licenses.count() > 0:
                default_license = licenses.last().data_value
            c['object'].content = c['object'].content + "?license=premium"
            if 'instance' in self.request.GET:
                instance = self.request.GET['instance']
            new_opened = self.object.interaction_set.create(user_id=user.pk, instance_id=instance)
            new_session = self.object.interaction_set.create(user_id=user.pk, instance_id=instance, type='session')
            c['session_id'] = new_session.pk
        return c


class ArticleListView(PermissionRequiredMixin, ListView):
    permission_required = 'articles.view_article'
    model = models.Article
    paginate_by = 20


class ArticleCreateView(PermissionRequiredMixin, CreateView):
    permission_required = 'articles.add_article'
    model = models.Article
    fields = ('name', 'type', 'content', 'text_content', 'topics', 'min', 'max', 'preview', 'thumbnail', 'campaign',
              'programs')

    def get_context_data(self, **kwargs):
        c = super(ArticleCreateView, self).get_context_data()
        c['action'] = 'Create'
        return c
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super(ArticleCreateView, self).form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "Article with ID %s has been created. " % self.object.pk)
        return reverse_lazy('articles:article_edit', kwargs={'article_id': self.object.pk})


class ArticleUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = 'articles.change_article'
    model = models.Article
    fields = ('name', 'type', 'content', 'text_content', 'topics', 'min', 'max', 'preview', 'thumbnail', 'campaign',
              'programs')
    pk_url_kwarg = 'article_id'

    def get_context_data(self, **kwargs):
        c = super(ArticleUpdateView, self).get_context_data()
        c['action'] = 'Edit'
        return c

    def get_success_url(self):
        messages.success(self.request, "Article with ID %s has been updated. " % self.object.pk)
        return reverse_lazy('articles:article_info', kwargs={'article_id': self.object.pk})


class TopicDetailView(DetailView):
    model = Topic
    pk_url_kwarg = 'topic_id'

    def get_context_data(self, **kwargs):
        c = super(TopicDetailView, self).get_context_data()
        print(self.request.GET)
        return c


class TopicListView(PermissionRequiredMixin, ListView):
    permission_required = 'articles.view_topic'
    model = Topic
    paginate_by = 20


class TopicCreateView(PermissionRequiredMixin, CreateView):
    permission_required = 'articles.add_topic'
    model = Topic
    fields = ('name', )

    def get_context_data(self, **kwargs):
        c = super(TopicCreateView, self).get_context_data()
        c['action'] = 'Create'
        return c

    def form_valid(self, form):
        return super(TopicCreateView, self).form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "Topic with ID %s has been created. " % self.object.pk)
        return reverse_lazy('articles:topic_edit', kwargs={'topic_id': self.object.pk})


class TopicUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = 'articles.change_topic'
    model = Topic
    fields = ('name', )
    pk_url_kwarg = 'topic_id'

    def get_context_data(self, **kwargs):
        c = super(TopicUpdateView, self).get_context_data()
        c['action'] = 'Edit'
        return c

    def get_success_url(self):
        messages.success(self.request, "Topic with ID %s has been updated. " % self.object.pk)
        return reverse_lazy('articles:topic_edit', kwargs={'topic_id': self.object.pk})


class ArticleTranslateDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'articles.view_articletranslate'
    model = models.ArticleTranslate
    login_url = reverse_lazy('static:login')
    pk_url_kwarg = 'translate_id'


class ArticleTranslateCreateView(PermissionRequiredMixin, CreateView):
    permission_required = 'articles.add_articletranslate'
    model = models.ArticleTranslate
    fields = ('language', 'name', 'content', 'text_content', 'preview')
    login_url = reverse_lazy('static:login')

    def get_context_data(self, **kwargs):
        c = super(ArticleTranslateCreateView, self).get_context_data(**kwargs)
        c['action'] = 'Create'
        c['article'] = models.Article.objects.get(id=self.kwargs['article_id'])
        return c
    
    def form_valid(self, form):
        form.instance.article_id = self.kwargs['article_id']
        return super(ArticleTranslateCreateView, self).form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "The translate has been created.")
        return reverse_lazy('articles:article_info', kwargs=dict(article_id=self.kwargs['article_id']))


class ArticleTranslateEditView(PermissionRequiredMixin, UpdateView):
    permission_required = 'articles.change_articletranslate'
    model = models.ArticleTranslate
    fields = ('language', 'name', 'content', 'text_content', 'preview')
    login_url = reverse_lazy('static:login')
    pk_url_kwarg = 'translate_id'

    def get_context_data(self, **kwargs):
        c = super(ArticleTranslateEditView, self).get_context_data(**kwargs)
        c['action'] = 'Edit'
        c['article'] = models.Article.objects.get(id=self.kwargs['article_id'])
        return c

    def form_valid(self, form):
        form.instance.article_id = self.kwargs['article_id']
        return super(ArticleTranslateEditView, self).form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "The translate has been updated.")
        return reverse_lazy('articles:article_info', kwargs=dict(article_id=self.kwargs['article_id']))


class ArticleTranslateDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = 'articles.delete_articletranslate'
    model = models.ArticleTranslate
    login_url = reverse_lazy('static:login')
    pk_url_kwarg = 'translate_id'

    def get_context_data(self, **kwargs):
        c = super(ArticleTranslateDeleteView, self).get_context_data(**kwargs)
        c['action'] = 'Delete'
        return c

    def get_success_url(self):
        messages.success(self.request, "The translate has been deleted.")
        return reverse_lazy('articles:article_info', kwargs=dict(article_id=self.kwargs['article_id']))
