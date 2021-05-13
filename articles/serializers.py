import os
from rest_framework import serializers
from articles.models import Intent, Article


class ArticleSimpleSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    
    def get_url(self, obj):
        service_url = '{0}/articles/{1}/info/'.format(os.getenv('CM_DOMAIN_URL'), obj.id)
        return service_url

    class Meta:
        model = Article
        fields = ['id', 'name', 'status', 'content', 'url']


class IntentArticleSerializer(serializers.ModelSerializer):
    article = ArticleSimpleSerializer()

    class Meta:
        model = Intent
        fields = ['id', 'intent_id', 'article']


class IntentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Intent
        fields = ['id', 'intent_id', 'article']
        
