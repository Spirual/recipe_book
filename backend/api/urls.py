from django.urls import include, path
from rest_framework import routers

from api.views import TagViewSet, IngredientViewSet, RecipeViewSet, \
    AddOrDeleteSubscription, Subscriptions

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    path('users/subscriptions/', Subscriptions.as_view()),
    path('users/<int:pk>/subscribe/', AddOrDeleteSubscription.as_view()),
]
