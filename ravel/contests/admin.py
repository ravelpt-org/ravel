from django.contrib import admin

from .models import Problem, Contest, ContestProblem, Team, Submission, UserData

# Register your models here.
admin.site.register(Team)
admin.site.register(Problem)
admin.site.register(Contest)
admin.site.register(ContestProblem)
admin.site.register(Submission)
admin.site.register(UserData)
