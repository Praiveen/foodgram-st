"""Сериализаторы для приложения users."""
import base64
import uuid

from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from users.models import User, Subscription
from foodgram_backend import constants

from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart
)


class RecipeMinifiedForUserSerializer(serializers.ModelSerializer):
    """Сериализатор для минимизированного представления рецептов."""

    class Meta:
        """Мета-класс."""

        from recipes.models import Recipe as ActualRecipe
        model = ActualRecipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class Base64ImageField(serializers.ImageField):
    """Изображения в формате base64 сохраняет как файлы."""

    def __init__(self, *args, **kwargs):
        """Инициализация класса."""
        self.file_prefix = kwargs.pop('file_prefix', 'file')
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        """Преобразование base64 в файл."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            filename = f'{self.file_prefix}_{uuid.uuid4()}.{ext}'
            data = ContentFile(base64.b64decode(imgstr), name=filename)
        return super().to_internal_value(data)


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для модели User."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        """Мета-класс для UserSerializer."""

        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )
        read_only_fields = DjoserUserSerializer.Meta.read_only_fields + (
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли запросивший пользователь."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return request.user.follower.filter(author=obj).exists()

    def get_avatar(self, obj):
        """Возвращает абсолютный URL для аватара."""
        request = self.context.get('request')
        if obj.avatar and hasattr(obj.avatar, 'url') and obj.avatar.url:
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class UserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователей, используемый Djoser."""

    class Meta(UserCreateSerializer.Meta):
        """Мета-класс для UserCreateSerializer."""

        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 'password'
        )


class UserCreateResponseSerializer(serializers.ModelSerializer):
    """Сериализатор для ответа при создании пользователя."""

    class Meta:
        """Мета-класс для UserCreateResponseSerializer."""

        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name'
        )
        read_only_fields = ('id',)


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""

    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        """Мета-класс для UserAvatarSerializer."""

        model = User
        fields = ['avatar']

    def to_representation(self, instance):
        """Возвращает абсолютный URL для аватара."""
        request = self.context.get('request')
        if request and instance.avatar and hasattr(instance.avatar,
                                                   'url'
                                                   ) and instance.avatar.url:
            return {'avatar': request.build_absolute_uri(instance.avatar.url)}
        return {'avatar': None}


class UserWithRecipesSerializer(UserSerializer):
    """Сериализатор для модели User, включающий их рецепты."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True)

    class Meta(UserSerializer.Meta):
        """Мета-класс для UserWithRecipesSerializer."""

        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')
        read_only_fields = UserSerializer.Meta.read_only_fields + \
            ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        """Получает ограниченное количество рецептов для пользователя."""
        request = self.context.get('request')
        limit = None
        if request:
            limit_str = request.query_params.get('recipes_limit')
            if limit_str:
                try:
                    limit = int(limit_str)
                    if limit <= 0:
                        limit = None
                except ValueError:
                    limit = None

        recipes_queryset = obj.recipes.all()
        if limit is not None:
            recipes_queryset = recipes_queryset[:limit]
        return RecipeMinifiedForUserSerializer(recipes_queryset, many=True,
                                               context=self.context).data


SubscriptionListSerializer = UserWithRecipesSerializer


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки."""

    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        """Мета-класс для SubscriptionCreateSerializer."""

        model = Subscription
        fields = ('author',)

    def validate(self, attrs):
        """Проверка данных для создания подписки."""
        request_user = self.context['request'].user
        author_to_subscribe = attrs['author']

        if request_user == author_to_subscribe:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя."
            )

        if Subscription.objects.filter(
            user=request_user, author=author_to_subscribe
        ).exists():
            raise serializers.ValidationError(
                "Вы уже подписаны на этого пользователя."
            )
        return attrs


class SubscribeResponseSerializer(UserSerializer):
    """Сериализатор для ответа при подписке/отписке."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True)

    class Meta(UserSerializer.Meta):
        """Мета-класс для SubscribeResponseSerializer."""

        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')
        read_only_fields = UserSerializer.Meta.read_only_fields + \
            ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        """Получает рецепты для подписанного автора, учитывая recipes_limit."""
        request = self.context.get('request')
        limit = None
        if request:
            limit_str = request.query_params.get('recipes_limit')
            if limit_str:
                try:
                    limit = int(limit_str)
                    if limit <= 0:
                        limit = None
                except ValueError:
                    limit = None
        recipes_queryset = obj.recipes.all()
        if limit is not None:
            recipes_queryset = recipes_queryset[:limit]
        return RecipeMinifiedForUserSerializer(recipes_queryset, many=True,
                                               context=self.context).data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        """Мета класс для сериализатора ингредиентов."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        """Мета класс для сериализатора ингредиентов в рецепте."""

        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeCreateIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для создания ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient')
    amount = serializers.IntegerField(
        min_value=constants.AMOUNT_INGREDIENTS_MIN,
        max_value=constants.AMOUNT_INGREDIENTS_MAX
    )

    class Meta:
        """Мета класс для сериализатора ингредиентов в рецепте."""

        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Сериализатор для минимизированного рецепта."""

    class Meta:
        """Мета класс для сериализатора минимизированного рецепта."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецепта."""

    author = serializers.SerializerMethodField()
    ingredients = RecipeIngredientSerializer(
        source='recipeingredients', many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        """Мета класс для сериализатора рецепта."""

        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'text',
            'ingredients',
            'cooking_time',
            'is_favorited', 'is_in_shopping_cart'
        )

    def get_author(self, obj):
        """Получение автора рецепта."""
        return UserSerializer(obj.author, context=self.context).data

    def get_is_favorited(self, obj):
        """Получение информации о том, является ли рецепт в избранном."""
        if 'request' in self.context and self.context['request']:
            user = self.context['request'].user
            if user.is_authenticated:
                return obj.favorites.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Получение информации о том, является ли рецепт в списке покупок."""
        if 'request' in self.context and self.context['request']:
            user = self.context['request'].user
            if user.is_authenticated:
                return obj.shopping_carts.filter(user=user).exists()
        return False

    def get_image(self, obj):
        """Получение изображения рецепта."""
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return ""


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""

    ingredients = RecipeCreateIngredientSerializer(many=True)
    image = Base64ImageField(required=True, allow_null=False)
    cooking_time = serializers.IntegerField(
        min_value=constants.COOKING_TIME_MIN,
        max_value=constants.COOKING_TIME_MAX
    )

    class Meta:
        """Мета класс для сериализатора создания и обновления рецепта."""

        model = Recipe
        fields = (
            'id', 'ingredients', 'image', 'name', 'text', 'cooking_time'
        )

    def validate_ingredients(self, value):
        """Валидация ингредиентов."""
        if not value:
            raise serializers.ValidationError(
                'Нужно добавить хотя бы один ингредиент.')
        seen = set()
        for item in value:
            ingredient = item['ingredient']
            if ingredient in seen:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.')
            seen.add(ingredient)
        return value

    def create_ingredients(self, recipe, ingredients_data):
        """Создание ингредиентов в рецепте."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            ) for item in ingredients_data
        ])

    def create(self, validated_data):
        """Создание рецепта."""
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта."""
        required_fields_for_update = {
            'ingredients', 'image', 'name', 'text', 'cooking_time'
        }
        missing_fields = []
        for field_name in required_fields_for_update:
            if field_name not in self.initial_data:
                missing_fields.append(field_name)

        if missing_fields:
            raise serializers.ValidationError({
                field: ['This field is required.'] for field in missing_fields
            })

        ingredients_data = validated_data.pop('ingredients', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if ingredients_data is not None:
            instance.recipeingredients.all().delete()
            self.create_ingredients(instance, ingredients_data)

        instance.save()
        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного."""

    recipe = RecipeMinifiedSerializer(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        """Мета класс для сериализатора избранного."""

        model = Favorite
        fields = ('id', 'user', 'recipe')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""

    recipe = RecipeMinifiedSerializer(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        """Мета класс для сериализатора списка покупок."""

        model = ShoppingCart
        fields = ('id', 'user', 'recipe')
