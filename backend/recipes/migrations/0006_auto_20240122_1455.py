# Generated by Django 3.2.23 on 2024-01-22 11:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0005_auto_20240119_1234'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='subscription',
            name='unique_user_subscriber',
        ),
        migrations.RemoveConstraint(
            model_name='subscription',
            name='check_self_subscriber',
        ),
        migrations.RemoveField(
            model_name='subscription',
            name='user',
        ),
        migrations.AddField(
            model_name='subscription',
            name='author',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='subscribers', to='users.customuser', verbose_name='Пользователь'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='subscription',
            name='subscriber',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscribes', to=settings.AUTH_USER_MODEL, verbose_name='Подписчик'),
        ),
        migrations.AddConstraint(
            model_name='subscription',
            constraint=models.UniqueConstraint(fields=('author', 'subscriber'), name='unique_author_subscriber'),
        ),
        migrations.AddConstraint(
            model_name='subscription',
            constraint=models.CheckConstraint(check=models.Q(('author', django.db.models.expressions.F('subscriber')), _negated=True), name='check_self_subscriber'),
        ),
    ]
