import django.core.exceptions

from .models import Problem, Contest, Submission, UserContest, UserProblem, ContestProblem, UserData, UserClass, \
    ScoreboardUser
from django.contrib.auth import authenticate
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse, Http404
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from .utils import create_user_contest, permitted_contest, permitted_problem, sub_lists, \
    check_if_teacher, is_resource_account

from datetime import datetime

import hashlib
import json

SUPPORTED_JUDGE_LANGUAGES = {"Python": ["py"], "Java": ["java"]}


#  "CPP": ["cpp"]


# contest home
def contest_home(request):
    data = {"in_contest_home": True, "active_contests": [], "completed_contests": []}
    user = request.user  # get user

    # handles users submitting class join requests
    if request.method == "POST":
        user_data = UserData.objects.get(user=user)
        try:
            user_class = UserClass.objects.get(class_code=request.POST["class_code"])
        except django.core.exceptions.ObjectDoesNotExist:
            user_class = None
            data["join_error"] = True

        if user_class.is_resource_class:
            user_class = None
            data["join_error"] = True

        if user_class is not None and user_data.user_class is None:
            user_class.join_class(user_data)
            data["join_success"] = True
            data["class"] = user_class

    try:
        user_class = UserData.objects.get(user=user.id).user_class
    except django.core.exceptions.ObjectDoesNotExist:
        user_class = None

    contest_query = (Q(contest_class=None) | Q(contest_class=user_class))

    data["active_contests"] = Contest.objects.filter(contest_query, end_time__gt=timezone.now())
    data["active_contests"] = render_to_string("card-item-templates/active-contests.html", data)

    data["is_completed"] = True
    data["completed_contests"] = Contest.objects.filter(contest_query, end_time__lte=timezone.now()).order_by(
        "-end_time")[:8]
    data["completed_contests"] = render_to_string("card-item-templates/completed-contests.html", data)

    # if we did this when it was none it would double up system-wide
    # contests when the user is not in a class

    if user_class is None:
        data["has_no_class"] = True

    return render(request, "contest_home.html", data)


def load_more_completed(request):
    user = request.user
    data = {}

    try:
        user_class = UserData.objects.get(user=user.id).user_class
    except django.core.exceptions.ObjectDoesNotExist:
        user_class = None

    index = int(request.GET['index'])

    contest_query = (Q(contest_class=None) | Q(contest_class=user_class))

    data["completed_contests"] = Contest.objects.filter(contest_query, end_time__lte=timezone.now()).order_by(
        "-end_time")[index * 8:(index * 8) + 8]

    return render(request, "card-item-templates/completed-contests.html", data)


# contest homepage / problem display
def view_contest(request, **args):
    data = {"in_problems": True, "in_contest": True, "contest": Contest.objects.get(id=args['contest_id']),
            "problems": [[]]}

    if not permitted_contest(request.user, data['contest']):
        raise PermissionDenied

    # get user information, create it if not found
    if data["contest"].is_open():
        try:
            UserContest.objects.get(user=request.user, contest=data['contest'])
        except django.core.exceptions.ObjectDoesNotExist:
            create_user_contest(request.user, data['contest'])

    if timezone.now() < data["contest"].start_time:
        # alert that the contest is currently closed.
        data["problems"] = []
        data["contest_hidden"] = True
    else:
        # gets all problems in contest, sorted by problem_order
        data["problems"] = data["contest"].problems.all().order_by('problem_order')

    data["problems"] = render_to_string("card-item-templates/problems.html", data)

    return render(request, "contest.html", data)


# problem submission handling
def problem_submission(request, **args):
    data = {'in_submissions': True, 'contest': Contest.objects.get(id=args["contest_id"]), 'in_contest': True,
            'languages': SUPPORTED_JUDGE_LANGUAGES, 'submission_error': '', 'has_submission_error': False}
    user = request.user

    if not permitted_contest(user, data['contest']):
        raise PermissionDenied

    data['problems'] = data['contest'].problems.all()

    if request.method == "POST":
        if not data['contest'].is_open():
            data['has_submission_error'] = True
            data['submission_error'] = "This contest is closed."
        else:
            try:
                user_contest = UserContest.objects.get(user=user, contest=data['contest'])
            except django.core.exceptions.ObjectDoesNotExist:
                user_contest = create_user_contest(user, data['contest'])

            # Handle in-contest submissions
            contest_problem = data["contest"].problems.get(id=request.POST["problem"])

            # get/create a new user problem (tends to trigger when a problem gets swapped in the editor)
            try:
                user_problem = user_contest.user_problems.get(problem=contest_problem)
            except django.core.exceptions.ObjectDoesNotExist:
                user_problem = UserProblem(user=user, user_contest=user_contest, problem=contest_problem)
                user_problem.save()
                user_contest.user_problems.add(user_problem)
                user_contest.save()

            try:
                file_data = request.FILES["fileUpload"].read().decode()
            except:
                data['has_submission_error'] = True
                data['submission_error'] = "File could not be read."

            if not data['submission_error']:
                # generate submission
                submission = Submission(user=user, problem=contest_problem,
                                        language=request.POST["language"],
                                        submission=file_data,
                                        contest=data['contest'])

                submission.save()
                user_problem.submissions.add(submission)
                user_problem.save()

        # Handle out of contest submissions (WIP - Will be added later)

    data['submissions'] = Submission.objects.filter(user=user, contest=data['contest']).order_by('-id')

    return render(request, "submissions.html", data)


# scoreboard
def view_scoreboard(request, **args):
    # needs to be rewritten to cut down on time.
    # current system has to manually sort every user on the scoreboard everytime the page is loaded
    # which leads to very long load times.

    data = {'in_scoreboard': True, 'user': request.user, 'contest': Contest.objects.get(id=args['contest_id']),
            'in_contest': True}

    if not permitted_contest(data['user'], data['contest']):
        raise PermissionDenied

    # gets user contest - just to make sure you show up on the board if you haven't submitted anything
    if data['contest'].is_open():
        try:
            UserContest.objects.get(user=data['user'], contest=data['contest'])
        except django.core.exceptions.ObjectDoesNotExist:
            create_user_contest(data['user'], data['contest'])

    data['problem_set'] = data['contest'].problems.order_by('problem_order')

    order = []
    # creates problem order / penalty data / point value data
    for problem in data['problem_set']:
        order.append(problem.id)

    data['users'] = []

    # creates dictionary objects for user's score reports
    for score in UserContest.objects.filter(contest=data['contest']):
        user = ScoreboardUser(score.user)

        if data["contest"].display_names:
            user.set_name(f"{score.user.first_name} {score.user.last_name}")

        for user_problem in score.user_problems.all():
            problem_data = {
                'is_first_solve': user_problem.is_first_solve,
                'correct_attempts': user_problem.correct_attempts,
                'wrong_attempts': user_problem.wrong_attempts,
                'total_attempts': user_problem.correct_attempts + user_problem.wrong_attempts,
                'total_points': (user_problem.wrong_attempts * user_problem.problem.penalty_points)
            }

            try:
                problem_data['is_pending'] = user_problem.submissions.latest('time').pending
            except django.core.exceptions.ObjectDoesNotExist:
                problem_data['is_pending'] = False

            if problem_data['correct_attempts'] > 0:
                user.total_solves += user_problem.problem.point_value
                problem_data['total_points'] += int(
                    (user_problem.solve_time.timestamp() - data['contest'].start_time.timestamp()) / 60)

            if problem_data['is_first_solve']:
                user.total_first_solves += 1

            user.total_points += problem_data['total_points']
            user.total_submissions += problem_data['total_attempts']

            user.scores[user_problem.problem.id] = problem_data

        user.sort_scores(order)
        data['users'].append(user)

    data['users'] = sorted(data['users'], reverse=True)

    return render(request, "scoreboard.html", data)


# handles site staff
def manage_system(request):
    user = request.user

    if not user.is_staff:
        raise PermissionDenied

    # handle changes to problems/contests/members
    if request.method == "POST":
        if request.POST.get('editor') is not None:

            match request.POST["editor"]:  # ensure we're editing
                case "member":  # handle member editing
                    member = UserData.objects.get(id=request.POST["id"])

                    class_code = request.POST.get("class_code")

                    if class_code is not None:
                        current_class = member.user_class
                        try:
                            new_class = UserClass.objects.get(class_code=class_code)

                            if current_class is not None and current_class.class_code != class_code:
                                current_class.remove_from_class(member)

                            new_class.join_class(member)
                        except django.core.exceptions.ObjectDoesNotExist:
                            pass

                    member.is_teacher = bool(request.POST.get("is_teacher"))
                    member.user.is_staff = bool(request.POST.get("is_staff"))
                    member.user.username = request.POST.get("username")
                    member.user.save()

                    member.save()
                case "contest":  # handle contest editing
                    if request.POST.get("editing") is not None:
                        contest = Contest.objects.get(id=request.POST["id"])
                    else:
                        contest = Contest()

                    if contest.contest_class is not None:
                        raise PermissionDenied

                    # set contest information to updated versions
                    contest.name = request.POST['contest_name']
                    contest.description = request.POST['contest_description']
                    contest.start_time = timezone.make_aware(
                        datetime.strptime(request.POST['start_time'], '%Y-%m-%dT%H:%M'))
                    contest.end_time = timezone.make_aware(
                        datetime.strptime(request.POST['end_time'], '%Y-%m-%dT%H:%M'))

                    if request.POST.get('freeze_time') is None:
                        contest.freeze_time = None
                    else:
                        contest.freeze_time = timezone.make_aware(
                            datetime.strptime(request.POST['freeze_time'], '%Y-%m-%dT%H:%M'))

                    contest.display_names = bool(request.POST.get('show_names'))
                    contest.show_difficulty = bool(request.POST.get('show_difficulty'))
                    contest.show_stats = bool(request.POST.get('show_stats'))
                    contest.use_global_stats = bool(request.POST.get('use_global_stats'))

                    contest.save()

                case "problem":  # handle problem editing
                    if request.POST.get("editing") is not None:
                        problem = Problem.objects.get(id=request.POST["id"])
                    else:
                        problem = Problem()

                    if problem.owner_class is not None:
                        raise PermissionDenied

                    # update information as necessary
                    problem.name = request.POST['name']
                    problem.description = request.POST['description']
                    problem.input_description = request.POST['input_description']
                    problem.output_description = request.POST['output_description']
                    problem.sample_in = request.POST['sample_input']
                    problem.sample_out = request.POST['sample_output']
                    problem.input = request.POST['input'].replace("\r", "").strip()
                    problem.output = request.POST['output'].replace("\r", "").strip()
                    problem.input_sum = hashlib.md5(problem.input.encode('utf-8')).hexdigest()
                    problem.output_sum = hashlib.md5(problem.output.encode('utf-8')).hexdigest()
                    problem.timeout = request.POST['timeout']
                    problem.difficulty = request.POST['difficulty']

                    problem.save()

    return render(request, "manage_system.html")


def get_system_users(request):
    user = request.user

    if not user.is_staff:
        raise PermissionDenied

    data = {"members": []}

    if request.GET.get("start") is None:
        start = 0
        count = 10
    else:
        start = int(request.GET["start"])
        count = int(request.GET["count"])

    # returns information on members  - just removes the teacher so that they can't edit themselves
    for member in UserData.objects.all()[start:start + count]:
        if member != user:
            data["members"].append(member)

    if request.GET.get("as_modal") is not None:
        return render(request, "modals/system_member_manager.html", data)
    else:
        return render(request, "modals/system_member_manager_list.html", data)


def get_system_contests(request):
    sys_user = request.user

    if not sys_user.is_staff:
        raise PermissionDenied

    data = {'in_system': True, 'contests': []}

    if request.GET.get("start") is None:
        start = 0
        count = 10
    else:
        start = int(request.GET["start"])
        count = int(request.GET["count"])

    for contest in Contest.objects.filter(contest_class=None)[start:start + count]:
        data['contests'].append(contest)

    if request.GET.get("as_modal") is not None:
        return render(request, "modals/system_contest_manager.html", data)
    else:
        return render(request, "modals/system_contest_manager_list.html", data)


def get_system_problems(request):
    sys_user = request.user

    if not sys_user.is_staff:
        raise PermissionDenied

    data = {'in_system': True, 'problems': []}

    if request.GET.get("start") is None:
        start = 0
        count = 10
    else:
        start = int(request.GET["start"])
        count = int(request.GET["count"])

    for problem in Problem.objects.filter(owner_class=None)[start:start + count]:
        data['problems'].append(problem)

    if request.GET.get("as_modal") is not None:
        return render(request, "modals/system_problem_manager.html", data)
    else:
        return render(request, "modals/system_problem_manager_list.html", data)


# handles class manager tab
def manage_class(request):
    user = UserData.objects.get(user=request.user)
    user_class = user.user_class

    # we only want teachers and admins to access this page
    if not user.can_manage_class:
        raise PermissionDenied

    # handle changes to problems/contests/members
    if request.method == "POST":
        if request.POST.get('editor') is not None:

            match request.POST["editor"]:  # ensure we're editing
                case "member":  # handle member editing
                    if not user.manage_members and not user.is_teacher:
                        raise PermissionDenied

                    member = UserData.objects.get(id=request.POST["id"])
                    if user.user_class == member.user_class:
                        member.manage_members = bool(request.POST.get("manage_members"))
                        member.manage_problems = bool(request.POST.get("manage_problems"))
                        member.manage_contests = bool(request.POST.get("manage_contests"))

                        member.save()
                    else:
                        raise PermissionDenied
                case "contest":  # handle contest editing
                    if not user.manage_contests and not user.is_teacher:
                        raise PermissionDenied

                    if request.POST.get("editing") is not None:
                        contest = Contest.objects.get(id=request.POST["id"])
                    else:
                        contest = Contest()
                        contest.contest_class = user_class

                    if contest.contest_class != user_class:
                        raise PermissionDenied

                    # ensure user has permission
                    if user.user_class == contest.contest_class:

                        # set contest information to updated versions
                        contest.name = request.POST['contest_name']
                        contest.description = request.POST['contest_description']
                        contest.start_time = timezone.make_aware(
                            datetime.strptime(request.POST['start_time'], '%Y-%m-%dT%H:%M'))
                        contest.end_time = timezone.make_aware(
                            datetime.strptime(request.POST['end_time'], '%Y-%m-%dT%H:%M'))

                        if request.POST.get('freeze_time') is None:
                            contest.freeze_time = None
                        else:
                            contest.freeze_time = timezone.make_aware(
                                datetime.strptime(request.POST['freeze_time'], '%Y-%m-%dT%H:%M'))

                        contest.display_names = bool(request.POST.get('show_names'))
                        contest.show_difficulty = bool(request.POST.get('show_difficulty'))
                        contest.show_stats = bool(request.POST.get('show_stats'))
                        contest.use_global_stats = bool(request.POST.get('use_global_stats'))

                        contest.save()

                case "problem":  # handle problem editing
                    if not user.manage_problems and not user.is_teacher:
                        raise PermissionDenied
                    if request.POST.get("editing") is not None:
                        problem = Problem.objects.get(id=request.POST["id"])
                    else:
                        problem = Problem()
                        problem.owner_class = user.user_class

                    if problem.owner_class != user_class:
                        raise PermissionDenied

                    # ensure user has permission to edit problem
                    if problem.owner_class == user.user_class:
                        # update information as necessary
                        problem.name = request.POST['name']
                        problem.description = request.POST['description']
                        problem.input_description = request.POST['input_description']
                        problem.output_description = request.POST['output_description']
                        problem.sample_in = request.POST['sample_input']
                        problem.sample_out = request.POST['sample_output']
                        problem.input = request.POST['input'].strip()
                        problem.output = request.POST['output'].strip()
                        problem.input_sum = hashlib.md5(problem.input.encode('utf-8')).hexdigest()
                        problem.output_sum = hashlib.md5(problem.output.encode('utf-8')).hexdigest()
                        problem.timeout = request.POST['timeout']
                        problem.difficulty = request.POST['difficulty']

                        problem.save()

    data = {"in_teacher": True, "members": [], "contests": Contest.objects.filter(contest_class=user_class),
            "problems": Problem.objects.filter(owner_class=user_class), "user_class": user_class,
            "user_data": user}

    # returns information on members  - just removes the teacher so that they can't edit themselves
    for member in UserData.objects.filter(user_class=user_class):
        if member != user:
            data["members"].append(member)

    return render(request, "manage_class.html", data)


# handles viewing of problems
def get_problem_as_modal(request):
    data = {"page": request.GET["page"]}

    if request.GET.get('contest') is not None:
        data["contest"] = Contest.objects.get(id=request.GET["contest"])
        data["contest_problem"] = data["contest"].problems.get(id=request.GET["problem"])
        data["problem"] = data["contest_problem"].problem
        if not permitted_problem(request.user, data["problem"]):
            raise PermissionDenied

    # handles modal swapping in a single method
    if data["page"] == "desc":  # Returns description tab
        return render(request, "modals/problem_desc.html", data)
    elif data["page"] == "inout":  # Returns input/output tab
        return render(request, "modals/problem_inout.html", data)
    elif data["page"] == "sample":  # Returns sample cases tab
        return render(request, "modals/problem_sample.html", data)
    elif data["page"] == "submit":  # Returns problem submission page
        data['return'] = request.GET['return']
        data["languages"] = SUPPORTED_JUDGE_LANGUAGES
        return render(request, "modals/submission.html", data)


# handles submission modal
def get_submission_as_modal(request):
    try:
        data = {'submission': Submission.objects.get(user=request.user, id=request.GET['submission'])}
    except django.core.exceptions.ObjectDoesNotExist:
        raise Http404
    return render(request, "modals/submission_view.html", data)


def edit_member_modal(request):
    data = {"member": UserData.objects.get(id=request.GET["user"])}

    if request.user.is_staff and request.GET.get('system'):
        data['in_system'] = True

    return render(request, "modals/edit_member.html", data)


# modal for editing contests
def edit_contest_modal(request):
    if request.GET['contest'] == "-1":
        data = {'mode': 'Adding'}
    else:
        data = {"contest": Contest.objects.get(id=request.GET["contest"]), "mode": "Editing",
                "show_problem_button": True}

    if request.user.is_staff and request.GET.get('system'):
        data['in_system'] = True

    return render(request, "modals/edit_contest.html", data)


# modal for editing problems
def edit_problem_modal(request):
    if request.GET['problem'] == "-1":
        data = {'mode': 'Adding'}
    else:
        data = {"problem": Problem.objects.get(id=request.GET["problem"]), "mode": "Editing"}

    if request.user.is_staff and request.GET.get('system'):
        data['in_system'] = True

    return render(request, "modals/edit_problem.html", data)


# modal for listing contest problems
def get_contest_problems(request):
    if request.GET.get('contest') is not None:
        data = {"contest": Contest.objects.get(id=request.GET['contest'])}
    else:
        data = {"contest": Contest.objects.get(id=request.POST['contest_id'])}

    if not permitted_contest(request.user, data['contest']):
        raise PermissionDenied

    data["problems"] = data["contest"].problems.all().order_by("problem_order")

    return render(request, "modals/list_contest_problems.html", data)


# modal for editing contest problems
def edit_contest_problem_modal(request):
    user = UserData.objects.get(user=request.user)

    data = {"contest": Contest.objects.get(id=request.GET["contest"])}

    if not permitted_contest(request.user, data["contest"]):
        if not (not user.manage_contests or not check_if_teacher(request.user)):
            raise PermissionDenied

    if request.GET['problem'] == "-1":
        data["mode"] = "Adding"
        data["current_problem_id"] = "none"
    else:
        data["mode"] = "Editing"
        data["current_problem"] = data["contest"].problems.get(id=request.GET["problem"])
        data["current_problem_id"] = data["current_problem"].id

    data["problems"] = list(Problem.objects.filter(owner_class=None))
    if request.GET.get('system') is None:
        data["problems"].extend(
            list(Problem.objects.filter(owner_class=UserData.objects.get(user=request.user).user_class)))

    return render(request, "modals/edit_contest_problem.html", data)


# Saves contest problems edited from the class manager screen. This is handled separately from normal
# form submissions because we don't want the modal to close.
@require_POST
def save_contest_problem(request):
    user = UserData.objects.get(user=request.user)
    contest = Contest.objects.get(id=request.POST["contest_id"])

    if not permitted_contest(request.user, contest) or not (
            not user.manage_contests or not check_if_teacher(request.user)):
        raise PermissionDenied

    # no specified id - creating a new contest problem.
    if request.POST["id"] == "none":
        contest_problem = ContestProblem()
    else:
        contest_problem = contest.problems.get(id=request.POST["id"])

    problem = Problem.objects.get(id=request.POST["problem"])

    if not permitted_problem(request.user, problem):
        raise PermissionDenied

    contest_problem.problem = problem
    contest_problem.problem_order = request.POST["order"]
    contest_problem.point_value = request.POST["value"]
    contest_problem.penalty_points = request.POST["penalty_points"]

    contest_problem.save()

    if request.POST["id"] == "none":
        contest.problems.add(contest_problem)
        contest.save()

    contest.update_user_contests()

    return get_contest_problems(request)


# removes user from a class
@require_POST
def leave_class(request):
    user = request.user
    user_data = UserData.objects.get(user=user)

    if not user_data.is_teacher and user_data.user_class is not None:
        user_data.user_class.remove_from_class(user_data)

    return HttpResponse()


# judge awaiting endpoint
def get_awaiting_judge(request):
    if request.method == "GET":
        data = json.loads(request.body)
        # signs in a user, then checks their group permissions.
        user = authenticate(username=data['username'].lower(), password=data['password'])

        # ensure use has a resource account class
        if user is not None and is_resource_account(user):
            data = {"submissions": []}

            for submission in Submission.objects.filter(pending=True).order_by('time'):
                submission_data = {
                    "id": submission.id,
                    "language": submission.language,
                    "time": submission.time,
                    "content": submission.submission,
                    "problem": submission.problem.problem.id,
                    "input_sum": submission.problem.problem.input_sum,
                    "output_sum": submission.problem.problem.output_sum,
                    "timeout": submission.problem.problem.timeout,
                }
                data["submissions"].append(submission_data)

            return JsonResponse(data)

    raise PermissionDenied


def get_problem_judge(request):
    if request.method == "GET":
        data = json.loads(request.body)
        # signs in a user, then checks their group permissions.
        user = authenticate(username=data['username'].lower(), password=data['password'])

        # ensure use has a resource account class
        if user is not None and is_resource_account(user):
            problem = Problem.objects.get(id=data['problem'])
            data = {"problem_input": problem.input.replace("\r", "").strip(), "problem_output": problem.output.replace("\r", "").strip()}
            return JsonResponse(data)

    raise PermissionDenied


# delete a problem
@require_POST
def delete_problem(request):
    user = request.user
    user_data = UserData.objects.get(user=user)

    problem = Problem.objects.get(id=request.POST['problem'])

    if (not user_data.is_teacher and not user_data.manage_contests) and permitted_problem(user, problem):
        raise PermissionDenied

    problem.delete()

    return HttpResponse()


# delete a contest
@require_POST
def delete_contest(request):
    user = request.user
    user_data = UserData.objects.get(user=user)

    contest = Contest.objects.get(id=request.POST['contest'])

    if (not user_data.is_teacher and not user_data.manage_contests) and permitted_contest(user, contest):
        raise PermissionDenied

    contest.delete()

    return HttpResponse()


# delete a contest problem
@require_POST
def delete_contest_problem(request):
    user = request.user
    user_data = UserData.objects.get(user=user)

    contest = Contest.objects.get(id=request.POST['contest'])
    contest_problem = ContestProblem.objects.get(id=request.POST['problem'])

    if (not user_data.is_teacher and not user_data.manage_contests) and permitted_contest(user, contest):
        raise PermissionDenied

    contest_problem.delete()

    return HttpResponse()


# kick member from a class
@require_POST
def kick_member(request):
    to_kick = UserData.objects.get(user=request.POST["user"])
    kicker = UserData.objects.get(user=request.user)
    if (
            kicker.is_teacher or kicker.manage_members) and kicker.user_class == to_kick.user_class and not to_kick.is_teacher:
        to_kick.user_class.remove_from_class(to_kick)

    return manage_class(request)


# judge update endpoint
@require_POST
@csrf_exempt
def judge_update(request):
    post_data = json.loads(request.body)
    # signs in a user, then checks their group permissions.
    user = authenticate(username=post_data['username'].lower(), password=post_data['password'])

    # ensure use has a resource account class
    if user is not None and is_resource_account(user):

        data = {"response": "", "error": ""}

        if request.method == "POST":
            for update in post_data['submissions']:
                submission = Submission.objects.get(id=update['id'])
                submission.pending = False
                submission.solved = update['solved']
                submission.error = update['error']
                submission.save()

                user_problem = UserProblem.objects.get(
                    user_contest=UserContest.objects.get(user=submission.user, contest=submission.contest),
                    user=submission.user, problem=submission.problem)

                contest_problem = submission.contest.problems.get(problem=submission.problem.problem)

                if submission.solved:
                    user_problem.correct_attempts += 1
                    contest_problem.correct_attempts += 1
                    submission.problem.problem.correct_attempts += 1

                    if user_problem.solve_time is not None:
                        user_problem.attempts_after_solve += 1
                    else:
                        user_problem.solve_time = submission.time
                        user_problem.user_contest.total_solves += 1
                        user_problem.user_contest.total_penalty_points += int(
                            (submission.time.timestamp() - submission.contest.start_time.timestamp()) / 60)

                        if contest_problem.first_solve is None:
                            contest_problem.first_solve = user_problem
                            user_problem.is_first_solve = True
                else:
                    user_problem.wrong_attempts += 1
                    contest_problem.wrong_attempts += 1
                    submission.problem.problem.wrong_attempts += 1
                    user_problem.user_contest.total_penalty_points += contest_problem.penalty_points

                user_problem.user_contest.save()
                contest_problem.save()
                user_problem.save()
                submission.problem.problem.save()

            data["response"] = 0
        else:
            data["response"] = 500
            data["error"] = "Illegal method"

        return JsonResponse(data)

    return PermissionDenied
