from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from api.views import SubscriptionsViewSet, AddOrDeleteSubscription

router = routers.DefaultRouter()
router.register(
    'subscriptions',
    SubscriptionsViewSet,
    basename='subscriptions',
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls', namespace='api')),
    path('api/users/', include(router.urls)),
    path('api/users/<int:pk>/subscribe/', AddOrDeleteSubscription.as_view()),
    path('api/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
