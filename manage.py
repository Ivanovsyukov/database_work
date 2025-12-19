#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    # Устанавливаем модуль настроек по умолчанию, если он ещё не задан
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_backend.settings')
    try:
        # Импортируем основную функцию Django для CLI
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Обработка ошибки: Django не найден
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # Выполняем команду, переданную через аргументы командной строки (sys.argv)
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
