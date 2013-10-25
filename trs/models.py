from django.db import models

# TODO: add setting ADMIN_USER_CAN_DELETE_PERSONS_AND_PROJECTS
# TODO: add django-appconf


class Person(models.Model):
    slug = models.SlugField(
        verbose_name="ID voor in de URL")
    name = models.CharField(
        verbose_name="naam",
        max_length=255)
    description = models.CharField(
        verbose_name="omschrijving",
        blank=True,
        max_length=255)
    # Description on persons is useful for noting that someone doesn't work
    # for us anymore, for instance. And other corner cases.

    class Meta:
        verbose_name = "persoon"
        verbose_name_plural = "personen"
        ordering = ['name']

    def __str__(self):
        return "Person {}".format(self.name)


class Project(models.Model):
    slug = models.SlugField(
        verbose_name="ID voor in de URL")
    code = models.CharField(
        verbose_name="projectcode",
        max_length=255)
    description = models.CharField(
        verbose_name="omschrijving",
        blank=True,
        max_length=255)
    added = models.DateTimeField(
        auto_now_add=True,
        verbose_name="toegevoegd op")

    class Meta:
        verbose_name = "project"
        verbose_name_plural = "projecten"
        ordering = ['code']

    def __str__(self):
        return "Project {}".format(self.code)
