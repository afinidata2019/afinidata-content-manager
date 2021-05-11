import os
import json
import requests
from articles import models
from django import forms


class AdminArticleForm(forms.ModelForm):

    class Meta:
        model = models.Article
        fields = ('name', 'status', 'type', 'content', 'text_content', 'topics', 'min', 'max', 'preview', 'thumbnail',
                  'campaign', 'programs')


class IntentForm(forms.Form):
    OPTIONS = []
    service_response = requests.get(os.getenv('NLU_API') + '/intents/?options=True').json()
    if 'count' in service_response and service_response['count'] > 0:
        OPTIONS = [ (intent['id'], intent['name']) for intent in service_response['results'] ]
    
    intents = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=OPTIONS)
    article =  forms.ModelChoiceField(widget = forms.HiddenInput(), queryset=models.Article.objects.all())
