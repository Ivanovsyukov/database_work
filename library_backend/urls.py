"""
URL configuration for library_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Административная панель Django — используется администраторами и библиотекарями
    # для ручного управления записями (например, при отладке или массовом импорте).
    path('admin/', admin.site.urls),

    # Основные endpoint'ы API без префикса (рекомендуемый маршрут).
    # Примеры:
    #   POST /auth/login      → авторизация сотрудника
    #   GET  /books            → каталог книг
    #   POST /loans           → оформление выдачи
    path('', include('library.urls')),

    # Обратно совместимый маршрут с префиксом `/api`.
    # Позволяет поддерживать существующие вызовы от фронтенда или мобильного клиента,
    # если они были разработаны с ожиданием `/api/...`.
    # В будущем может быть удалён после миграции всех клиентов на корневые пути.
    path('api/', include('library.urls')),
]
