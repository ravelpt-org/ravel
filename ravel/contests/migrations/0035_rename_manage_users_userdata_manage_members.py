# Generated by Django 4.2 on 2023-07-11 14:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0034_remove_userdata_is_admin_userdata_manage_contests_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userdata',
            old_name='manage_users',
            new_name='manage_members',
        ),
    ]
