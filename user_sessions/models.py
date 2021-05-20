from django.contrib.auth.models import User
from attributes.models import Attribute
from licences.models import License
from programs.models import Program
from entities.models import Entity
from areas.models import Area
from messenger_users.models import User as MessengerUser
from instances.models import Instance
from django.db import models


class SessionType(models.Model):
    name = models.CharField(max_length=140)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Session(models.Model):
    name = models.CharField(max_length=100)
    min = models.IntegerField(null=True, default=0, verbose_name='Min meses')
    max = models.IntegerField(null=True, default=72, verbose_name='Max meses')
    session_type = models.ForeignKey(SessionType, on_delete=models.CASCADE, null=True)
    areas = models.ManyToManyField(Area)
    entities = models.ManyToManyField(Entity)
    licences = models.ManyToManyField(License)
    programs = models.ManyToManyField(Program)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Intent(models.Model):
    intent_id = models.IntegerField(default=0)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)

    def __str__(self):
        return "intent: {0}, session: {1}".format(self.intent_id, self.session.name)


class Channels(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    channel_id = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.pk


class BotSessions(models.Model):
    BOT_SESSION_TYPES = (('welcome', 'Welcome'), ('default', 'Default'), ('exchange', 'Exchange'))
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    bot_id = models.IntegerField(default=0)
    session_type = models.CharField(max_length=20, choices=BOT_SESSION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.pk


class Lang(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    language_id = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.pk


FIELD_TYPES = (('text', 'Text'),
               ('quick_replies', 'Quick Replies'),
               ('buttons', 'Buttons'),
               ('save_values_block', 'Redirect Chatfuel block'),
               ('user_input', 'Save user input'),
               ('image', 'Send image'),
               ('condition', 'Condition'),
               ('set_attributes', 'Set Attributes'),
               ('redirect_session', 'Redirect session'),
               ('live_chat', 'Send to Live Chat'),
               ('assign_sequence', 'Subscribe user to Sequence'),
               ('unsubscribe_sequence', 'Unsubscribe user to Sequence'),
               ('one_time_notification', 'One Time Notification'),
               ('activate_ai', 'Activate AI'),
               ('deactivate_ai', 'Deactivate AI'),
               ('consume_service', 'Consume service'))


class Field(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    position = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    field_type = models.CharField(max_length=50, choices=FIELD_TYPES)

    def __str__(self):
        return "%s" % self.pk


class Interaction(models.Model):
    """
    Tracking the user interaction with the sessions

    Args:
        session:
        user_id: ID del usuario del bot asociado a la interaction.
        username: Username del usuario del bot asociado a la interaction (Redundancia que se utiliza para ciertos reportes).
        channel_id: channel id del usuario del bot.
        bot_id: Bot al cual está conectado el usuario.
        type: String que guarda el tipo de interaction que ejecutó el usuario, estas pueden ser de cualquier tipo. De uso cotidiano en la plataforma en ciertas cosas se encuentran ‘session’ y ‘opened’, su uso puede ser muy variado.
        value: Valor de tipo Entero que puede almacenarse en las interacciones. (Formato de Entero posiblemente temporal, guardado así por alguna necesidad, por revisar)
        created_at, updated_at: (Uso general, fecha de creación, fecha de última actualización).
    """
    session = models.ForeignKey(Session, on_delete=models.CASCADE, null=True)
    field = models.ForeignKey(Field, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(MessengerUser, on_delete=models.CASCADE, null=True)
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE, null=True)
    bot_id = models.IntegerField(default=1)
    type = models.CharField(max_length=255, default='open')
    value = models.IntegerField(default=0, null=True)
    text = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.type+":"+self.value


class Message(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text


class UserInput(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    text = models.TextField()
    validation = models.CharField(max_length=50, null=True, choices=(('phone', 'Phone'), ('email', 'Email'),
                                                                     ('date', 'Date')))
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, null=True)
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text


class Reply(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    label = models.CharField(max_length=50)
    the_attribute = models.CharField(max_length=50, null=True, blank=True)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, null=True, blank=True)
    value = models.CharField(max_length=100, null=True, blank=True)
    redirect_block = models.CharField(max_length=100, null=True, blank=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, null=True, blank=True)
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.label


class Button(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    button_type = models.CharField(max_length=20, null=True, blank=True)
    url = models.CharField(max_length=100, null=True, blank=True)
    title = models.CharField(max_length=50, null=True, blank=True)
    block_names = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class SetAttribute(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.attribute.name + ':' + self.value


class Condition(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    condition = models.CharField(max_length=50, choices=(('equal', 'Equal'), ('not_equal', 'Not equal'),
                                                         ('in', 'Is in')))
    value = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.attribute.name + ' ' + self.condition + ' ' + self.value


class Response(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE)
    instance_id = models.IntegerField(default=0)
    user_id = models.IntegerField(default=0)
    response = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.pk)


class RedirectBlock(models.Model):
    field = models.OneToOneField(Field, on_delete=models.CASCADE)
    block = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.block


class RedirectSession(models.Model):
    field = models.OneToOneField(Field, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.session.name


class AssignSequence(models.Model):
    field = models.OneToOneField(Field, on_delete=models.CASCADE)
    sequence_id = models.IntegerField(default=0)
    start_position = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.sequence_id


class UnsubscribeSequence(models.Model):
    field = models.OneToOneField(Field, on_delete=models.CASCADE)
    sequence_id = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.sequence_id


class AvailableService(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    url = models.CharField(max_length=200)
    request_type = models.CharField(max_length=5, choices=(('post', 'POST'), ('get', 'GET')), default='post')
    suggested_params = models.CharField(max_length=500)  # Comma separated service params
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.url


class Service(models.Model):
    field = models.OneToOneField(Field, on_delete=models.CASCADE)
    available_service = models.ForeignKey(AvailableService, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.url


class ServiceParam(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    parameter = models.CharField(max_length=30)
    value = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.parameter + '=' + self.value


class FieldProgramExclusion(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class FieldProgramComment(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
