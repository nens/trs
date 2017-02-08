from django.forms import ChoiceField
from django.forms import Form
from django.forms import ModelForm
from trs.models import Project
from trs.models import Person


class ProjectTeamForm(ModelForm):

    class Meta:
        model = Project
        fields = ['reservation',
                  'profit',
                  ]


class NewMemberForm(Form):

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
        self.fields['new_team_member'] = ChoiceField(
            required=False,
            choices=choices)
