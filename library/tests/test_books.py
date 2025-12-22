import pytest
from django.urls import reverse
from .factories import BookFactory, AuthorFactory, PublisherFactory
from library.models import Book

@pytest.mark.django_db
def test_create_book_with_authors(auth_client):
    """Создание книги с авторами — связь многие-ко-многим работает"""
    author1 = AuthorFactory()
    author2 = AuthorFactory()
    publisher = PublisherFactory()

    url = reverse('book-list')
    response = auth_client.post(url, {
        'title': 'Новая книга',
        'isbn': '1234567890123',
        'publication_year': 2025,
        'genre': 'Фантастика',
        'publisher_id': publisher.id,
        'author_ids': [author1.id, author2.id]
    })

    assert response.status_code == 201
    assert response.data['title'] == 'Новая книга'
    assert len(response.data['authors']) == 2
    author_ids = [a['id'] for a in response.data['authors']]
    assert author1.id in author_ids
    assert author2.id in author_ids

    # Проверяем в БД
    book = Book.objects.get(isbn='1234567890123')
    assert book.authors.count() == 2

@pytest.mark.django_db
def test_update_book_authors(auth_client):
    """Обновление авторов книги — старые удаляются, новые добавляются"""
    book = BookFactory()
    old_author = AuthorFactory()
    book.authors.add(old_author)

    new_author1 = AuthorFactory()
    new_author2 = AuthorFactory()
    publisher = PublisherFactory()

    url = reverse('book-detail', args=[book.id])
    response = auth_client.put(url, {
        'title': book.title,
        'isbn': book.isbn,
        'publication_year': book.publication_year,
        'genre': book.genre,
        'publisher_id': publisher.id,
        'author_ids': [new_author1.id, new_author2.id]
    }, content_type='application/json')

    assert response.status_code == 200
    assert len(response.data['authors']) == 2
    
    # Старый автор удалён
    author_ids = [a['id'] for a in response.data['authors']]
    assert old_author.id not in author_ids
    assert new_author1.id in author_ids
    assert new_author2.id in author_ids

@pytest.mark.django_db
def test_create_publisher_via_endpoint(auth_client):
    """Создание издательства через endpoint /publishers"""
    url = reverse('publisher-list')
    response = auth_client.post(url, {
        'name': 'Новое издательство',
        'address': 'г. Москва, ул. Пушкина, д. 10'
    })
    
    assert response.status_code == 201
    assert response.data['name'] == 'Новое издательство'
    
    # Проверяем, что можно использовать при создании книги
    book_url = reverse('book-list')
    book_response = auth_client.post(book_url, {
        'title': 'Книга с новым издательством',
        'isbn': '1234567890124',
        'publication_year': 2025,
        'genre': 'Роман',
        'publisher_id': response.data['id'],
        'author_ids': []
    })
    assert book_response.status_code == 201

@pytest.mark.django_db
def test_isbn_uniqueness(auth_client):
    """Уникальность ISBN — повторное создание → ошибка"""
    isbn = '9999999999999'
    publisher = PublisherFactory()
    
    # Создаём первую книгу
    url = reverse('book-list')
    response1 = auth_client.post(url, {
        'title': 'Книга 1',
        'isbn': isbn,
        'publication_year': 2025,
        'genre': 'Фантастика',
        'publisher_id': publisher.id,
        'author_ids': []
    })
    assert response1.status_code == 201

    # Пытаемся создать вторую с тем же ISBN
    response2 = auth_client.post(url, {
        'title': 'Книга 2',
        'isbn': isbn,  # ← тот же ISBN!
        'publication_year': 2024,
        'genre': 'Детектив',
        'publisher_id': publisher.id,
        'author_ids': []
    })
    
    assert response2.status_code == 400
    assert 'isbn' in str(response2.data).lower() or 'unique' in str(response2.data).lower()