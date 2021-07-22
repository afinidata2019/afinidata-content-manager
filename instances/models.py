from django.core.validators import MinValueValidator, MaxValueValidator
from messenger_users import models as user_models
from posts.models import Post, Interaction
from dateutil import parser, relativedelta
from attributes.models import Attribute
from programs.models import Program
from entities.models import Entity
from django.utils import timezone
from areas.models import Area
import datetime
from django.db import models
from django.db.models.aggregates import Max


class Instance(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    name = models.TextField()
    attributes = models.ManyToManyField(Attribute, through='AttributeValue')
    program = models.ForeignKey(
        Program, on_delete=models.DO_NOTHING, null=True)
    sessions = models.ManyToManyField(Session)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = (
            ('view_all_instances', 'User can view all instances'),
        )

    def __str__(self):
        return self.name

    def get_users(self):
        return user_models.User.objects \
            .filter(id__in=set(assoc.user_id for assoc in self.instanceassociationuser_set.all()))

    def get_months(self):
        if self.entity_id == 1:
            births = self.attributevalue_set.filter(attribute__name='birthday')
            if not births.exists():
                return None
            birth = births.last()
            print(self)
            print(birth)
            try:
                birthday = parser.parse(birth.value)
                if timezone.is_aware(birthday):
                    now = timezone.now()
                else:
                    now = datetime.datetime.now()
                rd = relativedelta.relativedelta(now, birthday)
                if rd.months:
                    months = rd.months
                else:
                    months = 0
                if rd.years:
                    months = months + (rd.years * 12)
                return months
            except:
                return None
        elif self.entity_id == 2:
            pregnant_weeks = self.attributevalue_set.filter(
                attribute__name='pregnant_weeks')
            if not pregnant_weeks.exists():
                return None
            pw = pregnant_weeks.last()
            months = round(int(pw.value) / 4)
            if months == 0:
                months = -1
            return months
        else:
            return None

    def get_weeks(self):
        if self.entity_id == 2:
            pregnant_weeks = self.attributevalue_set.filter(
                attribute__name='pregnant_weeks')
            if not pregnant_weeks.exists():
                return None
            pw = pregnant_weeks.last()
            weeks = int(pw.value)
            if weeks == 0:
                weeks = -1
            return weeks
        else:
            return None

    def get_time_feeds(self, first_limit, last_limit):
        feeds = self.instancefeedback_set.filter(
            created_at__gte=first_limit, created_at__lte=last_limit)
        return feeds

    def get_time_interactions(self, first_limit, last_limit):
        interactions = Interaction.objects.filter(created_at__gte=first_limit, created_at__lte=last_limit,
                                                  instance_id=self.pk)
        return interactions


    def get_activities(self):
        posts = Post.objects.filter(id__in=set([x.post_id for x in Interaction.objects.filter(instance_id=self.pk)]))\
            .only('id', 'name')
        for post in posts:
            post.assign = Interaction.objects.filter(
                post_id=post.id, type='dispatched', instance_id=self.pk).last()
            sessions = Interaction.objects.filter(
                post_id=post.id, type='session', instance_id=self.pk)
            if sessions.count() > 0:
                post.completed = sessions.last()
            else:
                post.completed = None
        return posts

    def get_activities_area(self, area, first_limit, last_limit):
        if area > 0:
            posts = Post.objects.\
                filter(id__in=set([x.post_id for x in Interaction.objects.filter(instance_id=self.pk)
                                   .filter(created_at__gte=first_limit, created_at__lte=last_limit, type='session')])) \
                .filter(area_id=area).only('id', 'name')
        else:
            posts = Post.objects. \
                filter(id__in=set([x.post_id for x in Interaction.objects.filter(instance_id=self.pk)
                                   .filter(created_at__gte=first_limit, created_at__lte=last_limit, type='session')])) \
                .only('id', 'name')
        return posts

    def get_completed_activities(self, tipo='session'):
        posts = Post.objects\
            .filter(id__in=set([x.post_id for x in Interaction.objects.filter(instance_id=self.pk, type=tipo)]))\
            .only('id')
        return posts

    def get_attributes(self):
        attributes_ids = set(item.pk for item in self.attributes.all())
        attributes = Attribute.objects.filter(id__in=attributes_ids)
        for attribute in attributes:
            attribute.assign = self.attributevalue_set.filter(
                attribute=attribute).last()
        return attributes

    def get_attribute_values(self, name):
        attribute = self.attributevalue_set.filter(attribute__name=name)
        if not attribute.count() > 0:
            return None
        return attribute.last()

    def is_session_active(self):
        sessions = self.sessions.filter(
            created_at__gte=timezone.now() - datetime.timedelta(days=7))
        return sessions.exists()

# Child Association with parent


class InstanceAssociationUser(models.Model):
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)
    user = models.ForeignKey('messenger_users.User',
                             on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Score(models.Model):
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    value = models.FloatField(default=0, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.instance.name + '__' + self.area.name + '__' + str(round(self.value, 2))


class ScoreTracking(models.Model):
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    value = models.FloatField(default=0, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.instance.name + '__' + self.area.name + '__' + str(round(self.value, 2))


class Response(models.Model):
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE)
    response = models.CharField(max_length=255)
    session = models.ForeignKey(
        Session, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s__%s__%s%s__%s" % (self.pk, self.instance.name, self.milestone.pk, self.milestone.name, self.response)


class AttributeValue(models.Model):
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s__%s__%s__%s" % (self.pk, self.instance.name, self.attribute.name, self.value)


class PostInteraction(models.Model):
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)
    post_id = models.IntegerField()
    type = models.CharField(max_length=255, default='open')
    value = models.IntegerField(default=0)
    created_at = models.DateTimeField()

    def __str__(self):
        return "%s %s %s %s" % (self.pk, self.instance, self.post_id, self.type)


REGISTER_TYPE_CHOICES = (
    (0, "Script with number"),
    (1, "Script with text")
)


class InstanceFeedback(models.Model):
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)
    post_id = models.IntegerField()
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    value = models.IntegerField(default=1, validators=[
                                MinValueValidator(0), MaxValueValidator(5)])
    reference_text = models.CharField(max_length=50)
    register_id = models.IntegerField(null=True)
    register_type = models.CharField(max_length=20, default=0)
    migration_field_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField()

    def __str__(self):
        return "%s %s %s %s" % (self.pk, self.instance_id, self.area, self.value)


class MilestoneInteraction(models.Model):
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)
    milestone_id = models.IntegerField()
    type = models.CharField(max_length=255, default='hitos_monitoreo')
    value = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s %s %s %s" % (self.pk, self.instance, self.milestone_id, self.type)
