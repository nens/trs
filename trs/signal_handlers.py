from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from trs.models import Person


# Have the creation of a User trigger the creation of a Person.
# The receiver decorator makes the signal connection.
@receiver(post_save, sender=User)
def create_person(sender, instance, created, **kwargs):
    if created:
        if Person.objects.filter(user=instance).exists():
            return
        name = instance.first_name + " " + instance.last_name
        if not name:
            # Upon creation, the name isn't properly set yet.
            name = instance.username
        Person.objects.create(name=name, user=instance)
    else:
        # Probably the later update of the user to set the first/last name.
        if not Person.objects.filter(user=instance).exists():
            return
        person = Person.objects.get(user=instance)
        name = instance.first_name + " " + instance.last_name
        person.name = name
        person.save()
