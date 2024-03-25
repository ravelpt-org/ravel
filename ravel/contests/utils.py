#
# Utility Functions
#
from .models import Contest, UserContest, UserProblem, UserData


# Creates a new UserContest object for a user joining a contest for the first time.
def create_user_contest(user, contest) -> UserContest:
    if not isinstance(contest, Contest):
        contest = Contest.objects.get(id=contest)
    user_contest = UserContest(user=user, contest=contest)
    user_contest.save()

    for problem in contest.problems.all():
        user_problem = UserProblem(user=user, user_contest=user_contest, problem=problem)
        user_problem.save()
        user_contest.user_problems.add(user_problem)

    user_contest.save()
    return user_contest


# check if a user is a teacher of a class
def check_if_teacher(user) -> bool:
    return UserData.objects.get(user=user).is_teacher


# Checks if a user's primary group allows them to view a contest
def permitted_contest(user, contest) -> bool:
    if user.is_staff is None and contest.contest_class is None:
        return True
    elif contest.contest_class is None or contest.contest_class == UserData.objects.get(user=user).user_class:
        return True
    else:
        return False


# Checks if a user's primary group allows them to view a problem
def permitted_problem(user, problem) -> bool:
    if problem.owner_class is None or problem.owner_class == UserData.objects.get(user=user).user_class:
        return True
    else:
        return False


# Splits a list into smaller sb-lists of a specified length
def sub_lists(items, size=4) -> list:
    _ = [[]]
    for item in items:
        # split problems into groups of 'size'
        if len(_[-1]) == size:
            _.append([item])
        else:
            _[-1].append(item)
    return _


# check if user is apart of resource class
def is_resource_account(user) -> bool:
    return UserData.objects.get(user=user).user_class.is_resource_class
