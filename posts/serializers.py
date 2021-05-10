from rest_framework import serializers
from posts.models import PostComplexity, Intent


class PostComplexitySerializer(serializers.ModelSerializer):

    class Meta:
        model = PostComplexity
        fields = ('post', 'user_id', 'months', 'complexity')


class IntentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Intent
        fields = ['id', 'intent_id', 'post']
