import pytest
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from library.models import Staff
from .factories import StaffFactory

@pytest.mark.django_db
def test_successful_staff_login(client):
    """Успешный вход — email есть в базе → staff_id в сессии"""
    staff = StaffFactory(email="librarian@test.com")
    
    response = client.post('/auth/login', {'email': 'librarian@test.com'})
    
    assert response.status_code == 200
    assert client.session['staff_id'] == staff.id

@pytest.mark.django_db
def test_failed_staff_login(client):
    """Неверный email — ошибка, сессии нет"""
    response = client.post('/auth/login', {'email': 'unknown@test.com'})
    
    assert response.status_code == 400  # или 401
    assert 'staff_id' not in client.session


@pytest.mark.django_db
def test_admin_can_create_librarian(admin_client):
    """Админ создаёт библиотекаря — сохраняется с ролью 'librarian'"""
    url = reverse('staff-list')  # или '/staff/'
    response = admin_client.post(url, {
        'first_name': 'Анна',
        'last_name': 'Петрова',
        'email': 'anna@test.com',
        'role': 'librarian'
    })

    assert response.status_code == 201
    assert response.data['role'] == 'librarian'
    
    # Проверяем, что сотрудник создан
    staff = Staff.objects.get(email='anna@test.com')
    assert staff.role == 'librarian'


@pytest.mark.django_db
def test_cannot_create_admin_via_api(admin_client):
    """Попытка создать админа через API — запрещено"""
    url = reverse('staff-list')
    response = admin_client.post(url, {
        'first_name': 'Злой',
        'last_name': 'Хакер',
        'email': 'hacker@test.com',
        'role': 'admin'
    })

    # Ожидаем ошибку или игнорирование роли
    assert response.status_code == 400
    assert 'error' in response.data
    # Убедимся, что админ не создан
    assert not Staff.objects.filter(email='hacker@test.com').exists()