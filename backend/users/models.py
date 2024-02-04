from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from foodgram import constants


class CustomUser(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    email = models.EmailField(
        verbose_name='Электронная почта',
        unique=True,
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        unique=True,
        max_length=constants.USER_CHAR_FIELD_MAX_LENGTH,
        validators=[UnicodeUsernameValidator()],
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=constants.USER_CHAR_FIELD_MAX_LENGTH,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=constants.USER_CHAR_FIELD_MAX_LENGTH,
    )
    password = models.CharField(
        verbose_name='Пароль',
        max_length=constants.USER_CHAR_FIELD_MAX_LENGTH,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
