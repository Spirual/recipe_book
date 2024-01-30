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
    Favorite,
    Subscription,
    ShoppingList,
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
            if Favorite.objects.filter(
                recipe=recipe,
                user=user,
            ).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            favorite = Favorite.objects.create(recipe=recipe, user=user)
            serializer = FavoriteSerializer(favorite)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if not recipe:
                return Response(
                    {'errors': 'Рецепт с таким ID в базе не найден!'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            favorite = Favorite.objects.filter(recipe=recipe, user=user)
            if favorite.exists():
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            data = {'errors': 'Рецепт отсутствует в избранном.'}
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_list = user.shopping_list.all()

        aggregated_shopping_list = {}
        for shopping_item in shopping_list:
            for recipe_ingredient in shopping_item.recipe.ingredients.all():
                ingredient_name = recipe_ingredient.ingredient.name
                if ingredient_name in aggregated_shopping_list:
                    aggregated_shopping_list[ingredient_name][
                        'amount'
                    ] += recipe_ingredient.amount
                else:
                    aggregated_shopping_list[ingredient_name] = {
                        'amount': recipe_ingredient.amount,
                        'measurement_unit': recipe_ingredient.ingredient.measurement_unit,
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
            if ShoppingList.objects.filter(
                recipe=recipe,
                user=user,
            ).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            shopping_list = ShoppingList.objects.create(
                recipe=recipe,
                user=user,
            )
            serializer = ShortRecipeSerializer(shopping_list.recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if not recipe:
                return Response(
                    {'errors': 'Рецепт с таким ID в базе не найден!'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            shopping_list = ShoppingList.objects.filter(
                recipe=recipe,
                user=user,
            )
            if shopping_list.exists():
                shopping_list.delete()
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

        subscription = Subscription.objects.filter(
            subscriber=user,
            author=author,
        )
        if subscription.exists():
            data = {'errors': 'Вы уже подписаны на этого пользователя.'}
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

        if author == user:
            data = {'errors': 'Нельзя подписаться на самого себя!'}
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

        subscription = Subscription.objects.create(
            subscriber=user,
            author=author,
        )
        serializer = SubscribedUserSerializer(
            subscription,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        author = get_object_or_404(User, pk=pk)
        user = request.user
        subscription = Subscription.objects.filter(
            subscriber=user,
            author=author,
        )
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        data = {'errors': 'Такого пользователя нет в ваших подписках'}
        return Response(status=status.HTTP_400_BAD_REQUEST, data=data)
