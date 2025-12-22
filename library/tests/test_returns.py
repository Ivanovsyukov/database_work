import pytest
from django.urls import reverse
from .factories import MemberFactory, BookCopyFactory
from django.utils import timezone
from datetime import timedelta
from django.urls import get_resolver
from library.models import Loan

@pytest.mark.django_db
def test_return_book_updates_status(logged_in_client):
    """Возврат книги — статус выдачи 'returned', копия → 'available'"""
    
    # 1. Создаём ДОСТУПНУЮ копию
    member = MemberFactory(membership_status='active')
    copy = BookCopyFactory(status='available')
    
    # 2. Создаём выдачу → копия станет 'borrowed'
    loan = Loan.objects.create(
        copy=copy,
        member=member,
        loan_date=timezone.now().date() - timedelta(days=5),
        due_date=timezone.now().date() + timedelta(days=9),
        status='active'
    )
    
    # Проверяем, что копия теперь 'borrowed'
    copy.refresh_from_db()
    assert copy.status == 'borrowed'
    
    # 3. Возвращаем книгу
    url = reverse('loan-return-book', args=[loan.id])
    response = logged_in_client.put(url)
    
    assert response.status_code == 200
    assert response.json()['message'] == "Книга возвращена"
    
    # Проверяем, что копия стала 'available'
    copy.refresh_from_db()
    assert copy.status == 'available'

@pytest.mark.django_db
def test_second_return_is_ignored(logged_in_client):
    """Повторный возврат — игнорируется (статус уже 'returned')"""
    
    # То же самое: сначала доступная копия
    member = MemberFactory(membership_status='active')
    copy = BookCopyFactory(status='available')
    
    loan = Loan.objects.create(
        copy=copy,
        member=member,
        loan_date=timezone.now().date() - timedelta(days=10),
        due_date=timezone.now().date() - timedelta(days=3),
        status='active'
    )
    
    # Первый возврат
    url = reverse('loan-return-book', args=[loan.id])
    response1 = logged_in_client.put(url)
    assert response1.status_code == 200
    
    # Повторный возврат
    response2 = logged_in_client.put(url)
    assert response2.status_code == 400
    assert response2.json()['error'] == "Книга уже возвращена"
    
    copy.refresh_from_db()
    assert copy.status == 'available'