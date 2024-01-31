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
)
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import Serializer, ModelSerializer
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    Subscription,
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
        return current_user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        current_user = self.context['request'].user
        if not current_user.is_authenticated:
            return False
        return current_user.shopping_list.filter(recipe=obj).exists()


class WriteRecipeIngredientSerializer(Serializer):
    id = IntegerField()
    amount = IntegerField()


class RecipeWriteSerializer(ModelSerializer):
    image = Base64ImageField(required=True)
    ingredients = WriteRecipeIngredientSerializer(many=True)
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())

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

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise ValidationError({'tags': 'Теги не могут повторятся!'})
            else:
                tags_list.append(tag)
        if not tags:
            raise ValidationError({'tags': 'Выберите хотя-бы один тег!'})
        if not ingredients:
            raise ValidationError(
                {'ingredients': 'Рецепт не может быть без ингредиентов!'}
            )
        recipe = Recipe.objects.create(
            **validated_data,
        )
        recipe.tags.set(tags)
        ingredient_list = []
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            if ingredient_id in ingredient_list:
                raise ValidationError(
                    {
                        'ingredients': (
                            f'Ингридиента с id {ingredient_id} ' 'повторяется!'
                        )
                    }
                )
            else:
                ingredient_list.append(ingredient_id)
            db_ingredient = Ingredient.objects.filter(id=ingredient_id).first()
            if not db_ingredient:
                raise ValidationError(
                    {
                        'ingredients': (
                            f'Ингридиента с id {ingredient_id} '
                            'не существует!'
                        )
                    }
                )
            if ingredient['amount'] < 1:
                raise ValidationError(
                    {
                        'amount': (
                            (f'Кол-во ингридиента {db_ingredient.name} '
                             'меньше 1.')
                        )
                    }
                )
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=db_ingredient,
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
            raise ValidationError({'tags': 'Выберите хотя-бы один тег!'})
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise ValidationError({'tags': 'Теги не могут повторятся!'})
            else:
                tags_list.append(tag)

        ingredients = validated_data.get('ingredients')
        if not ingredients:
            raise ValidationError(
                {'ingredients': 'Необходим хотя бы один ингредиент.'}
            )
        instance.ingredients.all().delete()
        ingredient_list = []
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            amount = ingredient['amount']
            if ingredient_id in ingredient_list:
                raise ValidationError(
                    {
                        'ingredients': (
                            f'Ингридиента с id {ingredient_id} ' 'повторяется!'
                        )
                    }
                )
            else:
                ingredient_list.append(ingredient_id)
            db_ingredient = Ingredient.objects.filter(
                id=ingredient_id,
            ).first()
            if not db_ingredient:
                raise ValidationError(
                    {
                        'ingredients': (
                            f'Ингридиента с id {ingredient_id} '
                            'не существует!'
                        )
                    }
                )
            if amount < 1:
                raise ValidationError(
                    {
                        'amount': (
                            (f'Кол-во ингридиента {db_ingredient.name} '
                             'меньше 1.')
                        )
                    }
                )
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=db_ingredient,
                amount=amount,
            )
        instance.save()
        return instance


class FavoriteSerializer(ModelSerializer):
    id = SerializerMethodField(read_only=True)
    name = SerializerMethodField(read_only=True)
    image = SerializerMethodField(read_only=True)
    cooking_time = SerializerMethodField(read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Вы уже добавили этот рецепт.',
            )
        ]

    def get_id(self, obj):
        return obj.recipe.id

    def get_name(self, obj):
        return obj.recipe.name

    def get_image(self, obj):
        if obj.recipe.image:
            return obj.recipe.image.url
        return None

    def get_cooking_time(self, obj):
        return obj.recipe.cooking_time


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


class SubscribedUserSerializer(ModelSerializer):
    id = IntegerField(source='author.id')
    email = CharField(source='author.email')
    username = CharField(source='author.username')
    first_name = CharField(source='author.first_name')
    last_name = CharField(source='author.last_name')
    is_subscribed = SerializerMethodField()
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user

        return user.subscribes.filter(author=obj.author).exists()

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()

    def get_recipes(self, obj):
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit', 20
        )
        recipes = obj.author.recipes.all()[: int(recipes_limit)]
        serializer = ShortRecipeSerializer(recipes, many=True)
        return serializer.data
