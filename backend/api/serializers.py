import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    Subscription,
    ShoppingList,
)

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context['request']
        return (
            request
            and request.user.is_authenticated
            and request.user.subscribes.filter(author=obj).exists()
        )


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagSerializer(ModelSerializer):
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
        request = self.context['request']
        return (
            request
            and request.user.is_authenticated
            and request.user.favorites.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context['request']
        return (
            request
            and request.user.is_authenticated
            and request.user.shopping_list.filter(recipe=obj).exists()
        )


class WriteRecipeIngredientSerializer(ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


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

    def validate(self, data):
        tags = data.get('tags')
        ingredients = data.get('ingredients')

        if not tags:
            raise ValidationError({'tags': 'Выберите хотя-бы один тег!'})
        tags_list = []
        for tag in tags:
            if tag.id not in tags_list:
                tags_list.append(tag.id)
            else:
                raise ValidationError({'tags': 'Теги не могут повторятся!'})

        if not ingredients:
            raise ValidationError(
                {'ingredients': 'Рецепт не может быть без ингредиентов!'}
            )
        ingredient_list = []
        for ingredient in ingredients:
            ingredient_name = ingredient['ingredient'].name

            if ingredient_name in ingredient_list:
                error = f'Ингридиент {ingredient_name} повторяется!'
                raise ValidationError({'ingredients': error})

            ingredient_list.append(ingredient_name)
        return data

    @transaction.atomic
    def create(self, validated_data):
        author = self.context['request'].user
        validated_data['author'] = author
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        self.process_recipe_ingredients(recipe, ingredients)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        instance.tags.clear()
        instance.tags.set(tags)

        instance.ingredients.all().delete()

        self.process_recipe_ingredients(instance, ingredients)

        instance = super().update(instance, validated_data)

        return instance

    @transaction.atomic
    def process_recipe_ingredients(self, recipe_instance, ingredients):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe_instance,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        ]

        RecipeIngredient.objects.bulk_create(recipe_ingredients)


class FavoriteSerializer(ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен!',
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return ShortRecipeSerializer(
            instance.recipe, context={'request': request}
        ).data


class ShoppingListSerializer(ModelSerializer):
    class Meta:
        model = ShoppingList
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен!',
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return ShortRecipeSerializer(
            instance.recipe, context={'request': request}
        ).data


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
        model = User

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        try:
            recipes_limit = int(
                self.context['request'].query_params.get('recipes_limit', 20)
            )
        except ValueError:
            recipes_limit = 20

        recipes = obj.recipes.all()[:recipes_limit]
        serializer = ShortRecipeSerializer(recipes, many=True)
        return serializer.data


class SubscribeSerializer(ModelSerializer):
    class Meta:
        fields = (
            'subscriber',
            'author',
        )
        model = Subscription
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('subscriber', 'author'),
                message='Вы уже подписаны на этого пользователя.',
            )
        ]

    def validate_author(self, data):
        request = self.context.get('request')
        user = request.user
        if user == data:
            raise ValidationError('Нельзя подписаться на самого себя!')
        return data

    def to_representation(self, instance):
        return SubscribedUserSerializer(
            instance.subscriber,
            context={'request': self.context.get('request')},
        ).data
