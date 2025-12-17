import pytest
from django.conf import settings
from django.core.management import call_command
from django.db import connection


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    pass


@pytest.fixture(scope='session')
def django_db_modify_db_settings(postgresql_proc):
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'bo2005ok',
        'HOST': postgresql_proc.host,
        'PORT': postgresql_proc.port,
        'ATOMIC_REQUESTS': True,
    }