"""Приложение админки для рецептов."""
from django.contrib import admin
from .models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
)


class RecipeIngredientInline(admin.TabularInline):
    """Inline для рецептов."""

    model = RecipeIngredient
    extra = 1
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов."""

    list_display = ('name', 'author', 'get_favorite_count')
    list_filter = ('author', 'name')
    search_fields = ('name', 'author__username')
    inlines = [RecipeIngredientInline]

    def get_favorite_count(self, obj):
        """Количество добавлений в избранное."""
        return Favorite.objects.filter(recipe=obj).count()
    get_favorite_count.short_description = 'Добавлено в избранное (раз)'


class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
