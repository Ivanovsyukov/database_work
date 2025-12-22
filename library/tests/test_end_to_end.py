import pytest
from django.urls import reverse
from django.core import mail
from .factories import AuthorFactory, PublisherFactory, MemberFactory
from django.utils import timezone
from datetime import timedelta

@pytest.mark.django_db
def test_full_book_lifecycle(logged_in_client):
    """Полный цикл книги: создать → добавить копию → выдать → вернуть → проверить статусы"""
    
    # 1. Создаём книгу
    author = AuthorFactory(first_name='Лев', last_name='Толстой')
    publisher = PublisherFactory(name='Эксмо')
    book_url = reverse('book-list')
    book_response = logged_in_client.post(book_url, {
        'title': 'Война и мир',
        'isbn': '1234567890123',
        'publication_year': 2020,
        'genre': 'Роман',
        'publisher_id': publisher.id,
        'author_ids': [author.id]
    }, content_type='application/json')
    assert book_response.status_code == 201
    book_id = book_response.json()['id']
    
    # 2. Добавляем копию
    copy_url = reverse('bookcopy-list')
    copy_response = logged_in_client.post(copy_url, {
        'book': book_id,
        'barcode': 'BC123456789012'
    }, content_type='application/json')
    assert copy_response.status_code == 201
    copy_id = copy_response.json()['id']
    
    # 3. Выдаём книгу
    member = MemberFactory(first_name='Иван', last_name='Иванов')
    loan_url = reverse('loan-list')
    loan_response = logged_in_client.post(loan_url, {
        'copy': copy_id,
        'member': member.id,
        'due_date': (timezone.now().date() + timedelta(days=14)).isoformat()
    }, content_type='application/json')
    assert loan_response.status_code == 201
    loan_id = loan_response.json()['id']
    
    # Проверяем статус копии
    copy_detail = logged_in_client.get(reverse('bookcopy-detail', args=[copy_id]))
    assert copy_detail.json()['status'] == 'borrowed'
    
    # 4. Возвращаем книгу
    return_url = reverse('loan-return-book', args=[loan_id])
    return_response = logged_in_client.put(return_url)
    assert return_response.status_code == 200
    
    # Проверяем финальные статусы
    copy_detail = logged_in_client.get(reverse('bookcopy-detail', args=[copy_id]))
    assert copy_detail.json()['status'] == 'available'
    
    loan_detail = logged_in_client.get(reverse('loan-detail', args=[loan_id]))
    assert loan_detail.json()['status'] == 'returned'

@pytest.mark.django_db
def test_reservation_lifecycle(logged_in_client):
    """Цикл бронирования: забронировать → выдать другому → вернуть → проверить email и статус брони"""
    
    # 1. Создаём книгу и копию
    author = AuthorFactory(first_name='Агата', last_name='Кристи')
    publisher = PublisherFactory(name='АСТ')
    book_response = logged_in_client.post(reverse('book-list'), {
        'title': 'Десять негритят',
        'isbn': '1234567890124',
        'publication_year': 2019,
        'genre': 'Детектив',
        'publisher_id': publisher.id,
        'author_ids': [author.id]
    }, content_type='application/json')
    book_id = book_response.json()['id']
    
    copy_response = logged_in_client.post(reverse('bookcopy-list'), {
        'book': book_id,
        'barcode': 'BC123456789013'
    }, content_type='application/json')
    copy_id = copy_response.json()['id']
    
    # 2. Бронируем книгу (читатель 1)
    member1 = MemberFactory(first_name='Анна', last_name='Каренина', email='anna@example.com')
    reservation_response = logged_in_client.post(reverse('reservation-list'), {
        'book': book_id,
        'member': member1.id,
        'expiry_date': (timezone.now().date() + timedelta(days=30)).isoformat()
    }, content_type='application/json')
    assert reservation_response.status_code == 201
    reservation_id = reservation_response.json()['id']
    
    # 3. Выдаём книгу ДРУГОМУ читателю (читатель 2)
    member2 = MemberFactory(first_name='Пётр', last_name='Петров')
    loan_response = logged_in_client.post(reverse('loan-list'), {
        'copy': copy_id,
        'member': member2.id,
        'due_date': (timezone.now().date() + timedelta(days=14)).isoformat()
    }, content_type='application/json')
    assert loan_response.status_code == 201
    loan_id = loan_response.json()['id']
    
    # 4. Возвращаем книгу → должно прийти email читателю 1
    return_url = reverse('loan-return-book', args=[loan_id])
    logged_in_client.put(return_url)
    
    # Проверяем email
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ['anna@example.com']
    assert 'Ваша бронь готова!' in mail.outbox[0].subject
    
    # Проверяем статус брони
    reservation_detail = logged_in_client.get(reverse('reservation-detail', args=[reservation_id]))
    # Бронь должна остаться 'active' (не fulfilled, потому что выдали не тому)
    assert reservation_detail.json()['status'] == 'active'

@pytest.mark.django_db
def test_fine_lifecycle(admin_client):
    """Цикл штрафа: выдать → не вернуть 5 дней → проверить штраф → оплатить → проверить разблокировку"""
    
    # 1. Создаём книгу и копию
    author = AuthorFactory(first_name='Максим', last_name='Горький')
    publisher = PublisherFactory(name='Росмэн')
    book_response = admin_client.post(reverse('book-list'), {
        'title': 'Мать',
        'isbn': '1234567890125',
        'publication_year': 2021,
        'genre': 'Роман',
        'publisher_id': publisher.id,
        'author_ids': [author.id]
    }, content_type='application/json')
    book_id = book_response.json()['id']
    
    copy_response = admin_client.post(reverse('bookcopy-list'), {
        'book': book_id,
        'barcode': 'BC123456789014'
    }, content_type='application/json')
    copy_id = copy_response.json()['id']
    
    # 2. Выдаём книгу с просрочкой 5 дней
    member = MemberFactory(first_name='Сергей', last_name='Сергеев')
    loan_date = timezone.now().date() - timedelta(days=19)
    due_date = loan_date + timedelta(days=8)  # просрочка = 11 дней
    
    loan = type('Loan', (), {})()  # Хитрый способ — создаём через модель
    from library.models import Loan
    loan = Loan.objects.create(
        copy_id=copy_id,
        member=member,
        loan_date=loan_date,
        due_date=due_date,
        status='active'
    )
    
    # Делаем просрочку
    loan.status = 'overdue'
    loan.save()
    
    # 3. Проверяем штраф (110 руб)
    assert hasattr(loan, 'fine')
    assert loan.fine.fine_amount == 110
    
    # Проверяем блокировку
    member.refresh_from_db()
    assert member.membership_status == 'suspended'
    
    # 4. Оплачиваем штраф
    pay_url = reverse('fine-pay', args=[loan.fine.id])
    pay_response = admin_client.put(pay_url)
    assert pay_response.status_code == 200
    
    # 5. Проверяем разблокировку
    member.refresh_from_db()
    assert member.membership_status == 'active'