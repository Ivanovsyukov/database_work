"""
ASGI config for library_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
# Устанавливаем модуль настроек по умолчанию, если переменная окружения не задана.
# Это необходимо для корректной инициализации Django при запуске через ASGI-сервер.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_backend.settings')
# Создаём и экспортируем ASGI-приложение как модульную переменную `application`.
# Именно на эту переменную будет ссылаться ASGI-сервер.
application = get_asgi_application()
