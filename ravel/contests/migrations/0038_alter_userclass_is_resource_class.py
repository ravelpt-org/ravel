# Generated by Django 4.2 on 2023-07-24 16:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0037_rename_is_resouce_class_userclass_is_resource_class'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userclass',
            name='is_resource_class',
            field=models.BooleanField(default=False),
        ),
    ]