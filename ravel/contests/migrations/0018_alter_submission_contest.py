# Generated by Django 4.2 on 2023-05-08 14:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0017_remove_userproblem_contest_problem_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='contest',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='contests.contest'),
        ),
    ]
