import pytest
from django.urls import reverse
from .factories import BookFactory
from library.models import BookCopy

@pytest.mark.django_db
def test_add_book_copy(auth_client):
    """Добавление копии книги — статус 'available', привязана к книге"""
    book = BookFactory()
    
    url = reverse('bookcopy-list')
    response = auth_client.post(url, {
        'book': book.id,
        'barcode': '1234567890123'
    })
    
    assert response.status_code == 201
    assert response.data['status'] == 'available'
    assert response.data['book'] == book.id
    
    # Проверяем в БД
    copy = BookCopy.objects.get(barcode='1234567890123')
    assert copy.status == 'available'
    assert copy.book == book

@pytest.mark.django_db
def test_barcode_uniqueness(auth_client):
    """Уникальность штрихкода — повторный штрихкод → ошибка"""
    book1 = BookFactory()
    book2 = BookFactory()
    barcode = 'UNIQUE1234567'
    
    # Создаём первую копию
    url = reverse('bookcopy-list')
    response1 = auth_client.post(url, {
        'book': book1.id,
        'barcode': barcode
    })
    assert response1.status_code == 201

    # Пытаемся создать вторую копию с тем же штрихкодом
    response2 = auth_client.post(url, {
        'book': book2.id,  # Другая книга — но штрихкод тот же!
        'barcode': barcode
    })
    
    assert response2.status_code == 400
    assert 'barcode' in str(response2.data).lower() or 'unique' in str(response2.data).lower()