"""URLs для приложения api."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet, RecipeViewSet, CustomUserViewSet,
    SubscriptionsListView, SubscribeView
)

app_name = 'api'

router = DefaultRouter()

router.register(r'users', CustomUserViewSet, basename='user')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')

custom_user_paths = [
    path(
        'users/subscriptions/',
        SubscriptionsListView.as_view(),
        name='subscriptions-list'
    ),
    path(
        'users/<int:id>/subscribe/',
        SubscribeView.as_view(),
        name='subscribe'
    ),
]

urlpatterns = [
    path('', include(custom_user_paths)),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
