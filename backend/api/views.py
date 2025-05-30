"""Представления для приложения recipes."""
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from .filters import RecipeFilter, IngredientFilter
from recipes.models import (
    Ingredient, Recipe, Favorite, ShoppingCart, RecipeIngredient
)
from .serializers import (
    IngredientSerializer, RecipeSerializer, RecipeCreateUpdateSerializer,
    RecipeMinifiedSerializer
)
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from djoser import views as djoser_views
from rest_framework.permissions import IsAuthenticated, AllowAny

from users.models import User, Subscription

from .serializers import (
    UserCreateResponseSerializer,
    UserAvatarSerializer,
    SubscriptionListSerializer,
    SubscriptionCreateSerializer,
    SubscribeResponseSerializer
)


class UserPagination(PageNumberPagination):
    """Пагинация для пользователей."""

    page_size_query_param = 'limit'
    page_size = 6


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Права доступа к объектам только для автора."""

    def has_object_permission(self, request, view, obj):
        """Проверка прав доступа к объекту."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для рецептов."""

    queryset = Recipe.objects.all().order_by('-pub_date')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsAuthorOrReadOnly]
    pagination_class = UserPagination
    filter_backends = [
        DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter
    ]
    filterset_class = RecipeFilter
    search_fields = ['name', 'author__username']
    ordering_fields = ['pub_date', 'name']

    def get_serializer_class(self):
        """Возвращает соответствующий сериализатор."""
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        """Сохраняет автора рецепта."""
        serializer.save(author=self.request.user)

    def create(self, request):
        """Создает рецепт."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        response_serializer = RecipeSerializer(
            serializer.instance, context=self.get_serializer_context())
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data,
                        status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, **kwargs):
        """Обновляет рецепт."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance,
                                         data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance = self.get_object()
        response_serializer = RecipeSerializer(
            instance, context=self.get_serializer_context())
        return Response(response_serializer.data)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавляет или удаляет рецепт из избранного."""
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            if user.favorites.filter(recipe=recipe).exists():
                return Response(
                    {'errors': 'Recipe already in favorites.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        favorite_instance = user.favorites.filter(recipe=recipe)
        if not favorite_instance.exists():
            return Response(
                {'errors': 'Recipe not in favorites.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Удаляет рецепт из списка покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            if user.shopping_cart.filter(recipe=recipe).exists():
                return Response(
                    {'errors': 'Recipe already in shopping cart.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        cart_item = user.shopping_cart.filter(recipe=recipe)
        if not cart_item.exists():
            return Response(
                {'errors': 'Recipe not in shopping cart.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивает список покупок."""
        user = request.user
        shopping_list = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        lines = []
        if shopping_list.exists():
            for item in shopping_list:
                name = item['ingredient__name']
                unit = item['ingredient__measurement_unit']
                amount = item['total_amount']
                lines.append(f'{name} ({unit}) — {amount}')
        else:
            lines.append("Ваш список покупок пуст.")

        content = '\n'.join(lines)
        response = HttpResponse(
            content, content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe_instance = self.get_object()
        redirect_path = reverse(
            'short_url_redirect', args=[recipe_instance.pk]
        )
        host_part = request.get_host()
        scheme_part = request.scheme
        if redirect_path.startswith('/'):
            short_link_url = f"{scheme_part}://{host_part}{redirect_path}"
        else:
            short_link_url = f"{scheme_part}://{host_part}/{redirect_path}"
        return Response({'short-link': short_link_url},
                        status=status.HTTP_200_OK)


class CustomUserViewSet(djoser_views.UserViewSet):
    """Представление для пользователей."""

    pagination_class = UserPagination

    def get_permissions(self):
        """Возвращает список прав доступа для текущего действия."""
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    def create(self, request):
        """Создание пользователя."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_user = serializer.instance
        response_serializer = UserCreateResponseSerializer(
            response_user, context=self.get_serializer_context()
        )

        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        url_name='user-me-avatar',
        permission_classes=[permissions.IsAuthenticated]
    )
    def avatar(self, request):
        """Управление аватаром пользователя."""
        user = request.user
        if request.method == 'PUT':
            serializer = UserAvatarSerializer(
                user, data=request.data,
                context=self.get_serializer_context()
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsListView(ListAPIView):
    """Представление для списка подписок."""

    serializer_class = SubscriptionListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = UserPagination

    def get_queryset(self):
        """Получение списка подписок."""
        user = self.request.user
        subscribed_author_ids = user.follower.values_list(
            'author_id', flat=True
        )

        return User.objects.filter(id__in=subscribed_author_ids)


class SubscribeView(APIView):
    """Представление для подписки на пользователя."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        """Подписка на пользователя."""
        author = get_object_or_404(User, id=id)
        user = request.user

        serializer_create = SubscriptionCreateSerializer(
            data={'author': author.pk},
            context={'request': request}
        )
        serializer_create.is_valid(raise_exception=True)
        Subscription.objects.create(user=user, author=author)

        serializer_context = {'request': request}
        response_serializer = SubscribeResponseSerializer(
            instance=author, context=serializer_context
        )
        return Response(response_serializer.data,
                        status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        """Отписка от пользователя."""
        try:
            author = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response(
                {'errors': 'Пользователь для отписки не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        subscription = user.follower.filter(
            author=author).first()

        if not subscription:
            return Response(
                {'errors': 'Вы не были подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([AllowAny])
def short_url_redirect(request, recipe_pk):
    """Редирект с /s/ID/ на фронтенд-страницу рецепта."""
    target_recipe = get_object_or_404(Recipe, pk=recipe_pk)
    destination_url = f"/recipes/{target_recipe.pk}/"
    return HttpResponseRedirect(destination_url)
