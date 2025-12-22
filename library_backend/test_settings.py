from .settings import *

# Отключаем DEBUG для тестов (как в продакшене)
DEBUG = False

# Настраиваем тестовую базу данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_library_db',
        'USER': 'postgres',
        'PASSWORD': 'bo2005ok',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Отключаем рассылку email — всё в памяти
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Отключаем миграции для ускорения тестов (опционально)
class DisableMigrations:
    def __contains__(self, item):
        return True
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()