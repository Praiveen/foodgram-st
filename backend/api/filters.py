"""Фильтры для рецептов."""
from django_filters.rest_framework import FilterSet, filters
from recipes.models import Ingredient, Recipe


class RecipeFilter(FilterSet):
    """Фильтры для рецептов."""

    author = filters.NumberFilter(field_name='author__id')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        """Мета-класс для фильтрации рецептов."""

        model = Recipe
        fields = ('author', 'is_favorited', 'is_in_shopping_cart')

    def get_authenticated_user(self):
        """Возвращает аутентифицированного пользователя, если он есть."""
        if hasattr(self, 'request') and self.request and hasattr(self.request,
                                                                 'user'):
            return (
                self.request.user
                if self.request.user.is_authenticated
                else None
            )
        return None

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрует рецепты по наличию в избранном."""
        user = self.get_authenticated_user()
        if value and user:
            return queryset.filter(favorites__user=user).distinct()
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрует рецепты по наличию в корзине покупок."""
        user = self.get_authenticated_user()
        if value and user:
            return queryset.filter(shopping_carts__user=user).distinct()
        return queryset


class IngredientFilter(FilterSet):
    """Фильтры для ингредиентов."""

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        """Мета-класс для фильтрации ингредиентов."""

        model = Ingredient
        fields = ['name']
