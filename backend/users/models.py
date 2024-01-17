from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = 'admin'
    USER = 'user'


class CustomUser(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    email = models.EmailField(
        'Электронная почта',
        max_length=254,
        unique=True,
    )
    username = models.CharField(
        'Имя пользователя',
        max_length=150,
        unique=True,
    )
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    password = models.CharField('Пароль', max_length=150)
    role = models.CharField(
        verbose_name='Роль',
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.USER,
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    @property
    def is_admin(self):
        return (
            self.role == UserRole.ADMIN or self.is_staff or self.is_superuser
        )

    @property
    def is_user(self):
        return self.role == UserRole.USER

    def __str__(self):
        return self.username
