from django.db import models


attribute_types = (
    ('numeric', 'Numeric'),
    ('string', 'String'),
    ('date', 'Date'),
    ('boolean', 'Boolean'),
    ('category', 'Category')
)

# Attributes with attribute_view 'service' are used as parameters in services and will not be shown in views
attribute_view = (
    (0, 'service'),
    (1, 'data')
)


class Attribute(models.Model):
    name = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=20, choices=attribute_types, default='string')
    attribute_view = models.IntegerField(choices=attribute_view, default=1)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        permissions = (
            ('view_all_attributes', 'User can view all attributes for entities'),
        )
