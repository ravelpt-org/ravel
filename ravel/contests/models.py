from django.contrib.auth.models import User
from django.db import models

from django.utils import timezone


# Create your models here.

class ProblemDifficulty(models.IntegerChoices):
    EASY = 1
    MEDIUM = 2
    HARD = 3


class Problem(models.Model):
    owner_class = models.ForeignKey("UserClass", blank=True, null=True, on_delete=models.CASCADE)
    name = models.TextField()
    short_name = models.CharField(max_length=6, blank=True)

    description = models.TextField()
    short_description = models.CharField(max_length=50, blank=True)

    difficulty = models.PositiveSmallIntegerField(choices=ProblemDifficulty.choices)

    input_description = models.TextField(blank=True)
    output_description = models.TextField(blank=True)

    image = models.ImageField(blank=True, null=True)

    origin_contest = models.TextField(blank=True)

    sample_in = models.TextField()
    sample_out = models.TextField()
    input = models.TextField()
    output = models.TextField()
    input_sum = models.TextField(default="")
    output_sum = models.TextField(default="")
    timeout = models.IntegerField(default=10)

    correct_attempts = models.IntegerField(default=0)
    wrong_attempts = models.IntegerField(default=0)

    def get_total_attempts(self):
        return self.correct_attempts + self.wrong_attempts


class ContestProblem(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    point_value = models.IntegerField()
    penalty_points = models.IntegerField()
    problem_order = models.IntegerField()

    first_solve = models.ForeignKey("UserProblem", on_delete=models.CASCADE, blank=True, null=True)
    correct_attempts = models.IntegerField(default=0)
    wrong_attempts = models.IntegerField(default=0)


class Contest(models.Model):
    name = models.TextField()
    description = models.TextField(blank=True)

    contest_class = models.ForeignKey("UserClass", on_delete=models.CASCADE, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    freeze_time = models.DateTimeField(blank=True, null=True)
    problems = models.ManyToManyField(ContestProblem, blank=True)

    show_difficulty = models.BooleanField(default=False)
    display_names = models.BooleanField(default=False)

    show_stats = models.BooleanField(default=True)
    use_global_stats = models.BooleanField(default=True)

    # returns True if the contest is open
    def is_open(self) -> bool:
        current = timezone.now()
        if current > self.start_time:
            if current < self.end_time:
                return True
        return False

    # returns True if the contest is frozen
    def is_frozen(self) -> bool:
        if self.is_open():
            if timezone.now() > self.freeze_time:
                return True
        return False

    def get_total_submissions(self):
        wrong_submissions = 0
        correct_submissions = 0

        for problem in self.problems.all():
            wrong_submissions += problem.wrong_attempts
            correct_submissions += problem.correct_attempts

        return wrong_submissions + correct_submissions, wrong_submissions, correct_submissions

    def overall_accuracy(self, as_html=True):

        submissions = self.get_total_submissions()

        if submissions[2] > 0:
            accuracy = round((100 / (submissions[1] + submissions[1])) * submissions[2])
        else:
            accuracy = 0

        if as_html:

            low_color = (0, 128, 0)
            high_color = (255, 0, 0)

            # this mess of code makes pretty accuracy colors. attempts to interpolate between green & red.
            # calculates each channel with the following formula:
            # color1 + ((color2-color1) * value / 100)

            new_r = int(high_color[0] + ((low_color[0] - high_color[0]) * accuracy / 100))
            new_g = int(high_color[1] + ((low_color[1] - high_color[1]) * accuracy / 100))
            new_b = int(high_color[2] + ((low_color[2] - high_color[2]) * accuracy / 100))

            color = f"{new_r:02x}{new_g:02x}{new_b:02x}"

            return f'<span style="color: #{color};">{accuracy}%</span>'
        else:
            return accuracy

    def participant_count(self):
        return len(UserContest.objects.filter(contest=self))

    def update_user_contests(self) -> None:
        problems = self.problems.all()
        problem_ids = [i.id for i in problems]

        for user_contest in UserContest.objects.filter(contest=self):
            user_problems = user_contest.user_problems.all()
            user_problem_ids = [x.problem.id for x in user_problems]

            for problem in problem_ids:
                if problem not in user_problem_ids:
                    new_problem = UserProblem(user=user_contest.user, user_contest=user_contest,
                                              problem=problems.get(id=problem))
                    new_problem.save()
                    user_contest.user_problems.add(new_problem)

            user_contest.save()


class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(ContestProblem, on_delete=models.CASCADE)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, null=True)
    submission = models.TextField()
    error = models.TextField(blank=True, null=True)
    language = models.CharField(max_length=15)
    time = models.DateTimeField(auto_now=True)
    pending = models.BooleanField(default=True)
    solved = models.BooleanField(default=False)


class UserProblem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_contest = models.ForeignKey("UserContest", on_delete=models.CASCADE)
    problem = models.ForeignKey(ContestProblem, on_delete=models.CASCADE)
    submissions = models.ManyToManyField(Submission, blank=True)
    wrong_attempts = models.IntegerField(default=0)
    correct_attempts = models.IntegerField(default=0)
    attempts_after_solve = models.IntegerField(default=0)
    solve_time = models.DateTimeField(null=True)
    is_first_solve = models.BooleanField(default=False)


class UserContest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    user_problems = models.ManyToManyField(UserProblem)
    total_solves = models.IntegerField(default=0)
    total_penalty_points = models.IntegerField(default=0)


class Team(models.Model):
    contests = models.ManyToManyField(Contest)
    team_name = models.TextField()
    members = models.ManyToManyField(User)


class UserData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_class = models.ForeignKey("UserClass", on_delete=models.CASCADE, blank=True, null=True, default=None)
    is_teacher = models.BooleanField(default=False)
    manage_members = models.BooleanField(default=False)
    manage_contests = models.BooleanField(default=False)
    manage_problems = models.BooleanField(default=False)

    def can_manage_class(self):
        return self.manage_members or self.manage_contests or self.manage_problems or self.is_teacher


class UserClass(models.Model):
    class_code = models.CharField(max_length=10, blank=False, null=False, unique=True)
    class_members = models.ManyToManyField(UserData)
    is_resource_class = models.BooleanField(default=False)

    # single function for adding users to a class (updates both them and the userclass)
    def join_class(self, user: UserData):
        # can't add a user to a class if they're already in one!
        if user.user_class is not None:
            return False
        else:
            user.user_class = self
            self.class_members.add(user)
            user.save()
            self.save()

            return True

    # single function for removing users from a class (updates both them and the userclass)
    def remove_from_class(self, user: UserData):
        # resets user to defaults before removing them
        if user.user_class is None:
            return False
        else:
            user.user_class = None
            user.is_teacher = False
            user.manage_members = False
            user.manage_contests = False
            user.manage_problems = False

            user.save()

            self.class_members.remove(user)
            self.save()

            return True


class ScoreboardUser:
    def __init__(self, _user):
        self.user = _user
        self.name = _user.username

        self.total_points = 0
        self.total_solves = 0
        self.total_submissions = 0
        self.total_first_solves = 0

        self.scores = {}
        self.sorted_scores = []

    def set_name(self, _name):
        self.name = _name

    def sort_scores(self, order):
        self.sorted_scores = []
        for problem in order:
            self.sorted_scores.append(self.scores[problem])

    def __gt__(self, other):
        if self.total_solves > other.total_solves:
            return True
        elif self.total_solves == other.total_solves:
            if self.total_solves == 0 and other.total_solves == 0:
                if self.total_submissions > other.total_submissions:
                    return True
            elif self.total_points < other.total_points:
                return True
            elif self.total_first_solves > other.total_first_solves:
                return True
        return False
