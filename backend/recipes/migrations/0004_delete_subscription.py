# Generated by Django 3.2.23 on 2024-02-01 13:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_delete_shoppinglist'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Subscription',
        ),
    ]
