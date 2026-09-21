# main_app/api_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import GameViewSet, FieldViewSet

router = DefaultRouter()
router.register(r'games', GameViewSet, basename='game')
router.register(r'fields', FieldViewSet, basename='field')

urlpatterns = [
    path('', include(router.urls)),
]