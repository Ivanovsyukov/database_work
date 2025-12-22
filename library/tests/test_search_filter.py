import pytest
from django.urls import reverse
from .factories import AuthorFactory, BookFactory, MemberFactory, BookCopyFactory
from django.utils import timezone
from datetime import timedelta
from library.models import Loan

@pytest.mark.django_db
def test_filter_books_by_author(logged_in_client):
    """Фильтрация книг по автору — возвращает только книги выбранного автора"""
    author1 = AuthorFactory(first_name='Лев', last_name='Толстой')
    author2 = AuthorFactory(first_name='Фёдор', last_name='Достоевский')
    
    # Книги Толстого
    book1 = BookFactory(title='Война и мир')
    book1.authors.set([author1])
    
    book2 = BookFactory(title='Анна Каренина')
    book2.authors.set([author1])
    
    # Книга Достоевского
    book3 = BookFactory(title='Преступление и наказание')
    book3.authors.set([author2])
    
    # Запрос книг по автору Толстого
    url = reverse('book-list')
    response = logged_in_client.get(url, {'author': author1.id})
    
    assert response.status_code == 200
    books = response.json()
    if isinstance(books, dict) and 'results' in books:  # если есть пагинация
        books = books['results']
    
    assert len(books) == 2
    book_ids = {book['id'] for book in books}
    assert book1.id in book_ids
    assert book2.id in book_ids
    assert book3.id not in book_ids

@pytest.mark.django_db
def test_filter_books_by_genre_and_year(logged_in_client):
    """Фильтрация книг по жанру/году — работает корректно"""
    # Книги разных жанров и лет
    book1 = BookFactory(title='Детектив 2020', genre='Детектив', publication_year=2020)
    book2 = BookFactory(title='Фантастика 2022', genre='Фантастика', publication_year=2022)
    book3 = BookFactory(title='Детектив 2022', genre='Детектив', publication_year=2022)
    
    # Фильтр: только детективы
    url = reverse('book-list')
    response = logged_in_client.get(url, {'genre': 'Детектив'})
    books = response.json()
    if isinstance(books, dict) and 'results' in books:
        books = books['results']
    
    assert len(books) == 2
    assert book1.id in [b['id'] for b in books]
    assert book3.id in [b['id'] for b in books]
    
    # Фильтр: только 2022 год
    response = logged_in_client.get(url, {'year': 2022})
    books = response.json()
    if isinstance(books, dict) and 'results' in books:
        books = books['results']
    
    assert len(books) == 2
    assert book2.id in [b['id'] for b in books]
    assert book3.id in [b['id'] for b in books]
    
    # Комбинированный фильтр: детективы 2022 года
    response = logged_in_client.get(url, {'genre': 'Детектив', 'year': 2022})
    books = response.json()
    if isinstance(books, dict) and 'results' in books:
        books = books['results']
    
    assert len(books) == 1
    assert books[0]['id'] == book3.id

@pytest.mark.django_db
def test_search_fines_by_member_name(logged_in_client):
    """Поиск штрафов по ФИО читателя — через автозаполнение → возвращает его штрафы"""
    from library.models import Loan
    
    # Создаём читателей с фиксированными именами
    member1 = MemberFactory(first_name='Иван', last_name='Иванов')
    member2 = MemberFactory(first_name='Петр', last_name='Петров')
    
    # Создаём штраф для Иванова
    copy1 = BookCopyFactory()
    loan1 = Loan.objects.create(
        copy=copy1,
        member=member1,
        loan_date=timezone.now().date() - timedelta(days=20),
        due_date=timezone.now().date() - timedelta(days=6),
        status='active'
    )
    loan1.status = 'overdue'
    loan1.save()
    
    # Создаём штраф для Петрова
    copy2 = BookCopyFactory()
    loan2 = Loan.objects.create(
        copy=copy2,
        member=member2,
        loan_date=timezone.now().date() - timedelta(days=20),
        due_date=timezone.now().date() - timedelta(days=8),
        status='active'
    )
    loan2.status = 'overdue'
    loan2.save()
    
    # ШАГ 1: Ищем читателя по ФИО "Иван"
    members_url = reverse('member-list')
    members_response = logged_in_client.get(members_url, {'search': 'Иван'})
    members_data = members_response.json()
    if isinstance(members_data, dict) and 'results' in members_data:
        members_data = members_data['results']
    
    assert len(members_data) == 1
    found_member_id = members_data[0]['id']
    assert found_member_id == member1.id
    
    # ШАГ 2: Получаем штрафы этого читателя
    fines_url = reverse('fine-by-member', args=[found_member_id])
    fines_response = logged_in_client.get(fines_url)
    
    assert fines_response.status_code == 200
    fines_data = fines_response.json()
    if isinstance(fines_data, dict) and 'results' in fines_data:
        fines_data = fines_data['results']
    
    # Должен быть только штраф Иванова
    assert len(fines_data) == 1
    assert fines_data[0]['loan'] == loan1.id