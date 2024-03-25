from django.urls import path

from . import views
urlpatterns = [

    path('', views.index, name="index"),
    path('home', views.index, name="index"),
    path('about', views.about, name="about"),

    # user screens
    path('login', views.user_login, name="login"),
    path('logout', views.user_logout, name="logout"),
    path('create', views.user_create, name="create_account"),

    # css request handler
    path('files/css/styles', views.get_css_file, name="get_css_styles"),
]

app_name = "homesite"
