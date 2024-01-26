from django.contrib.auth import get_user_model
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
from api.serializers import TagSerializer, IngredientSerializer, \
    RecipeWriteSerializer, RecipeReadSerializer, FavoriteSerializer, \
    SubscribedUserSerializer
from recipes.models import Tag, Ingredient, Recipe, Favorite, Subscription

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
    search_fields = ('name',)


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
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        if request.method == 'POST':
            favorite = Favorite.objects.create(recipe=recipe, user=user)
            serializer = FavoriteSerializer(favorite)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            favorite = Favorite.objects.filter(recipe=recipe, user=user)
            if favorite.exists():
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            data = {'errors': 'Рецепт отсутствует в избранном.'}
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)


class SubscriptionsViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubscribedUserSerializer
    pagination_class = PageLimitPagination

    def get_queryset(self):
        return self.request.user.subscribes.all()


class AddOrDeleteSubscription(APIView):
    permission_classes = (IsAuthenticated,)

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
