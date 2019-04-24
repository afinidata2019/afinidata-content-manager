from django.urls import path
from posts import views

app_name = 'posts'

urlpatterns = [
    path('', views.HomeView.as_view(), name="home"),
    path('new/', views.NewPostView.as_view(), name='new'),
    path('<int:id>/edit/', views.EditPostView.as_view(), name="edit-post"),
    path('<int:id>/', views.post, name="post"),
    path('<int:id>/delete/', views.DeletePostView.as_view(), name='delete'),
    path('<int:id>/send_to_review/', views.ChangePostStatusToReviewView.as_view(), name='new-review'),
    path('set_interaction/', views.set_interaction_to_post, name='set_interaction'),
    path('<int:id>/thumbnail/', views.get_thumbnail_by_post, name='get_thumbnail'),
    path('<int:id>/review/', views.ReviewPostView.as_view(), name='review'),
    path('interaction/<int:id>/edit/', views.edit_interaction, name="interaction-edit"),
    path('feedback/', views.feedback, name="feedback"),
    path('<int:id>/statistics/', views.StatisticsView.as_view(), name='post-statistics'),
    path('<int:id>/activity/', views.post_activity, name='post-activity'),
    path('tags/create', views.create_tag, name="create-tag"),
    path('tags/', views.tags, name='tags'),
    path('<int:id>/set_tag', views.set_tag_to_post, name="set-tag-to-post"),
    path('<int:id>/get_tags', views.get_tags_for_post, name="get-tags-for-post"),
    path('<int:id>/remove_tag', views.remove_tag_for_post, name='remove-tag-for-post'),
    path('list/', views.PostsListView.as_view(), name="posts-list"),
    path('set_user_send/', views.set_user_send, name='set-user-send'),
    path('by_limit/', views.post_by_limits, name='posts_by_limit'),
    path('questions/<int:id>/', views.QuestionView.as_view(), name='question'),
    path('questions/', views.QuestionsView.as_view(), name='questions'),
    path('questions/new/', views.CreateQuestion.as_view(), name='new-question'),
    path('questions/<int:id>/edit/', views.EditQuestion.as_view(), name='edit-question'),
    path('questions/<int:id>/delete/', views.DeleteQuestionView.as_view(), name='delete-question'),
    path('<int:id>/questions/', views.question_by_post, name='question_by_post'),
    path('questions/<int:id>/response/', views.create_response_for_question, name='response_for_cuestion'),
    path('questions/<int:id>/replies/', views.get_replies_to_question, name='replies_for_question')
]
