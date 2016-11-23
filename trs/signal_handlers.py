from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from trs.models import Person


# Have the creation of a User trigger the creation of a Person.
# The receiver decorator makes the signal connection.
@receiver(post_save, sender=User)
def create_person(sender, instance, created, **kwargs):
    if created:
        if Person.objects.filter(user=instance).exists():
            return
        name = instance.first_name + ' ' + instance.last_name
        Person.objects.create(name=name,
                              user=instance)
