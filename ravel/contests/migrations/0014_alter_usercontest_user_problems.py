# Generated by Django 4.2 on 2023-05-08 14:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0013_alter_usercontest_user_problems'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usercontest',
            name='user_problems',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='contests.userproblem'),
        ),
    ]
