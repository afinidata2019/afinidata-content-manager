from attributes.models import Attribute 
from user_sessions.models import Reply


def transfer_attributes():
    replies = Reply.objects.exclude(attribute__isnull=False).exclude(the_attribute__isnull=True).exclude(the_attribute='')
    for reply in replies:
        attr = Attribute.objects.filter(name=reply.the_attribute)
        if attr.exists():
            reply.attribute = attr.last()
            reply.save()
