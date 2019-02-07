from django.views.generic import TemplateView
from posts.models import Post, Interaction, Feedback, Label
from django.shortcuts import get_object_or_404, render, redirect
from posts.forms import CreatePostFormModel, CreatePostForm
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core import serializers
from messenger_users.models import User
from datetime import datetime


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
                                           user_id=user.pk)
                post_session.save()
                return render(request, 'posts/post.html',
                              {'post': post, 'session_id': post_session.pk})
            except:

                return render(request, 'posts/post.html', {'post': post, 'session_id': 'null'})
        
        return render(request, 'posts/post.html', {'post': post, 'session_id': 'null'})


class StatisticsView(TemplateView):
    template_name = 'posts/statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        view_post = Post.objects.get(id=kwargs['id'])
        clicks = view_post.interaction_set.filter(type='opened')
        sessions = view_post.interaction_set.filter(type='session')
        context['post'] = view_post
        context['clicks'] = clicks
        context['sessions'] = sessions
        context['domain'] = settings.DOMAIN_URL
        return context


def new_post(request):

    form = CreatePostForm(request.POST or None)

    if form.is_valid():

        data = form.cleaned_data

        saved_post = Post.objects.create(**data)

        return redirect('posts:post', id=saved_post.pk)

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
            interaction = Interaction.objects.filter(pk=id).update(minutes=request.POST['minutes'])
            return JsonResponse(dict(
                status='updated',
                interaction=interaction
            ))
        except:
            raise Http404('Error')

    else:
        return JsonResponse(dict(hello="world"))


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
        try:
            post_to_edit = Post.objects.get(id=request.POST['id'])
            post_to_edit.name = request.POST['name'] if request.POST['name'] else None
            post_to_edit.content = request.POST['content'] if request.POST['content'] else None
            post_to_edit.type = request.POST['type'] if request.POST['type'] else None
            post_to_edit.author = request.POST['author'] if request.POST['author'] else None
            post_to_edit.save()

        except:
            print('not found')
            pass
        return redirect('posts:edit-post', id=id)


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