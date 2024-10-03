# Generated by Django 4.2 on 2023-05-03 16:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0004_contestproblem_problem'),
    ]

    operations = [
        migrations.AddField(
            model_name='contestproblem',
            name='correct_attempts',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='contestproblem',
            name='show_stats',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='contestproblem',
            name='use_global_stats',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='contestproblem',
            name='wrong_attempts',
            field=models.IntegerField(default=0),
        ),
    ]