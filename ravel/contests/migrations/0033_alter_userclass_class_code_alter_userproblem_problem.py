# Generated by Django 4.2 on 2023-06-17 23:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0032_alter_userdata_user_class'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userclass',
            name='class_code',
            field=models.CharField(max_length=10, unique=True),
        ),
        migrations.AlterField(
            model_name='userproblem',
            name='problem',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contests.contestproblem'),
        ),
    ]
