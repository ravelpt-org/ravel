# Generated by Django 4.2 on 2023-05-12 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0019_alter_submission_submission'),
    ]

    operations = [
        migrations.AddField(
            model_name='userproblem',
            name='solve_time',
            field=models.DateTimeField(null=True),
        ),
    ]