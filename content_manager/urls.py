"""content_manager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from articles import api_views as articles_api_views
from attributes import api_views as attributes_api_views
from bots import api_views as bots_api_views
from entities import api_views as entities_api_views
from groups import api_views as groups_api_views
from instances import api_views as instances_api_views
from messenger_users import api_views as messenger_users_api_views
from posts import api_views as posts_api_views
from programs import api_views as programs_api_views
from user_sessions import api_views as sessions_api_views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


# api v0.1 router
router = routers.DefaultRouter()
router.register(r'articles', articles_api_views.ArticleViewSet)
router.register(r'article_intent', articles_api_views.ArticleIntentViewSet)
router.register(r'attributes', attributes_api_views.AttributeViewSet)
router.register(r'bot_sessions', sessions_api_views.BotSessionViewSet)
router.register(r'entities', entities_api_views.EntityViewSet)
router.register(r'groups', groups_api_views.GroupViewset)
router.register(r'instances', instances_api_views.InstanceViewSet)
router.register(r'instances_attributevalue', instances_api_views.InstancesAttributeViewSet)
router.register(r'interactions', bots_api_views.InteractionViewSet)
router.register(r'messenger_users', messenger_users_api_views.UserViewSet)
router.register(r'messenger_users_channels', messenger_users_api_views.UserChannelSet)
router.register(r'messenger_users_data', messenger_users_api_views.UserDataViewSet)
router.register(r'posts', posts_api_views.PostViewSet)
router.register(r'post_intent', posts_api_views.PostIntentViewSet)
router.register(r'programs', programs_api_views.ProgramViewSet)
router.register(r'programs_attributes', programs_api_views.AttributesViewSet)
router.register(r'programs_attribute_types', programs_api_views.AttributeTypeViewSet)
router.register(r'sessions', sessions_api_views.SessionViewSet)
router.register(r'sessions_replies', sessions_api_views.SessionsRepliesViewSet)
router.register(r'sessions_interactions', sessions_api_views.InteractionViewSet)
router.register(r'user_interactions', bots_api_views.UserInteractionViewSet)
router.register(r'user', messenger_users_api_views.UserViewSet)


urlpatterns = [
    path('', include("static.urls", namespace="static")),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('posts/', include("posts.urls", namespace="posts")),
    path('upload/', include('upload.urls', namespace='upload')),
    path('instances/', include('instances.urls', namespace='instances')),
    path('messenger_users/', include("messenger_users.urls", namespace="users")),
    path('utilities/', include("utilities.urls", namespace="utilities")),
    path('dashboard/', include("dash.urls", namespace="dash")),
    path('codes/', include("random_codes.urls", namespace="codes")),
    path('reply/', include("reply_repo.urls", namespace="replies")),
    path('support/', include("support.urls", namespace="support")),
    path('articles/', include('articles.urls', namespace='articles')),
    path('areas/', include('areas.urls', namespace='areas')),
    path('user_sessions/', include('user_sessions.urls', namespace='user_sessions')),
    path('chatfuel/', include('chatfuel.urls', namespace='chatfuel')),
    path('milestones/', include('milestones.urls', namespace='milestones')),
    path('api/0.1/', include(router.urls)),
    
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
