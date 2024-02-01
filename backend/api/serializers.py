import base64

import webcolors
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (
    IntegerField,
    SerializerMethodField,
    CharField,
    ImageField,
)
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import Serializer, ModelSerializer

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
)
from users.serializers import CustomUserSerializer

User = get_user_model()


class Hex2NameColor(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise ValidationError('Для этого цвета нет имени')
        return data


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagSerializer(ModelSerializer):
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(ModelSerializer):
    id = SerializerMethodField(read_only=True)
    name = SerializerMethodField(read_only=True)
    measurement_unit = SerializerMethodField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_id(self, obj):
        return obj.ingredient.id

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit


class RecipeReadSerializer(ModelSerializer):
    image = SerializerMethodField(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True, read_only=True)
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_is_favorited(self, obj):
        current_user = self.context['request'].user
        if not current_user.is_authenticated:
            return False
        return current_user.favorites.filter(pk=obj.pk).exists()

    def get_is_in_shopping_cart(self, obj):
        current_user = self.context['request'].user
        if not current_user.is_authenticated:
            return False
        return current_user.shopping_list.filter(pk=obj.pk).exists()


class WriteRecipeIngredientSerializer(Serializer):
    id = IntegerField()
    amount = IntegerField()


class RecipeWriteSerializer(ModelSerializer):
    image = Base64ImageField(required=True)
    ingredients = WriteRecipeIngredientSerializer(many=True)
    tags = PrimaryKeyRelatedField(
        many=True,
        required=True,
        queryset=Tag.objects.all(),
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeReadSerializer(
            instance, context={'request': request}
        ).data

    def validate_tags(self, data):
        if data is None or len(data) == 0:
            raise ValidationError({'tags': 'Выберите хотя-бы один тег!'})
        tags_list = []
        for tag in data:
            if not Tag.objects.filter(id=tag.id).exists():
                raise ValidationError(
                    {'tags': f'Тега с ID {tag.id} не существует.'}
                )
            if tag.id not in tags_list:
                tags_list.append(tag.id)
            else:
                raise ValidationError({'tags': 'Теги не могут повторятся!'})
        return data

    def validate_ingredients(self, data):
        if data is None or len(data) == 0:
            raise ValidationError(
                {'ingredients': 'Рецепт не может быть без ингредиентов!'}
            )
        ingredient_list = []
        for ingredient in data:
            ingredient_id = ingredient['id']
            db_ingredient = Ingredient.objects.filter(id=ingredient_id).first()

            if not db_ingredient:
                error = f'Ингридиента с id {ingredient_id} не существует!'
                raise ValidationError({'ingredients': error})

            if ingredient_id in ingredient_list:
                error = f'Ингридиент {db_ingredient.name} повторяется!'
                raise ValidationError({'ingredients': error})

            if ingredient['amount'] < 1:
                error = f'Кол-во ингридиента {db_ingredient.name} меньше 1.'
                raise ValidationError({'amount': error})

            ingredient_list.append(ingredient_id)
        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        if not ingredients:
            raise ValidationError(
                {'ingredients': 'Рецепт не может быть без ингредиентов!'}
            )
        tags = validated_data.pop('tags')
        if not tags:
            raise ValidationError({'tags': 'Рецепт не может быть без тегов!'})
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount'],
            )
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time,
        )

        tags = validated_data.get('tags')
        if not tags:
            raise ValidationError({'tags': 'Рецепт не может быть без тегов!'})
        instance.tags.clear()
        instance.tags.set(tags)

        ingredients = validated_data.get('ingredients')
        if not ingredients:
            raise ValidationError(
                {'ingredients': 'Рецепт не может быть без ингредиентов!'}
            )
        instance.ingredients.all().delete()
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount'],
            )
        instance.save()
        return instance


class FavoriteSerializer(Serializer):
    id = IntegerField()
    name = CharField()
    image = ImageField()
    cooking_time = IntegerField()


class ShortRecipeSerializer(ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class SubscribedUserSerializer(CustomUserSerializer):
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        recipes_limit = int(
            self.context['request'].query_params.get('recipes_limit', 20)
        )
        recipes = obj.recipes.all()[:recipes_limit]
        serializer = ShortRecipeSerializer(recipes, many=True)
        return serializer.data
