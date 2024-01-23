from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet

from api.serializers import TagSerializer
from recipes.models import Tag


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
