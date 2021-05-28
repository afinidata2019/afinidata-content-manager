from .models import AttributeValue, Instance
from messenger_users.models import User, UserData
from rest_framework import serializers
from attributes.serializers import AttributeSerializer
# from messenger_users.serializers import UserShortSerializer


class InstanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Instance
        fields = '__all__'


class AttributeValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeValue
        fields = '__all__'


class AttributeValueListSerializer(serializers.ModelSerializer):
    attribute = AttributeSerializer(read_only=True, many=False)

    class Meta:
        model = AttributeValue
        fields = ('id', 'value', 'attribute', 'instance')


class AttributeValueFilterPosibleVal(serializers.ModelSerializer):

    class Meta:
        model = AttributeValue
        fields = ('value', )


class InstanceShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instance
        fields = ('id','name')
