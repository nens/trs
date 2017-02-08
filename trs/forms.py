from django.forms import ModelForm
from trs.models import Project
from trs.models import ThirdPartyEstimate


class ProjectTeamForm(ModelForm):

    class Meta:
        model = Project
        fields = ['reservation',
                  'profit',
                  ]
