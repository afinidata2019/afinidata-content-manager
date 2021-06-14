import json
import os
import requests
from django import forms

from messenger_users.models import User
from user_sessions import models


class InteractionCorrectForm(forms.Form):
    interaction = forms.ModelChoiceField(queryset=models.Interaction.objects.all())
    reply = forms.ModelChoiceField(queryset=models.Reply.objects.all(), required=False)
    intent = forms.IntegerField(required=False)
    ignore = forms.BooleanField(required=False)