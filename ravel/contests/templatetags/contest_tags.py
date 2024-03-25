from django import template
from ..models import UserData, UserContest

register = template.Library()


@register.simple_tag
def get_problem_accuracy(contest_problem, use_global):
    if use_global:
        if contest_problem.problem.correct_attempts > 0 or contest_problem.problem.wrong_attempts > 0:
            return int(
                100 / (
                        contest_problem.problem.correct_attempts + contest_problem.problem.wrong_attempts)) * contest_problem.problem.correct_attempts
        else:
            return "--"
    else:
        if contest_problem.correct_attempts > 0 or contest_problem.wrong_attempts > 0:
            return int(100 / (
                    contest_problem.correct_attempts + contest_problem.wrong_attempts)) * contest_problem.correct_attempts
        else:
            return "--"


@register.simple_tag
def get_problem_correct(contest_problem, use_global):
    if use_global:
        return contest_problem.problem.correct_attempts
    else:
        return contest_problem.correct_attempts


@register.simple_tag
def get_problem_wrong(contest_problem, use_global):
    if use_global:
        return contest_problem.problem.wrong_attempts
    else:
        return contest_problem.wrong_attempts


@register.simple_tag
def get_rows(data):
    return data.count("\n") + 1


@register.simple_tag
def has_class_perms(user):
    return UserData.objects.get(user=user).can_manage_class()


@register.simple_tag
def is_teacher(user):
    return UserData.objects.get(user=user).is_teacher


@register.simple_tag
def in_class(user):
    return UserData.objects.get(user=user).user_class is not None


@register.simple_tag
def get_problem_count(contest):
    return len(contest.problems.all())


@register.simple_tag
def get_user_count(contest):
    return len(UserContest.objects.filter(contest=contest))
