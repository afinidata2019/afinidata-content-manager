from .models import UserChannel, UserData, User, Child, ChildData
from rest_framework import serializers
from django.utils import timezone
import requests
import os

from instances.serializers import InstanceShortSerializer
from instances.models import Instance

class UserSerializer(serializers.ModelSerializer):
    profile_pic = serializers.ReadOnlyField()
    last_message = serializers.ReadOnlyField()
    last_bot_id = serializers.ReadOnlyField()
    bot_channel_id = serializers.ReadOnlyField()
    user_channel_id = serializers.ReadOnlyField()
    last_seen = serializers.ReadOnlyField()
    last_channel_interaction = serializers.ReadOnlyField()
    window = serializers.ReadOnlyField()

    # get id, name from instances associates to user
    instances = serializers.SerializerMethodField()

    def get_instances(self, obj):
        qs = Instance.objects.filter(instanceassociationuser__user_id=obj.pk)
        serializer = InstanceShortSerializer(qs, many=True)
        return serializer.data

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'last_seen', 'backup_key', 'license', 'language',
                  'last_channel_interaction', 'window', 'channel_id', 'user_channel_id', 'bot_channel_id', 'bot_id', 'profile_pic',
                  'last_message', 'last_bot_id', 'created_at', 'updated_at', 'entity','instances']


class UserConversationSerializer(serializers.ModelSerializer):
    profile_pic = serializers.ReadOnlyField()
    last_message = serializers.ReadOnlyField()
    last_bot_id = serializers.ReadOnlyField()
    bot_channel_id = serializers.ReadOnlyField()
    user_channel_id = serializers.ReadOnlyField()
    last_seen = serializers.ReadOnlyField()
    last_user_message = serializers.ReadOnlyField()
    last_channel_interaction = serializers.ReadOnlyField()
    window = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'last_seen', 'last_user_message',
                  'last_channel_interaction', 'window', 'user_channel_id', 'bot_channel_id', 'bot_id', 'profile_pic',
                  'last_message', 'last_bot_id']


class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserData
        exclude = ['created']


class ChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Child
        exclude = ['created']


class ChildDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChildData
        exclude = ['timestamp']


class UserChannelSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserChannel
        fields = '__all__'


class DetailedUserChannelSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True, many=False)

    class Meta:
        model = UserChannel
        fields = '__all__'


class UserDataFilterPosibleVal(serializers.ModelSerializer):

    value = serializers.CharField(source='data_value')

    class Meta:
        model = UserData
        fields = ('value', )
