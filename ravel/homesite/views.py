from django.http import Http404, HttpResponse
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from django.apps import apps
UserData = apps.get_model("contests", "UserData")

from .utils import is_valid_email

import re

# Create your views here.


COLOR_SCHEMES = {
    "dark":
        {
            "primary": "#171717",
            "secondary": "#27272a",
            "accent": "#a855f7",
            "primary_text": "#fafafa",
            "secondary_text": "#d4d4d8",
            "primary_border": "#52525b",
        }
}


def index(request):
    data = {'in_home': True}
    return render(request, "index.html", data)


def about(request):
    data = {'in_about': True}
    return render(request, "about.html", data)


# login page
def user_login(request):
    error = False
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username.lower(), password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('contests:contests')
        else:
            error = True

    return render(request, 'login.html', {'login_page': True, 'error': error})


# logout
def user_logout(request):
    logout(request)
    return redirect('homesite:login')


# user creation screen
def user_create(request):
    data = {'login_page': True, 'error': ""}

    if request.method == "POST":
        data.update(request.POST)

        username = request.POST['username'].lower()

        # remove data that doesn't need to be passed again
        del data['csrfmiddlewaretoken']
        del data['password']
        del data['re_password']

        is_valid_user = True

        # check to make sure first/last name fields aren't empty
        if request.POST['first_name'].strip() == "":
            is_valid_user = False

        # check username validity
        if not len(re.findall(r"[a-zA-Z0-9@.+\-_]*", username)) == 2:
            data['username_error'] = "Invalid username. Only special characters @ . + - _ are allowed."
            is_valid_user = False
            user_check = None
        else:
            try:
                user_check = User.objects.get(username=username)
            except ObjectDoesNotExist:
                user_check = None

        # check username uniqueness
        if user_check is not None:
            data['username_error'] = "Username already in use."
            is_valid_user = False

        # check email validity
        if not is_valid_email(request.POST['email']):
            data['email_error'] = "Email is invalid."
            is_valid_user = False
            email_check = None
        else:
            try:
                email_check = User.objects.get(email=request.POST['email'])
            except ObjectDoesNotExist:
                email_check = None

        # check email uniqueness
        if email_check is not None:
            data['email_error'] = "Email already in use."
            is_valid_user = False

        # check password length
        if len(request.POST['password']) < 8:
            data['password_error'] = "Password must be at least 8 characters."
            is_valid_user = False
        # check passwords matching
        elif request.POST['password'] != request.POST['re_password']:
            data['password_error'] = "Passwords do not match."
            is_valid_user = False

        # create user & sign in
        if is_valid_user:
            user = User.objects.create_user(username=username, password=request.POST['password'],
                                            email=request.POST['email'],
                                            first_name=request.POST['first_name'], last_name=request.POST['last_name'])

            user_data = UserData(user=user)
            user_data.save()

            login(request, user)
            return redirect('contests:contests')

    return render(request, "new_user.html", data)


# returns the ./templates/css/styles.css file as a template
def get_css_file(request):
    data = COLOR_SCHEMES['dark']
    loaded = render_to_string("css/styles.css", data)
    response = HttpResponse(loaded)
    response['Content-Type'] = 'text/css'
    return response


# returns error page with proper error text
def return_error(request, *_, **exception):
    if exception.get('exception') is not None:
        if isinstance(exception['exception'], Http404):
            data = {"error_message": "404 - Page Not Found"}
        elif isinstance(exception['exception'], PermissionDenied):
            data = {"error_message": "403 - Forbidden"}
    else:
        data = {"error_message": "500 - Internal Server Error"}

    return render(request, "error.html", data)