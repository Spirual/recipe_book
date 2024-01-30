import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        with open(r'demo_data/ingredients.json', encoding='utf-8') as jsonfile:
            ingredients = json.load(jsonfile)
            for ingredient in ingredients:
                Ingredient.objects.create(
                    name=ingredient['name'],
                    measurement_unit=ingredient['measurement_unit'],
                )
