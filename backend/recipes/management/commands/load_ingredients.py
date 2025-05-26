"""Импорты."""
import os
import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient
from django.conf import settings


class Command(BaseCommand):
    """Команда для загрузки ингредиентов."""

    help = 'Загружает ингредиенты из data/ingredients.json'

    def handle(self, *args, **options):
        """Обрабатывает команду."""
        file_path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.json')
        file_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Файл {file_path} не найден.'))
            return
        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)
        count = 0
        for item in data:
            name = item.get('name')
            measurement_unit = item.get('measurement_unit')
            if name and measurement_unit:
                obj, created = Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit
                )
                if created:
                    count += 1
        self.stdout.write(self.style.
                          SUCCESS(f'Загружено {count} новых ингредиентов.'))
