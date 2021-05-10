from rest_framework import serializers
from articles.models import Intent


class IntentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Intent
        fields = ['id', 'intent_id', 'article']
