from django_filters import NumberFilter, AllValuesMultipleFilter
from django_filters.rest_framework import FilterSet
from rest_framework.filters import SearchFilter

from recipes.models import Recipe


class RecipesFilterBackend(FilterSet):
    author = NumberFilter(field_name='author__id')
    tags = AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = NumberFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited')

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        is_favorited = value
        if user.is_authenticated and is_favorited:
            return queryset.filter(id__in=user.favorites.values('recipe__id'))

        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        is_in_shopping_cart = value
        if user.is_authenticated and is_in_shopping_cart:
            return queryset.filter(id__in=user.shopping_list.values('recipe__id'))

        return queryset


class IngredientFilter(SearchFilter):
    search_param = 'name'
