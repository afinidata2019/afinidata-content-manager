import os
import json
import requests
from django import forms
from django.core.handlers.wsgi import WSGIRequest


class CreateLogForm(forms.Form):
    request_id = forms.CharField(required=False)
    section = forms.CharField()
    payload = forms.CharField(widget=forms.Textarea)
    bot_channel_id = forms.CharField(required=False)
    user_id = forms.IntegerField(required=False)
    user_channel_id = forms.CharField(required=False)
    project_log_id = forms.CharField(required=False)


class GeneralLog:
    all_valid_keys = ['request_id', 'project', 'section', 'payload', 'bot_channel_id', 'user_id', 'user_channel_id', 'status_code', 'message', 'project_log_id']
    create_valid_keys = ['request_id', 'project', 'section', 'payload', 'bot_channel_id', 'user_id', 'user_channel_id']
    update_valid_keys = ['section', 'status_code', 'message', 'project_log_id']

    def __str__(self):
        return str(self.get_request_id())

    def __init__(self, initial=dict()):
        super().__init__()
        
        if isinstance(initial, requests.models.Response) or isinstance(initial, WSGIRequest):
            initial = initial.POST if len(initial.POST) > 0 else json.loads(initial.body)
        
        form = CreateLogForm(initial)
        form.is_valid()

        log_params = dict( project='content_manager' )
        for key, val in form.cleaned_data.items():
            if val:
                log_params[key] = val

        if 'request_id' not in log_params and 'log' in initial and initial['log']:
            log_params['request_id'] = str(initial['log'])
        
        self.log_params = log_params
        self.url = '{0}/general_log/'.format(os.getenv('LOG_API'))
        self.last_id = False


    def get_request_id(self):
        return self.log_params['request_id'] if ('request_id' in self.log_params and self.log_params['request_id']) else False


    def clean_dict(self, valid_keys, dicts):
        cleaned = dict()
        for current_dict in dicts:
            for key, val in current_dict.items():
                if key in valid_keys:
                    cleaned[key] = val
        return cleaned


    def add(self, data):
        try:
            # all new requests must be associatd to a main request
            if 'request_id' not in self.log_params or not self.log_params['request_id']:
                print('Error: all new requests must be associatd to a main request')
                return False

            create_data = self.clean_dict(valid_keys=self.all_valid_keys, dicts=[data, self.log_params])
            if not create_data:
                return False

            response = requests.post(self.url, json=create_data).json()
            if not response or ('request_status' in response and response['request_status'] != 200):
                print('Error:')
                print(response)
                return False

            return True

        except Exception as e:
            print('Log_add error: {0}'.format(e))            
            return False


    def add_main(self, data):
        try:
            form = CreateLogForm(data)
            if not form.is_valid():
                print('Error: wrong params {0}'.format(form.errors.as_json())) 
                return False
            
            create_data = self.clean_dict(valid_keys=self.create_valid_keys, dicts=[form.cleaned_data, self.log_params])
            if not create_data:
                print('Error: No data sent') 
                return False

            response = requests.post(self.url, json=create_data).json()
            if not response or ('request_status' in response and response['request_status'] != 200):
                print('Error:')
                print(response)
                return False

            if 'request_id' not in self.log_params or not self.log_params['request_id']:
                self.log_params['request_id'] = response['log']['request_id']
            
            self.last_id = response['log']['id']
            return True

        except Exception as e:
            print('Log_add_main error: {0}'.format(e))
            return False


    def update_main(self, data):
        try:
            update_data = self.clean_dict(valid_keys=self.update_valid_keys, dicts=[data])
            if not update_data or not self.last_id:
                print('Error: wrong params, last_id:{}'.format(self.last_id)) 
                return False
            
            response = requests.patch('{0}{1}/'.format(self.url, self.last_id), json=update_data).json()
            if not response or ('request_status' in response and response['request_status'] != 200):
                print('Error:')
                print(response)
                return False
            return True

        except Exception as e:
            print('Log_update error: {0}'.format(e))
            return False

