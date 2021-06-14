from rest_framework import serializers
from attributes.serializers import AttributeShortSerializer
from messenger_users.serializers import UserReplySerializer
from user_sessions.models import BotSessions, Interaction, Message, Session, Reply


class SessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Session
        fields = ['id', 'name']


class BotSessionsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = BotSessions
        fields = ['id', 'session_id', 'bot_id', 'session_type']


class FieldSessionSerializer(serializers.ModelSerializer):
    session = SessionSerializer(read_only=True)
    class Meta:
        model = Reply
        fields = ['session'] 
        

class ReplySerializer(serializers.ModelSerializer):

    class Meta:
        model = Reply
        fields = '__all__'  


class ReplyLabelSerializer(serializers.ModelSerializer):
    field = FieldSessionSerializer(read_only=True)
    
    class Meta:
        model = Reply
        fields = ['id', 'label', 'field']  


class InteractionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Interaction
        fields = '__all__'


class ReplyInteractionSerializer(serializers.ModelSerializer):
    attribute = AttributeShortSerializer(read_only=True)

    class Meta:
        model = Reply
        fields = ['id', 'label', 'value', 'attribute'] 


class InteractionReplyCorrectionSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    question = serializers.SerializerMethodField()
    session_name = serializers.SerializerMethodField()

    def get_replies(self, obj):
        qs = Reply.objects.filter(field=obj.field)
        serializer = ReplyInteractionSerializer(qs, many=True)
        return serializer.data

    def get_question(self, obj):
        qs = Message.objects.filter(field__session_id=obj.session_id, field__position=obj.field.position-1)
        if qs.exists():
            return qs.first().text
        return ''
    
    def get_session_name(self, obj):
        return '{0} ({1}) in position {2}'.format(obj.session.name, obj.session.id, obj.field.position)
    
    class Meta:
        model = Interaction
        fields = ['id', 'question', 'text', 'session', 'session_name', 'replies']


class InteractionReplySerializer(serializers.ModelSerializer):
    user = UserReplySerializer(read_only=True)
    question = serializers.SerializerMethodField()

    def get_question(self, obj):
        qs = Message.objects.filter(field__session_id=obj.session_id, field__position=obj.field.position-1)
        if qs.exists():
            return qs.first().text
        return ''
    
    class Meta:
        model = Interaction
        fields = ['id', 'question', 'text', 'user']


