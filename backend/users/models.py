from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from foodgram import settings


class CustomUser(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    email = models.EmailField(
        'Электронная почта',
        max_length=settings.EMAIL_MAX_LENGTH,
        unique=True,
    )
    username = models.CharField(
        'Имя пользователя',
        max_length=settings.USER_CHAR_FIELD_MAX_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message=(
                    'Используются недопустимые ' 'символы в имени пользователя'
                ),
            )
        ],
    )
    first_name = models.CharField(
        'Имя',
        max_length=settings.USER_CHAR_FIELD_MAX_LENGTH,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=settings.USER_CHAR_FIELD_MAX_LENGTH,
    )
    password = models.CharField(
        'Пароль',
        max_length=settings.USER_CHAR_FIELD_MAX_LENGTH,
    )
    favorites = models.ManyToManyField(
        'recipes.Recipe',
        related_name='added_to_favorites',
    )
    shopping_list = models.ManyToManyField(
        'recipes.Recipe',
        related_name='added_to_shopping_list',
    )
    subscribes = models.ManyToManyField(
        'CustomUser',
        related_name='subscribers',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
