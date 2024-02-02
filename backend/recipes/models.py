from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, MinValueValidator
from django.db import models

from api import constants

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название',
        unique=True,
        max_length=constants.CHAR_FIELD_MAX_LENGTH,
    )
    color = models.CharField(
        verbose_name='Цветовой HEX-код',
        unique=True,
        max_length=constants.TAG_COLOR_MAX_LENGTH,
        validators=[
            RegexValidator(
                regex=r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
                message='Введенное значение не является цветом в формате HEX!',
            )
        ],
    )
    slug = models.SlugField(
        verbose_name='Уникальный слаг',
        unique=True,
        max_length=constants.CHAR_FIELD_MAX_LENGTH,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название ингридиента',
        max_length=constants.CHAR_FIELD_MAX_LENGTH,
    )
    measurement_unit = models.CharField(
        max_length=constants.CHAR_FIELD_MAX_LENGTH,
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} [{self.measurement_unit}]'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=constants.CHAR_FIELD_MAX_LENGTH,
    )
    image = models.ImageField(
        verbose_name='Изображение блюда',
        upload_to='recipe_images/',
        blank=False,
        null=False,
    )
    text = models.TextField(verbose_name='Описание рецепта')
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes',
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(
                limit_value=constants.VALIDATE_MIN_VALUE,
                message=(
                    (
                        'Время приготовления не может быть меньше'
                        f' {constants.VALIDATE_MIN_VALUE} минуты'
                    ),
                ),
            ),
        ],
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )
    favorites = models.ManyToManyField(
        User,
        related_name='favorites',
        blank=True,
    )
    shopping_list = models.ManyToManyField(
        User,
        related_name='shopping_list',
        blank=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='Ингридиент'
    )
    amount = models.FloatField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(
                limit_value=constants.VALIDATE_MIN_VALUE,
                message=(
                    (
                        'Количество ингридиентов не может '
                        f'быть меньше {constants.VALIDATE_MIN_VALUE}'
                    ),
                ),
            ),
        ],
    )

    class Meta:
        verbose_name = 'Ингридиенты в рецепте'
        verbose_name_plural = 'Ингридиенты в рецепте'
