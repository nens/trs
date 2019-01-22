import django.forms as django_forms
from trs.models import Project
from trs.models import Person


class ProjectTeamForm(django_forms.ModelForm):

    class Meta:
        model = Project
        fields = ['reservation',
                  'software_development',
                  'profit',
                  ]


class NewMemberForm(django_forms.Form):

    def __init__(self, project, has_permission, *args, **kwargs):
        super(NewMemberForm, self).__init__(*args, **kwargs)
        if not has_permission:
            return

        already_known = project.assigned_persons().values_list(
            'id', flat=True)
        choices = list(Person.objects.filter(
            archived=False).exclude(
                id__in=already_known).values_list('pk', 'name'))
        choices.insert(0, ('', '---'))
        self.fields['new_team_member'] = django_forms.ChoiceField(
            required=False,
            choices=choices)


class ProjectMemberForm(django_forms.Form):

    person_id = django_forms.IntegerField(
        min_value=0,
        widget=django_forms.HiddenInput(),
        # TODO: set disabled=True after updating to django 1.9+
        )

    hours = django_forms.IntegerField(
        label='uren',
        required=False,
        min_value=0,
        widget=django_forms.TextInput(attrs={'size': 4,
                                             'type': 'number'}))
    # TODO: ideally, project managers cannot edit hours. This is now only
    # enforced through the UI. With django 1.9+ we can do more.

    hourly_tariff = django_forms.IntegerField(
        label='uurtarief',
        required=False,
        min_value=0,
        widget=django_forms.TextInput(attrs={'size': 4,
                                             'type': 'number'}))
