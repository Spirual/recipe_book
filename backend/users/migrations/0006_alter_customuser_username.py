# Generated by Django 3.2.23 on 2024-02-02 17:50

import django.contrib.auth.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_auto_20240202_1102'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='username',
            field=models.CharField(max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='Имя пользователя'),
        ),
    ]
