import pytest
from django.utils import timezone
from .factories import MemberFactory, BookCopyFactory, BookFactory
from datetime import timedelta
from library.models import Reservation
from library.models import Loan
from library.management.commands.update_overdue_loans import Command

@pytest.mark.django_db
def test_update_overdue_loans_command():
    
    # Создаём просроченную выдачу
    member = MemberFactory()
    copy = BookCopyFactory()
    loan = Loan.objects.create(
        copy=copy,
        member=member,
        loan_date=timezone.now().date() - timedelta(days=20),
        due_date=timezone.now().date() - timedelta(days=6),
        status='active'
    )
    
    # Запускаем команду
    Command().handle()
    
    # Проверяем
    loan.refresh_from_db()
    assert loan.status == 'overdue'
    assert hasattr(loan, 'fine')

@pytest.mark.django_db
def test_cleanup_expired_reservations():
    
    # Создаём просроченную бронь
    member = MemberFactory()
    book1 = BookFactory()
    book2 = BookFactory()
    reservation = Reservation.objects.create(
        book=book1,
        member=member,
        expiry_date=timezone.now().date() - timedelta(days=1),
        reservation_date=timezone.now().date() - timedelta(days=3),
        status='active'
    )
    
    # Создаём актуальную бронь (не должна отмениться)
    reservation2 = Reservation.objects.create(
        book=book2,
        member=member,
        expiry_date=timezone.now().date() + timedelta(days=10),
        status='active'
    )
    
    # Запускаем команду
    Command().handle()
    
    # Проверяем
    reservation.refresh_from_db()
    assert reservation.status == 'cancelled'
    
    reservation2.refresh_from_db()
    assert reservation2.status == 'active'