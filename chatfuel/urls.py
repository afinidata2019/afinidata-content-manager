from django.urls import path
from chatfuel import views

app_name = 'chatfuel'

urlpatterns = [
    # MESSENGER USERS VIEWS
    path('create_messenger_user_data/', views.CreateMessengerUserDataView.as_view(), name='create_messenger_user_data'),
    path('verify_user/', views.VerifyMessengerUserView.as_view(), name='verify_user'),
    path('replace_user_info/', views.ReplaceUserInfoView.as_view(), name='replace_user_info'),
    path('change_bot/', views.ChangeBotUserView.as_view(), name='change_bot'),
    path('change_botchannel/', views.ChangeBotChannelUserView.as_view(), name='change_botchannel'),
    path('stop_bot/', views.StopBotUserView.as_view(), name='stop_bot'),
    path('create_messenger_user/', views.CreateMessengerUserView.as_view(), name='create_messenger_user'),
    path('get_initial_user_data/', views.GetInitialUserData.as_view(), name='get_initial_user_data'),
    path('get_user_previous_field/', views.GetUserPreviousField.as_view(), name='get_user_previous_field'),
    path('recover_user/', views.RecoverUser.as_view(), name='recover_user'),
    
    # INSTANCES VIEWS
    path('get_instances/', views.GetInstancesByUserView.as_view(), name='get_instances'),
    path('guess_instance/', views.GuessInstanceByUserView.as_view(), name='guess_instance'),
    path('create_instance/', views.create_instance, name='new_instance'),
    path('get_instance_attribute/', views.GetInstanceAttributeView.as_view(), name='get_instance_attribute'),
    path('change_instance_name/', views.ChangeInstanceNameView.as_view(), name='change_instance_name'),

    # CODE VIEWS
    path('verify_code/', views.VerifyCodeView.as_view(), name='verify_code'),
    path('exchange_code/', views.ExchangeCodeView.as_view(), name='exchange_code'),
    path('create_instance_attribute/', views.CreateInstanceAttributeView.as_view(), name='create_instance_attribute'),
    
    # INTERACTION VIEWS
    path('create_instance_interaction_view/', views.CreateInstanceInteractionView.as_view(),
         name='create_instance_interaction_view'),
    
    # CHILDREN
    path('get_favorite_child/', views.GetFavoriteChildView.as_view(), name='get_favorite_child'),
    path('get_last_child/', views.GetLastChildView.as_view(), name='get_last_child'),
    
    # ARTICLES
    path('get_article/', views.GetRecomendedArticleView.as_view(), name='get_article'),
    path('get_article_text/', views.GetArticleTextView.as_view(), name='get_article_text'),
    path('get_article_image/', views.GetArticleImageView.as_view(), name='get_article_image'),
    path('article_feedback/', views.AddFeedbackToArticleView.as_view(), name='article_feedback'),

    # MILESTONES UTILITIES
    path('get_milestone/', views.GetMilestoneView.as_view(), name='get_milestone'),
    path('get_program_milestone/', views.GetProgramMilestoneView.as_view(), name='get_program_milestone'),
    path('get_program_risks/', views.GetProgramRisksMilestoneView.as_view(), name='get_program_risks'),
    path('get_instance_milestones/', views.GetInstanceMilestoneView.as_view(), name='get_instance_milestones'),
    path('response_milestone/', views.CreateResponseView.as_view(), name='response_milestone'),

    # SESSIONS UTILITIES
    path('get_session/', views.GetSessionView.as_view(), name='get_session'),
    path('send_session/', views.SendSessionView.as_view(), name='send_session'),
    path('get_session_field/', views.GetSessionFieldView.as_view(), name='get_session_field'),
    path('save_last_reply/', views.SaveLastReplyView.as_view(), name='save_last_reply'),

    # REMINDERS DATETIME
    path('save_reminder_datetime/', views.SaveReminderDateTimeView.as_view(), name='save_reminder_datetime'),
    
    # CHATFUEL UTILITIES
    path('redirect_to_block/', views.BlockRedirectView.as_view(), name='redirect_to_block'),
    path('validates_date/', views.ValidatesDateView.as_view(), name='validates_date'),
    path('calculate_pregnant_weeks/', views.CalculateWeeksView.as_view(), name='pregnant_weeks'),
    path('default_date_values/', views.DefaultDateValuesView.as_view(), name='default_date_values'),
    path('set_default_date/', views.SetDefaultDateValueView.as_view(), name='set_default_date'),
    
]