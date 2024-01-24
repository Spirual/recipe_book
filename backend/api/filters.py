from django_filters import CharFilter, NumberFilter, BooleanFilter
from django_filters.rest_framework import FilterSet

from recipes.models import Recipe, Tag


class RecipesFilterBackend(FilterSet):
    author = NumberFilter(field_name='author__id')
    tags = CharFilter(field_name='tags__slug', method='filter_tags')
    is_favorited = NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = NumberFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited')

    def filter_tags(self, queryset, name, value):
        tags = self.request.query_params.getlist('tags')
        return queryset.filter(tags__slug__in=tags).distinct()

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        is_favorited = bool(value)
        if is_favorited:
            queryset = queryset.filter(
                id__in=user.favorites.values('recipe__id')
            )
        else:
            queryset = queryset.exclude(
                id__in=user.favorites.values('recipe__id')
            )

        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        is_in_shopping_cart = bool(value)
        if is_in_shopping_cart:
            queryset = queryset.filter(
                id__in=user.shopping_list.values('recipe__id')
            )
        else:
            queryset = queryset.exclude(
                id__in=user.shopping_list.values('recipe__id')
            )

        return queryset
