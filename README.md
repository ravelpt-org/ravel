# Ravel

An open-source platform for competitive programming practice, powered by [DeBussy](https://github.com/TimberCreekProgrammingTeam/debussy), written in Django Python.

---

### Features

- Classroom-based environments
- Public questions
- Custom questions
- Public contests
- Private contests

### Planned Features

- Profile pages
- Question PDFs
- Multi-file testcases
- Ability to join multiple classes
- Individual problem solving
- And more....

---

### Getting Started

Ravel uses a number of libraries to give the best user experience, and they are required to run the program. In order to download the packages, use the following pip command from the project's primary directory.

```pip install -r requirements.txt```

This command will install the following packages:
- [django](https://pypi.org/project/Django/)
- [django-debug-toolbar](https://pypi.org/project/django-debug-toolbar/)
- [pillow](https://pypi.org/project/pillow/)


The next step is to setup the database. Since Django does this already, we just need to run a command. In a terminal window, navigate to the `./ravel/` subdirectory and run the following command:

```
python manage.py migrate
```

The webservice can then be started with the `runserver` argument, where `ip` and `port` are the desired values:

```
python manage.py runserver ip:port
```

It is recommended that a superuser is created on the website in order to act as the site's admin. This can be achieved with the following Django command:

```
python manage.py createsuperuser
```