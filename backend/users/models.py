from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from api import constants
from foodgram import settings


class CustomUser(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    email = models.EmailField(
        'Электронная почта',
        max_length=constants.EMAIL_MAX_LENGTH,
        unique=True,
    )
    username = models.CharField(
        'Имя пользователя',
        max_length=constants.USER_CHAR_FIELD_MAX_LENGTH,
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
        max_length=constants.USER_CHAR_FIELD_MAX_LENGTH,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=constants.USER_CHAR_FIELD_MAX_LENGTH,
    )
    password = models.CharField(
        'Пароль',
        max_length=constants.USER_CHAR_FIELD_MAX_LENGTH,
    )
    subscribes = models.ManyToManyField(
        'CustomUser',
        related_name='subscribers',
        blank=True,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
