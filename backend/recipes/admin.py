from django.contrib import admin

from recipes.models import Tag, Ingredient, Recipe, RecipeIngredient, \
    Subscription, Favorite, ShoppingList


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    search_fields = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ('ingredient',)


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
    )
    list_filter = ('author', 'name', 'tags')
    list_display_links = ('name',)
    inlines = [RecipeIngredientInline]
    readonly_fields = ('favorite_count',)

    def favorite_count(self, obj):
        return obj.favorites.count()

    favorite_count.short_description = 'В избранном'


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Subscription)
admin.site.register(Favorite)
admin.site.register(ShoppingList)
admin.site.register(Tag)
