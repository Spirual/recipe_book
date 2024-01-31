import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Загрузка ингридиентов в БД.
        with open(r'demo_data/ingredients.json', encoding='utf-8') as jsonfile:
            ingredients = json.load(jsonfile)
            for ingredient in ingredients:
                Ingredient.objects.create(
                    name=ingredient['name'],
                    measurement_unit=ingredient['measurement_unit'],
                )

        # Создание тегов для рецепта.
        Tag.objects.create(name='Завтрак', color='#FFA500', slug='breakfast')
        Tag.objects.create(name='Обед', color='#228B22', slug='lunch ')
        Tag.objects.create(name='Ужин', color='#483D8B', slug='dinner')
