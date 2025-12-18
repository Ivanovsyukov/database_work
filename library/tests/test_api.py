# library/tests/test_api.py
import pytest
from rest_framework.test import APIClient
from library.tests.factories import BookCopyFactory, MemberFactory, StaffFactory


@pytest.mark.django_db
def test_create_loan_via_api():
    client = APIClient()
    
    # Подготовка данных
    staff = StaffFactory()
    copy = BookCopyFactory()
    member = MemberFactory()

    # Логин сотрудника (сохраняет staff_id в сессии)
    login_res = client.post('/auth/login', {'email': staff.email}, format='json')
    assert login_res.status_code == 200
    
    # Запрос
    response = client.post('/loans', {
        'copy': copy.id,
        'member': member.id,
    }, format='json')
    
    # Проверка
    assert response.status_code == 201
    assert response.data['status'] == 'active'
    assert response.data['copy'] == copy.id


@pytest.mark.django_db
def test_get_books_list():
    client = APIClient()
    response = client.get('/books')
    assert response.status_code == 200
    assert isinstance(response.data, list)
