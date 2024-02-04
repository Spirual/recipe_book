from django.contrib.auth import get_user_model
from django.db.models import Sum, F
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
    SubscribeSerializer,
    ShoppingListSerializer,
)
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    Subscription,
    RecipeIngredient,
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

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        user = request.user
        data = {'user': user.pk, 'recipe': pk}
        serializer = FavoriteSerializer(
            context={'request': request}, data=data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite = Favorite.objects.filter(recipe=recipe, user=user)
        if not favorite.exists():
            data = {'errors': 'Рецепт отсутствует в избранном.'}
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user

        aggregated_shopping_list = (
            RecipeIngredient.objects.filter(recipe__shopping_list__user=user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(
                amount=Sum('amount'),
                name=F('ingredient__name'),
                measurement_unit=F('ingredient__measurement_unit'),
            )
        )

        context = {'shopping_list': aggregated_shopping_list}

        shopping_cart_text = render_to_string('shopping_list.txt', context)

        response = HttpResponse(shopping_cart_text, content_type='text/plain')
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping_list.txt"'

        return response

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        user = request.user
        data = {'user': user.pk, 'recipe': pk}
        serializer = ShoppingListSerializer(
            context={'request': request}, data=data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        shopping_list = ShoppingList.objects.filter(recipe=recipe, user=user)
        if not shopping_list.exists():
            data = {'errors': 'Рецепт отсутствует в списке покупок.'}
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)
        shopping_list.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class Subscriptions(APIView):
    permission_classes = (IsAuthorOrReadOnlyPermission,)

    def get(self, request):
        subscribes = User.objects.filter(
            subscribers__subscriber=self.request.user
        )
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
        data = {'subscriber': user.pk, 'author': author.pk}

        serializer = SubscribeSerializer(
            context={'request': request}, data=data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        author = get_object_or_404(User, pk=pk)
        user = request.user
        subscription = Subscription.objects.filter(
            subscriber=user,
            author=author,
        )
        if not subscription.exists():
            data = {'errors': 'Такого пользователя нет в ваших подписках'}
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
