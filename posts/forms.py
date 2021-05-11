import os
import json
import requests
from django import forms
from messenger_users.models import User
from instances.models import Instance
from areas.models import Area
from posts import models



class CreatePostForm(forms.Form):

    TYPE_CHOICES = (('embeded', 'Embeded'), ('youtube', 'Youtube'))

    name = forms.CharField(label='Name')
    thumbnail = forms.CharField(label='Thumbnail')
    new = forms.BooleanField(label='New?', required=False)
    type = forms.ChoiceField(widget=forms.Select, choices=TYPE_CHOICES)
    min_range = forms.IntegerField()
    max_range = forms.IntegerField()
    area = forms.ModelChoiceField(queryset=Area.objects.all())
    content = forms.CharField(label='Content')
    content_activity = forms.CharField(label='Activity for FB. (Divide sections with | )', widget=forms.Textarea)
    preview = forms.CharField(widget=forms.Textarea)


class UpdatePostFormModel(forms.ModelForm):

    class Meta:
        model = models.Post
        fields = ['name', 'content', 'type', 'min_range', 'max_range', 'area', 'preview']


class UpdateTaxonomy(forms.ModelForm):
    class Meta:
        model = models.Taxonomy
        fields = ['post', 'area', 'subarea', 'component']


class QuestionForm(forms.ModelForm):

    class Meta:
        model = models.Question
        fields = ('name', 'post', 'replies')


class IntentForm(forms.Form):
    OPTIONS = []
    service_response = requests.get(os.getenv('NLU_API') + '/intents/?options=True').json()
    if 'count' in service_response and service_response['count'] > 0:
        OPTIONS = [ (intent['id'], intent['name']) for intent in service_response['results'] ]
    
    intents = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=OPTIONS)
    post =  forms.ModelChoiceField(widget = forms.HiddenInput(), queryset=models.Post.objects.all())
    


class ReviewCommentForm(forms.ModelForm):

    class Meta:
        model = models.ReviewComment
        fields = ('comment',)


class QuestionResponseForm(forms.ModelForm):

    class Meta:
        model = models.QuestionResponse
        fields = ('response', 'value')


class GetPostForm(forms.Form):
    user_id = forms.ModelChoiceField(queryset=User.objects.all())
    instance = forms.ModelChoiceField(queryset=Instance.objects.all())
    locale = forms.CharField(required=False)
