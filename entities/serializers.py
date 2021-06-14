from rest_framework import serializers
from entities.models import Entity
from attributes import serializers as attrSerializers


class EntitySerializer(serializers.ModelSerializer):
    
    attributes = attrSerializers.AttributeSerializer(many=True)
    
    class Meta:
        model = Entity
        fields = ['id', 'name', 'description', 'created_at', 'updated_at', 'attributes']
        # fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        depth = 1


class EntityNameSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Entity
        fields = ['name']