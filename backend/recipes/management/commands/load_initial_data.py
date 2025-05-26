"""Загружает начальные данные (админ, пользователи, рецепты)."""
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from recipes.models import Ingredient, Recipe, RecipeIngredient

User = get_user_model()


class Command(BaseCommand):
    """Загружает начальные данные (админ, пользователи, рецепты)."""

    def handle(self, *args, **options):
        """Выполняет логику загрузки начальных данных."""
        self.stdout.write(self.style.SUCCESS("Начало загрузки данных"))

        self._create_admin_user()
        created_users = self._create_regular_users()
        self._create_recipes(created_users)

        self.stdout.write(self.style.SUCCESS("Загрузка данных завершена."))

    def _create_admin_user(self):
        """Создает администратора, если он не существует."""
        admin_email = "admin@example.com"
        admin_password = "adminpassword123"
        if not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(
                email=admin_email,
                username="admin",
                first_name="Admin",
                last_name="User",
                password=admin_password,
            )
            self.stdout.write(
                self.style.SUCCESS(f'Администратор "{admin_email}" создан.')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Администратор "{admin_email}" уже есть.')
            )

    def _create_regular_users(self):
        """Создает обычных пользователей или получает существующих."""
        users_data = [
            {
                "email": "user1@example.com",
                "username": "user1",
                "first_name": "Alice",
                "last_name": "Smith",
                "password": "user1password",
            },
            {
                "email": "user2@example.com",
                "username": "user2",
                "first_name": "Bob",
                "last_name": "Johnson",
                "password": "user2password",
            },
        ]
        created_or_fetched_users = []
        for user_data in users_data:
            if not User.objects.filter(email=user_data["email"]).exists():
                user = User.objects.create_user(**user_data)
                created_or_fetched_users.append(user)
                self.stdout.write(
                    self.style.SUCCESS(f'User "{user_data["email"]}" created.')
                )
            else:
                user = User.objects.get(email=user_data["email"])
                created_or_fetched_users.append(user)
        if not created_or_fetched_users:
            self.stdout.write(
                self.style.WARNING("Не создано новых пользователей.")
            )
            existing_users = User.objects.exclude(is_superuser=True)
            if existing_users.exists():
                created_or_fetched_users.extend(list(existing_users))
            else:
                self.stdout.write(
                    self.style.ERROR("Нет доступных обычных пользователей.")
                )
                admin_user = User.objects.filter(is_superuser=True).first()
                if admin_user:
                    created_or_fetched_users.append(admin_user)
        return created_or_fetched_users

    def _create_recipes(self, authors):
        """Создает образцы рецептов, если они не существуют."""
        available_ingredients = list(Ingredient.objects.all())
        if not available_ingredients:
            self.stdout.write(
                self.style.ERROR("Нет ингредиентов.")
            )
            return

        if not authors:
            self.stdout.write(
                self.style.ERROR("Нет доступных авторов.")
            )
            return

        recipes_data = [
            {
                "name": "Яичница глазунья",
                "text": "Простой завтрак. Яйца на сковороду,"
                "соль, перец. Жарьте.",
                "cooking_time": 5,
            },
            {
                "name": "Куриный суп с лапшой",
                "text": "Отварите курицу, овощи, лапша."
                "Варите. Подавайте горячим.",
                "cooking_time": 45,
            },
            {
                "name": "Греческий салат",
                "text": "Овощи, оливки, фета. Масло, орегано.",
                "cooking_time": 15,
            },
        ]

        for recipe_data in recipes_data:
            if not Recipe.objects.filter(name=recipe_data["name"]).exists():
                author = random.choice(authors)
                recipe = Recipe.objects.create(
                    author=author,
                    name=recipe_data["name"],
                    text=recipe_data["text"],
                    cooking_time=recipe_data["cooking_time"],
                    pub_date=timezone.now(),
                )

                num_ingred = random.randint(1, min(3,
                                                   len(available_ingredients)))
                recipe_ingredients_sample = random.sample(
                    available_ingredients, num_ingred
                )
                for ingredient_obj in recipe_ingredients_sample:
                    RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient=ingredient_obj,
                        amount=random.randint(1, 100),
                    )

                self.stdout.write(
                    self.style.SUCCESS(f'Рецепт "{recipe.name}" создан.')
                )
