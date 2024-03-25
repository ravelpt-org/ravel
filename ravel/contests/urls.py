from django.urls import path

from . import views
urlpatterns = [
    # contest links
    path('contests', views.contest_home, name='contests'),
    path('contests/<int:contest_id>', views.view_contest, name="view_contest"),
    path('contests/<int:contest_id>/submit', views.problem_submission, name="contest_submit"),

    # individual problem solving


    # teacher/admin stuff
    path('class', views.manage_class, name="manage_class"),
    path('system', views.manage_system, name="manage_system"),


    # contest scoreboard
    path('contests/<int:contest_id>/scoreboard', views.view_scoreboard, name='scoreboard'),

    # ajax request handlers
    path('ajax/problem', views.get_problem_as_modal, name="get_problem_modal"),
    path('ajax/load_contests', views.load_more_completed, name="load_more_completed"),
    path('ajax/submission', views.get_submission_as_modal, name="get_submission_modal"),
    path('ajax/edit/member', views.edit_member_modal, name="edit_member_modal"),
    path('ajax/edit/contest', views.edit_contest_modal, name="edit_contest_modal"),
    path('ajax/edit/problem', views.edit_problem_modal, name="edit_problem_modal"),
    path('ajax/edit/contest_problem', views.edit_contest_problem_modal, name="edit_contest_problem"),
    path('ajax/list/contest_problems', views.get_contest_problems, name="get_contest_problems"),
    path('ajax/sys/get_users', views.get_system_users, name="get_sys_users"),
    path('ajax/sys/get_problems', views.get_system_problems, name="get_sys_problems"),
    path('ajax/sys/get_contests', views.get_system_contests, name="get_sys_contests"),


    # POST handlers
    path('save/contest_problem', views.save_contest_problem, name="save_contest_problem"),
    path('delete/contest', views.delete_contest, name="delete_contest"),
    path('delete/problem', views.delete_problem, name="delete_problem"),
    path('delete/contest-problem', views.delete_contest_problem, name="delete_contest_problem"),
    path('users/kick', views.kick_member, name="kick_member"),

    # judge handlers
    path('judge/pending', views.get_awaiting_judge, name="judge_get_pending"),
    path('judge/problem', views.get_problem_judge, name="judge_get_problem"),
    path('judge/update', views.judge_update, name="judge_update_submission"),

    path('leave', views.leave_class, name="leave_class"),

]

app_name = "contests"
