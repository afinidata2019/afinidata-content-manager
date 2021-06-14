from rest_framework import serializers
from attributes.models import Attribute


class AttributeSerializer(serializers.ModelSerializer):
    attribute_types = (
        ('numeric', 'Numeric'),
        ('string', 'String'),
        ('date', 'Date'),
        ('boolean', 'Boolean')
    )
    type = serializers.ChoiceField(attribute_types)

    class Meta:
        model = Attribute
        fields = ['id', 'name', 'type', 'attribute_view', 'created_at', 'updated_at']


class AttributeShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Attribute
        fields = ['id', 'name']