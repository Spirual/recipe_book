from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.template.loader import render_to_string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from api.filters import RecipesFilterBackend, IngredientFilter
from api.pagination import PageLimitPagination
from api.permissions import IsAuthorOrReadOnlyPermission
from api.serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeWriteSerializer,
    RecipeReadSerializer,
    FavoriteSerializer,
    SubscribedUserSerializer,
    ShortRecipeSerializer,
)
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
)

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    permission_classes = (IsAuthorOrReadOnlyPermission,)
    pagination_class = None
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ReadOnlyModelViewSet):
    pagination_class = None
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class RecipeViewSet(ModelViewSet):
    permission_classes = (IsAuthorOrReadOnlyPermission,)
    pagination_class = PageLimitPagination
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilterBackend

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = Recipe.objects.filter(pk=pk).first()
        user = request.user
        if request.method == 'POST':
            if not recipe:
                return Response(
                    {'errors': 'Рецепт с таким ID в базе не найден!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if user.favorites.filter(pk=recipe.pk).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.favorites.add(recipe)
            serializer = FavoriteSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if not recipe:
                return Response(
                    {'errors': 'Рецепт с таким ID в базе не найден!'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if user.favorites.filter(pk=recipe.pk).exists():
                user.favorites.remove(recipe)
                return Response(status=status.HTTP_204_NO_CONTENT)
            data = {'errors': 'Рецепт отсутствует в избранном.'}
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_list = user.shopping_list.all()

        aggregated_shopping_list = {}
        for recipe in shopping_list:
            for recipe_ingredient in recipe.ingredients.all():
                ingredient_name = recipe_ingredient.ingredient.name
                if ingredient_name in aggregated_shopping_list:
                    aggregated_shopping_list[ingredient_name][
                        'amount'
                    ] += recipe_ingredient.amount
                else:
                    aggregated_shopping_list[ingredient_name] = {
                        'amount': recipe_ingredient.amount,
                        'measurement_unit':
                            recipe_ingredient.ingredient.measurement_unit,
                    }

        context = {'shopping_list': aggregated_shopping_list}

        shopping_cart_text = render_to_string('shopping_list.txt', context)

        response = HttpResponse(shopping_cart_text, content_type='text/plain')
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping_list.txt"'

        return response

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = Recipe.objects.filter(pk=pk).first()
        user = request.user
        if request.method == 'POST':
            if not recipe:
                return Response(
                    {'errors': 'Рецепт с таким ID в базе не найден!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if user.shopping_list.filter(pk=recipe.pk).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.shopping_list.add(recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if not recipe:
                return Response(
                    {'errors': 'Рецепт с таким ID в базе не найден!'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if user.shopping_list.filter(pk=recipe.pk).exists():
                user.shopping_list.remove(recipe)
                return Response(status=status.HTTP_204_NO_CONTENT)
            data = {'errors': 'Рецепт отсутствует в списке покупок.'}
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)


class Subscriptions(APIView):
    permission_classes = (IsAuthorOrReadOnlyPermission,)
    pagination_class = PageLimitPagination

    def get(self, request):
        user = request.user
        subscribes = user.subscribes.all()
        paginator = PageLimitPagination()
        page = paginator.paginate_queryset(subscribes, request)
        serializer = SubscribedUserSerializer(
            page,
            many=True,
            context={'request': request},
        )
        return paginator.get_paginated_response(serializer.data)


class AddOrDeleteSubscription(APIView):
    permission_classes = (IsAuthorOrReadOnlyPermission,)

    def post(self, request, pk):
        author = get_object_or_404(User, pk=pk)
        user = request.user

        if user.subscribes.filter(pk=author.pk).exists():
            data = {'errors': 'Вы уже подписаны на этого пользователя.'}
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

        if author == user:
            data = {'errors': 'Нельзя подписаться на самого себя!'}
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

        user.subscribes.add(author)
        serializer = SubscribedUserSerializer(
            author,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        author = get_object_or_404(User, pk=pk)
        user = request.user
        if user.subscribes.filter(pk=author.pk).exists():
            user.subscribes.remove(author)
            return Response(status=status.HTTP_204_NO_CONTENT)
        data = {'errors': 'Такого пользователя нет в ваших подписках'}
        return Response(status=status.HTTP_400_BAD_REQUEST, data=data)
