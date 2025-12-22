import pytest
from django.urls import reverse
from .factories import MemberFactory, BookFactory
from django.core import mail
from django.utils import timezone
from library.models import Reservation, Loan, BookCopy

@pytest.mark.django_db
def test_create_reservation(logged_in_client):
    """Создание брони — книга + читатель → запись в reservations"""
    book = BookFactory()
    member = MemberFactory()
    
    url = reverse('reservation-list')
    response = logged_in_client.post(url, {
        'book': book.id,
        'member': member.id,
        'expiry_date': '2025-12-31'
    }, content_type='application/json')
    
    assert response.status_code == 201
    assert response.json()['status'] == 'active'
    assert response.json()['book'] == book.id
    assert response.json()['member'] == member.id

@pytest.mark.django_db
def test_cannot_double_reserve(logged_in_client):
    """Повторное бронирование — той же книгой тем же читателем → ошибка"""
    book = BookFactory()
    member = MemberFactory()
    
    # Первая бронь
    url = reverse('reservation-list')
    response1 = logged_in_client.post(url, {
        'book': book.id,
        'member': member.id,
        'expiry_date': '2025-12-31'
    }, content_type='application/json')
    assert response1.status_code == 201
    
    # Вторая бронь — должна упасть
    response2 = logged_in_client.post(url, {
        'book': book.id,
        'member': member.id,
        'expiry_date': '2026-01-31'
    }, content_type='application/json')
    
    assert response2.status_code == 400
    assert 'already exists' in str(response2.data).lower() or 'active' in str(response2.data).lower()

@pytest.mark.django_db
def test_cancel_reservation(logged_in_client):
    """Отмена брони — статус 'cancelled'"""
    book = BookFactory()
    member = MemberFactory()
    
    reservation = Reservation.objects.create(
        book=book,
        member=member,
        expiry_date='2025-12-31'
    )
    
    url = reverse('reservation-cancel', args=[reservation.id])
    response = logged_in_client.put(url)
    
    assert response.status_code == 200
    assert response.json()['message'] == "Бронирование отменено"

@pytest.mark.django_db
def test_reservation_fulfilled_on_loan(logged_in_client):
    """Автоматическое завершение брони при выдаче — статус 'fulfilled'"""
    
    book = BookFactory()
    member = MemberFactory()
    
    # Создаём бронь
    reservation = Reservation.objects.create(
        book=book,
        member=member,
        expiry_date='2025-12-31'
    )
    
    # Создаём копию и выдаём именно этому читателю
    copy = BookCopy.objects.create(book=book, barcode='1234567890123')
    loan = Loan.objects.create(
        copy=copy,
        member=member,
        loan_date=timezone.now().date(),
        due_date=timezone.now().date() + timezone.timedelta(days=14),
        status='active'
    )
    
    # Проверяем, что бронь завершена
    reservation.refresh_from_db()
    assert reservation.status == 'fulfilled'

@pytest.mark.django_db
def test_email_sent_on_copy_availability(logged_in_client):
    """Отправка email при готовности брони — при возврате книги → письмо первому в очереди"""
    
    # Создаём книгу и копию
    book = BookFactory()
    copy = BookCopy.objects.create(book=book, barcode='1234567890124', status='available')
    
    # Создаём бронь
    member = MemberFactory(email='test@example.com')
    Reservation.objects.create(
        book=book,
        member=member,
        expiry_date='2025-12-31'
    )
    
    # Создаём выдачу и возвращаем книгу
    loan = Loan.objects.create(
        copy=copy,
        member=MemberFactory(),  # другой читатель
        loan_date=timezone.now().date() - timezone.timedelta(days=5),
        due_date=timezone.now().date() - timezone.timedelta(days=1),
        status='active'
    )
    
    # Возвращаем книгу → должно отправиться письмо
    url = reverse('loan-return-book', args=[loan.id])
    logged_in_client.put(url)
    
    # Проверяем email
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ['test@example.com']
    assert 'Ваша бронь готова!' in mail.outbox[0].subject