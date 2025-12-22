import pytest
from django.test import Client
from rest_framework.test import APIClient
from .factories import StaffFactory

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def logged_in_client():
    """Клиент с реальной сессией (как в браузере)"""
    client = Client()
    staff = StaffFactory(email="librarian@test.com", role="librarian")
    # Выполняем логин
    client.post('/auth/login', {'email': 'librarian@test.com'})
    return client

@pytest.fixture
def librarian():
    return StaffFactory(role='librarian')

@pytest.fixture
def admin_user():
    return StaffFactory(role='admin')

@pytest.fixture
def auth_client(api_client, librarian):
    api_client.force_authenticate(user=librarian)
    return api_client

@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client