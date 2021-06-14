import os
from rest_framework import serializers
from posts.models import PostComplexity, Intent, Post


class PostComplexitySerializer(serializers.ModelSerializer):

    class Meta:
        model = PostComplexity
        fields = ('post', 'user_id', 'months', 'complexity')


class PostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        fields = '__all__'


class PostOptionsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        fields = ['id', 'name']


class PostSimpleSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    
    def get_url(self, obj):
        service_url = '{0}/posts/{1}/statistics/'.format(os.getenv('CM_DOMAIN_URL'), obj.id)
        return service_url

    class Meta:
        model = Post
        fields = ['id', 'name', 'status', 'content', 'url']


class IntentPostSerializer(serializers.ModelSerializer):
    post = PostSimpleSerializer()

    class Meta:
        model = Intent
        fields = ['id', 'intent_id', 'post']


class IntentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Intent
        fields = ['id', 'intent_id', 'post']
