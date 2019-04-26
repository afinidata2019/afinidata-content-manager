from django.views.generic import TemplateView, UpdateView, CreateView, DeleteView, DetailView, ListView
from posts.models import Post, Interaction, Feedback, Label, Question, Response
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from posts.forms import CreatePostForm
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from messenger_users.models import User
from datetime import datetime, timedelta, date
from django.urls import reverse_lazy
import math
import random
import pytz
import requests


class HomeView(TemplateView):
    template_name = 'posts/index.html'


def post(request, id):

    if request.method == 'GET':
        post = Post.objects.get(id=id)
        user = None
        try:
            username = request.GET['username']
            user = User.objects.get(username=username)
            print('user: ', user)
        except:
            print('not user with username')
            pass

        if not user:
            try:
                channel_id = request.GET['channel_id']
                user = User.objects.get(last_channel_id=channel_id)
                print(user)
            except:
                print('not user with last channel id')
                pass

        if not user:
            try:
                channel_id = request.GET['channel_id']
                user = User.objects.get(channel_id=channel_id)
                print(user)
            except:
                print('not user with channel id')
                pass

        if user:
            try:

                bot_id = request.GET['bot_id']
                Interaction\
                    .objects\
                    .create(
                        post=post,
                        channel_id=user.last_channel_id,
                        username=user.username,
                        bot_id=bot_id,
                        type='opened',
                        user_id=user.pk
                )
                post_session = Interaction(post=post,
                                           channel_id=user.last_channel_id,
                                           bot_id=bot_id,
                                           username=user.username,
                                           type='session',
                                           user_id=user.pk,
                                           value=-1)
                post_session.save()
                return render(request, 'posts/post.html',
                              {'post': post, 'session_id': post_session.pk})
            except:

                return render(request, 'posts/post.html', {'post': post, 'session_id': 'null'})
        
        return render(request, 'posts/post.html', {'post': post, 'session_id': 'null'})


class StatisticsView(TemplateView):
    template_name = 'posts/statistics.html'

    def get_context_data(self, **kwargs):
        #context = super().get_context_data(**kwargs)
        context = dict()
        view_post = Post.objects.get(id=kwargs['id'])
        clicks = view_post.interaction_set.filter(type='opened')
        sessions = view_post.interaction_set.filter(type='session')
        feedbacks = view_post.feedback_set.all()
        users = set()
        context['post'] = view_post
        context['clicks'] = clicks
        context['sessions'] = sessions
        context['domain'] = settings.DOMAIN_URL

        sessions_minutes = 0
        for session in sessions:
            users.add(session.user_id)
            if session.value != 0:
                sessions_minutes = sessions_minutes + int(session.value)
            else:
                sessions_minutes = sessions_minutes + .3

        context['channel_users'] = len(users)

        sessions_minutes = math.floor(sessions_minutes)
        context['session_minutes'] = sessions_minutes
        if sessions.count() > 0:
            context['session_average'] = round(sessions_minutes / int(sessions.count()), 2)
        else:
            context['session_average'] = 0

        feedback_total = 0

        for feedback in feedbacks:
            feedback_total = feedback_total + int(feedback.value)

        context['feedback_total'] = feedback_total
        if feedbacks.count() > 0:
            context['feedback_average'] = round(feedback_total / feedbacks.count(), 2)
        else:
            context['feedback_average'] = 0
        context['feedback_ideal'] = feedbacks.count() * 5

        return context


class NewPostView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ('name', 'author', 'thumbnail', 'new', 'type', 'min_range', 'max_range', 'area_id', 'content',
              'content_activity', 'preview')
    template_name = 'posts/new.html'
    login_url = '/admin/login/'
    redirect_field_name = 'redirect_to'

    def form_valid(self, form):
        post = form.save()
        return redirect('posts:edit-post', id=post.pk)


class EditPostView(LoginRequiredMixin, UpdateView):
    login_url = '/admin/login/'
    redirect_field_name = 'redirect_to'
    model = Post
    pk_url_kwarg = 'id'
    context_object_name = 'post'
    fields = ('name', 'author', 'thumbnail', 'new', 'type', 'min_range', 'max_range', 'area_id', 'content',
              'content_activity', 'preview')
    template_name = 'posts/sedit.html'

    def form_valid(self, form):
        post = form.save()
        return redirect('posts:edit-post', id=post.pk)


def new_post(request):

    form = CreatePostForm(request.POST or None)

    if form.is_valid():

        data = form.cleaned_data

        saved_post = Post.objects.create(**data)

        return redirect('posts:edit-post', id=saved_post.pk)

    try:
        if request.GET['quest'] == 'afini':

            return render(request, 'posts/new.html', {'form': form})

        else:
            raise Http404('Not found')
    except:
        raise Http404('Not found')

@csrf_exempt
def edit_interaction(request, id):

    if request.method == 'POST':

        print(request.POST)

        try:
            interaction = Interaction.objects.filter(pk=id).update(value=request.POST['minutes'])
            return JsonResponse(dict(
                status='updated',
                interaction=interaction
            ))
        except:
            raise Http404('Error')

    else:
        return JsonResponse(dict(hello="world"))


@csrf_exempt
def set_user_send(request):
    if request.method == 'POST':
        user = None
        post_id = None
        bot_id = None
        print(request.POST)
        try:
            username = request.POST['username']
            user = User.objects.get(username=username)
            print('user: ', user)
        except:
            print('not user with username')
            pass

        if not user:
            try:
                channel_id = request.POST['channel_id']
                user = User.objects.get(last_channel_id=channel_id)
                print(user)
            except:
                print('not user with last channel id')
                pass

        if not user:
            try:
                channel_id = request.POST['channel_id']
                user = User.objects.get(channel_id=channel_id)
                print(user)
            except:
                print('not user with channel id')
                pass

        if not user:
            return JsonResponse(dict(status='error', error='not user defined'))

        try:
            post_id = request.POST['post_id']
            selected_post = Post.objects.get(pk=post_id)
            print(selected_post)
        except:
            return JsonResponse(dict(status='error', error='not post with id or id not defined'))

        try:
            bot_id = request.POST['bot_id']
        except:
            bot_id = 1

        new_interaction = Interaction.objects.create(
            post=selected_post,
            channel_id=user.last_channel_id,
            username=user.username,
            bot_id=bot_id,
            type='sended',
            user_id=user.pk
        )

        return JsonResponse(dict(
            status='created',
            data=dict(
                user_id=user.pk,
                post_id=selected_post.pk,
                type='sended'
            )
        ))
    else:
        raise Http404('Not found')


@csrf_exempt
def feedback(request):
    if request.method == 'POST':
        user = None
        print(request.POST)
        try:
            username = request.POST['username']
            user = User.objects.get(username=username)
            print('user: ', user)
        except:
            print('not user with username')
            pass

        if not user:
            try:
                channel_id = request.POST['channel_id']
                user = User.objects.get(last_channel_id=channel_id)
                print(user)
            except:
                print('not user with last channel id')
                pass

        if not user:
            try:
                channel_id = request.POST['channel_id']
                user = User.objects.get(channel_id=channel_id)
                print(user)
            except:
                print('not user with channel id')
                pass

        try:
            if request.POST \
               and len(request.POST) >= 4 \
               and request.POST['bot_id'] \
               and user \
               and request.POST['post_id'] \
               and request.POST['value']:
                print(request.POST)
                active_feedback = Feedback.objects.filter(bot_id=request.POST['bot_id'],
                                                          user_id=user.pk,
                                                          post_id=request.POST['post_id'])
                if not active_feedback:
                    if 1 <= int(request.POST['value']) <= 5:
                        new_feedback = Feedback.objects.create(bot_id=request.POST['bot_id'],
                                                               channel_id=user.last_channel_id,
                                                               post_id=request.POST['post_id'],
                                                               user_id=user.pk,
                                                               value=request.POST['value'],
                                                               username=user.username)

                        return JsonResponse(dict(status='created',
                                                 data=dict(
                                                     id=new_feedback.pk,
                                                     post_id=new_feedback.post_id,
                                                     user_id=new_feedback.user_id,
                                                     bot_id=new_feedback.bot_id,
                                                     value=new_feedback.value,
                                                     username=user.username
                                                 )))
                    else:
                        return JsonResponse(dict(status='error',
                                                 error='value is not valid'))
                else:
                    change_feedback = Feedback.objects.get(bot_id=request.POST['bot_id'],
                                                           user_id=user.pk,
                                                           post_id=request.POST['post_id'])

                    if change_feedback.value != int(request.POST['value']) \
                       and 1 <= int(request.POST['value']) <= 5:

                        change_feedback.value = request.POST['value']
                        change_feedback.save(update_fields=['value'])
                        return JsonResponse(dict(status='updated',
                                                 data=dict(
                                                     id=change_feedback.pk,
                                                     post_id=change_feedback.post_id,
                                                     user_id=change_feedback.user_id,
                                                     bot_id=change_feedback.bot_id,
                                                     value=change_feedback.value,
                                                     username=user.username
                                                 )))
                    else:
                        return JsonResponse(dict(status='not-updated',
                                                 data=dict(
                                                     id=change_feedback.pk,
                                                     post_id=change_feedback.post_id,
                                                     user_id=change_feedback.user_id,
                                                     bot_id=change_feedback.bot_id,
                                                     value=change_feedback.value,
                                                     username=user.username
                                                 )))

            else:
                return JsonResponse(dict(status='error',
                                         error='invalid params'))
        except Exception as e:
            return JsonResponse(dict(status='error',
                                     error='invalid params'))

    else:
        raise Http404('Not found')


def edit_post(request, id):

    if request.method == 'GET':

        try:
            post_to_edit = Post.objects.get(id=id)
            return render(request, 'posts/edit.html', {'post': post_to_edit})
        except:
            raise Http404('Not found')

    else:
        new = False
        try:
            new = True if request.POST['new'] else False
        except:
            pass
        try:
            post_to_edit = Post.objects.get(id=request.POST['id'])
            post_to_edit.name = request.POST['name'] if request.POST['name'] else None
            post_to_edit.content = request.POST['content'] if request.POST['content'] else None
            post_to_edit.type = request.POST['type'] if request.POST['type'] else None
            post_to_edit.author = request.POST['author'] if request.POST['author'] else None
            post_to_edit.min_range = request.POST['min_range'] if request.POST['min_range'] else None
            post_to_edit.max_range = request.POST['max_range'] if request.POST['max_range'] else None
            post_to_edit.area_id = request.POST['area_id'] if request.POST['area_id'] else None
            post_to_edit.preview = request.POST['preview'] if request.POST['preview'] else None
            post_to_edit.thumbnail = request.POST['thumbnail'] if request.POST['thumbnail'] else None
            post_to_edit.content_activity = request.POST['content_activity'] if request.POST['content_activity'] else None
            post_to_edit.new = new
            result = post_to_edit.save()
        except:
            print('not found')
            pass
        return redirect('posts:edit-post', id=id)


class DeletePostView(LoginRequiredMixin, DeleteView):
    login_url = '/admin/login/'
    redirect_field_name = 'redirect_to'
    model = Post
    template_name = 'posts/delete.html'
    pk_url_kwarg = 'id'
    context_object_name = 'post'

    success_url = '/posts/list/?quest=afini'


@csrf_exempt
def create_tag(request):

    if request.method == 'POST':
        print(request)
        try:
            name = request.POST['name']
        except:
            name = None
        if not name:
            return JsonResponse(dict(status='error', error='Param name not defined'))

        possible_tag = Label.objects.filter(name=name)

        if len(possible_tag) > 0:
            return JsonResponse(dict(status='error', error='Label exists'))

        new_label = Label.objects.create(name=name)

        if new_label:
            return JsonResponse(dict(status='created', data=dict(id=new_label.pk, name=new_label.name)))

        else:
            return JsonResponse(dict(status='error', error='not identified error'))

    else:
        raise Http404('Not found')


@csrf_exempt
def tags(request):
    tags = Label.objects.all()
    show_tags = []

    for tag in tags:
        new_tag = dict(id=tag.pk, name=tag.name)
        show_tags.append(new_tag)

    return JsonResponse(dict(status='founded', data=show_tags))

@csrf_exempt
def set_tag_to_post(request, id):
    if request.method == 'POST':

        try:
            post = Post.objects.get(id=id)
        except:
            post = None

        if not post:
            return JsonResponse(dict(status='error', error='Post with id not exists'))

        try:
            tag = request.POST['name']
        except:
            tag = None

        if not tag:
            return JsonResponse(dict(status='error', error='param tag not present'))

        try:
            tag = Label.objects.get(name=tag)
        except:
            tag = None

        if not tag:
            return JsonResponse(dict(status='error',
                                     error='tag with name {name} not exist'.format(name=request.POST['name'])))

        tags = post.label_set.filter(id=tag.pk)

        if len(tags) > 0:
            return JsonResponse(dict(status='error', error='posts has tag now'))

        tag.posts.add(post)
        return JsonResponse(dict(status='added', data=dict(id=tag.pk, name=tag.name)))
    else:
        raise Http404('Not found')

@csrf_exempt
def get_tags_for_post(request, id):

    if request.method == 'GET':
        try:
            post = Post.objects.get(id=id)
        except:
            post = None

        if not post:
            return JsonResponse(dict(status='error', error='Post with id not exists'))

        tags = post.label_set.all()
        show_tags = []

        for tag in tags:
            show_tags.append(dict(id=tag.pk, name=tag.name))

        return JsonResponse(dict(status='founded', data=show_tags))

    else:
        raise Http404('Not found')

@csrf_exempt
def remove_tag_for_post(request, id):

    if request.method != 'POST':
        raise Http404('Not found')

    try:
        post = Post.objects.get(id=id)
        print(post)
    except:
        post = None

    if not post:
        return JsonResponse(dict(status='error', error='Post with id not founded'))

    try:
        tag = request.POST['name']
    except:
        tag = None

    if not tag:
        return JsonResponse(dict(status='error', error='Param name not set'))

    try:
        tag = Label.objects.get(name=tag)
    except:
        tag = None

    if not tag:
        return JsonResponse(dict(status='error', error='Tag with name not exist'))

    try:
        search_tag = post.label_set.get(id=tag.pk)
        print(search_tag)
    except:
        search_tag = None

    if not search_tag:
        return JsonResponse(dict(status='error', error='Post has not tag with name'))

    result = post.label_set.remove(tag)
    print(result)
    return JsonResponse(dict(status='removed', data=dict(id=tag.pk, name=tag.name)))


class PostsListView(LoginRequiredMixin, TemplateView):

    template_name = 'posts/list.html'
    login_url = '/admin/login/'
    redirect_field_name = 'redirect_to'

    def get_context_data(self, *args, **kwargs):
        context = dict()
        context['domain'] = settings.DOMAIN_URL
        posts = Post.objects.all()
        for post in posts:
            post.clicks = post.interaction_set.filter(type='opened').count()
            session_total = 0
            users = set()
            sessions = post.interaction_set.filter(type='session')
            for session in sessions:
                users.add(session.user_id)
                session_total = session_total + int(session.value)
            post.session_total = session_total
            if sessions.count() > 0:
                post.session_average = round(session_total / sessions.count(), 2)
            else:
                post.session_average = 0
            feedback_total = 0
            feedback_list = post.feedback_set.all()
            for feedback in feedback_list:
                feedback_total = feedback_total + int(feedback.value)
            post.feedback_total = feedback_total
            if feedback_list.count() > 0:
                post.feedback_average = round(feedback_total / feedback_list.count(), 2)
                post.feedback_total_users = feedback_list.count()
            else:
                post.feedback_average = 0
                post.feedback_total_users = 0
            posts_sended = post.interaction_set.filter(type='sended')
            if posts_sended.count() > 0:
                users_to_sended = set()
                for interaction in posts_sended:
                    users_to_sended.add(interaction.user_id)
                post.total_sended_users = len(users_to_sended)
            else:
                post.total_sended_users = 0
            post.users = len(users)
            posts_used = post.interaction_set.filter(type='used')
            if posts_used.count() > 0:
                users_to_used = set()
                for interaction in posts_used:
                    users_to_used.add(interaction.user_id)
                post.total_used_users = len(users_to_used)
                print(len(users_to_used))
            else:
                post.total_used_users = 0
        context['posts'] = posts

        return context


def post_by_limits(request):
    if request.method == 'POST':
        return JsonResponse(dict(status='error', error='Invalid method.'))

    try:
        value = int(request.GET['value'])
        area_id = int(request.GET['area_id'])
        username = request.GET['username']
        user = User.objects.get(username=username)
    except Exception as e:
        return JsonResponse(dict(status='error', error='Invalid params.'))

    group = 'C'

    try:
        group_register = user.userdata_set.get(data_key='AB_group')
        group = group_register.data_value
    except Exception as e:
        print(str(e))
        pass

    print(group)

    if group == 'A':
        uri = 'https://metrics.afinidata.com/recommend?user_id=%s&months=%s&n=10&criterion=read_rate&' \
              'method=deterministic&upto=2019-04-15' % (user.pk, value)
    elif group == 'B':
        uri = 'https://metrics.afinidata.com/recommend?user_id=%s&months=%s&n=10&criterion=feedback' \
              '&method=deterministic&upto=2019-04-15' % (user.pk, value)
    else:
        uri = False

    if uri:
        print('user id: ', user.pk)
        print('group: ', group)
        today = datetime.now()
        days = timedelta(days=35)
        date_to_use = today - days
        r = requests.get(uri)
        response = r.json()
        service_post_list = [int(x) for x in response['recommendation']]
        print('service give posts with id')
        print(service_post_list)
        user_opened_post_list = [x.post_id for x in Interaction.objects.filter(type__in=['sended', 'opened'],
                                                                                user_id=user.pk,
                                                                                created_at__gt=date_to_use)]
        print('local excluded')
        print(user_opened_post_list)
        #user_opened_post_list = [131, 128, 88, 47]
        print('fake excluded (for dev only)')
        print(user_opened_post_list)
        recommendations = [x for x in service_post_list if x not in user_opened_post_list]
        print(recommendations)
        feedback_post_id = int(recommendations[0])
        print('id: ', feedback_post_id)
        #feedback_post_id = 1
        service_post = Post.objects.get(id=feedback_post_id)

    else:
        today = datetime.now()
        days = timedelta(days=35)
        date_to_use = today - days
        print(date_to_use)
        interactions = Interaction.objects.filter(user_id=user.pk, type='sended', created_at__gt=date_to_use)
        excluded = set()
        for interaction in interactions:
            if interaction.post_id:
                excluded.add(interaction.post_id)
        print(excluded)

        utc = pytz.UTC
        new_user_limit = utc.localize(datetime(2019, 3, 20, 0, 0, 0))
        print(new_user_limit)
        if user.created_at > new_user_limit:
            posts = Post.objects \
                .exclude(id__in=excluded) \
                .filter(min_range__lte=value, max_range__gte=value, area_id=area_id)
        else:
            posts = Post.objects \
                .exclude(id__in=excluded) \
                .filter(min_range__lte=value, max_range__gte=value, area_id=area_id, new=True)

        if posts.count() <= 0:
            return JsonResponse(dict(status='error', error='Not posts founded with value'))

        rand_limit = random.randrange(0, posts.count())
        service_post = posts[rand_limit]
    if service_post.content_activity:
        activity = service_post.content_activity.split('|')
        print(activity)
    return JsonResponse(dict(
        set_attributes=dict(
            post_id=service_post.pk,
            post_uri=settings.DOMAIN_URL + '/posts/' + str(service_post.pk),
            post_preview=service_post.preview,
            post_title=service_post.name
        ),
        messages=[]
    ))


def post_activity(request, id):
    if request.method == 'POST':
        return JsonResponse(dict(status='error', error='Invalid params.'))

    try:
        search_post = Post.objects.get(id=id)
        post_count = int(request.GET['post_count'])
    except Exception as e:
        return JsonResponse(dict(status='error', error=str(e)))

    if not search_post.content_activity:
        return JsonResponse(dict(status='error', error='Post has not activity'))

    activity_array = search_post.content_activity.split('|')
    print(len(activity_array))
    if post_count > len(activity_array) - 1:
        return JsonResponse(dict(status='error', error='Invalid params.'))
    if post_count < len(activity_array) - 1:
        post_has_finished = False
    else:
        post_has_finished = True
    return JsonResponse(dict(
        set_attributes=dict(
            activity_content=activity_array[post_count].strip(),
            post_count=post_count + 1,
            post_has_finished=post_has_finished
        ),
        messages=[]
    ))


class QuestionsView(LoginRequiredMixin, TemplateView):
    template_name = 'posts/questions.html'
    login_url = '/admin/login/'
    redirect_field_name = 'redirect_to'

    def get_context_data(self, **kwargs):
        questions = Question.objects.all()
        return dict(questions=questions)


class CreateQuestion(LoginRequiredMixin, CreateView):
    model = Question
    template_name = 'posts/new-question.html'
    fields = ('name', 'post', 'replies')
    login_url = '/admin/login/'
    redirect_field_name = 'redirect_to'

    def form_valid(self, form):
        new_question = form.save()
        return redirect('posts:review', id=new_question.post.pk)


class EditQuestion(LoginRequiredMixin, UpdateView):
    model = Question
    template_name = 'posts/question-edit.html'
    fields = ('name', 'post', 'replies')
    pk_url_kwarg = 'id'
    context_object_name = 'question'
    login_url = '/admin/login/'
    redirect_field_name = 'redirect_to'

    def form_valid(self, form):
        question = form.save()
        return redirect('posts:review', id=question.post.pk)


class QuestionView(LoginRequiredMixin, TemplateView):
    template_name = 'posts/question.html'
    login_url = '/admin/login/'
    redirect_field_name = 'redirect_to'

    def get_context_data(self, **kwargs):
        question = get_object_or_404(Question, pk=kwargs['id'])
        return dict(question=question)


class DeleteQuestionView(LoginRequiredMixin, DeleteView):
    template_name = 'posts/question-delete.html'
    model = Question
    login_url = '/admin/login/'
    redirect_field_name = 'redirect_to'
    pk_url_kwarg = 'id'
    context_object_name = 'question'
    success_url = reverse_lazy('posts:questions')


@csrf_exempt
def question_by_post(request, id):
    if request.method == 'POST':
        return JsonResponse(dict(status='error', error='Invalid method.'))

    questions = Question.objects.filter(post_id=id)

    if questions.count() <= 0:
        return JsonResponse(dict(status='error', error='No questions for this post'))

    random_limit = random.randrange(0, questions.count())
    question = questions[random_limit]
    print(question)
    return JsonResponse(dict(
        set_attributes=dict(
            question_id=question.pk,
            question_name=question.name
        ),
        messages=[]
    ))


@csrf_exempt
def set_interaction_to_post(request):
    if request.method == 'GET':
        return JsonResponse(dict(status='error', error='Invalid method.'))
    value = 0

    try:
        username = request.POST['username']
        user = User.objects.get(username=username)
    except Exception as e:
        return JsonResponse(dict(status='error', error='Invalid params.'))
    try:
        post_id = request.POST['post_id']
        post=Post.objects.get(id=post_id)
    except:
        post = None
    try:
        value = request.POST['value']
    except:
        pass

    interaction = Interaction.objects.create(
        type=request.POST['interaction_type'],
        channel_id=user.last_channel_id,
        username=user.username,
        user_id=user.pk,
        bot_id=request.POST['bot_id'],
        post=post,
        value=value
    )
    return JsonResponse(dict(status='done', data=dict(
        interaction=dict(
            id=interaction.pk
        )
    )))


@csrf_exempt
def get_thumbnail_by_post(request, id):
    if request.method == 'POST':
        return JsonResponse(dict(status='error', error='Invalid params'))

    try:
        post = Post.objects.get(pk=id)
        print(post)
        thumbnail = post.thumbnail
    except Exception as e:
        return JsonResponse(status='error', error='Invalid params')

    return JsonResponse(dict(
        set_attributes=dict(),
        messages=[
            dict(
                attachment=dict(
                    type='image',
                    payload=dict(
                        url=thumbnail
                    )
                )
            )
        ]
    ))


@csrf_exempt
def create_response_for_question(request, id):
    if request.method == 'GET':
        return JsonResponse(dict(status='error', error='Invalid method.'))

    try:
        username = request.POST['username']
        user = User.objects.get(username=username)
        question = Question.objects.get(id=id)
        user_response = request.POST['response']
    except Exception as e:
        return JsonResponse(dict(status='error', error='Invalid params.'))

    print(question)
    print(user)
    print(user_response)
    response = Response.objects.create(
        question=question,
        user_id=user.pk,
        username=username,
        response=user_response
    )

    return JsonResponse(dict(
        status='done',
        data=dict(
            response=dict(
                id=response.pk,
                user_id=response.user_id,
                username=response.username,
                response=response.response,
                question=response.question.name
            )
        )
    ))


@csrf_exempt
def get_replies_to_question(request, id):

    if request.method == 'POST':
        return JsonResponse(dict(status='error', error='Invalid method.'))

    try:
        question = Question.objects.get(pk=id)
    except:
        return JsonResponse(dict(status='error', error='Invalid params'))

    split_replies = question.replies.split(', ')
    quick_replies = []
    for reply in split_replies:
        new_reply = dict(title=reply, set_attributes=dict(response=reply), block_names=['Validador Feedback Ciclo 1-2'])
        quick_replies.append(new_reply)

    print(quick_replies)
    return JsonResponse(dict(
        messages=[
            {
                "text": question.name,
                "quick_replies": quick_replies
            }
        ]
    ))


class ReviewPostView(LoginRequiredMixin, DetailView):
    template_name = 'posts/review.html'
    login_url = '/admin/login/'
    redirect_field_name = 'redirect_to'
    model = Post
    pk_url_kwarg = 'id'