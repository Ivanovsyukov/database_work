# library/tests/test_api.py
import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from library.tests.factories import BookCopyFactory, MemberFactory


@pytest.mark.django_db
def test_create_loan_via_api():
    client = APIClient()
    
    # Подготовка данных
    copy = BookCopyFactory()
    member = MemberFactory()
    
    # Запрос
    response = client.post('/api/loans/', {
        'copy': copy.id,
        'member': member.id,
        'issued_by_staff_id': 1
    }, format='json')
    
    # Проверка
    assert response.status_code == 201
    assert response.data['status'] == 'active'
    assert response.data['copy'] == copy.id


@pytest.mark.django_db
def test_get_books_list():
    client = APIClient()
    response = client.get('/api/books/')
    assert response.status_code == 200
    assert isinstance(response.data, list)