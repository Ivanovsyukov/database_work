import pytest
from django.urls import reverse
from .factories import MemberFactory, BookCopyFactory
from library.models import Loan
from datetime import date, timedelta

@pytest.mark.django_db
def test_issue_book_to_active_member(logged_in_client):
    """Выдача книги активному читателю — статус выдачи 'active', копия → 'borrowed'"""
    member = MemberFactory(membership_status='active')
    copy = BookCopyFactory(status='available')
    
    url = reverse('loan-list')
    response = logged_in_client.post(url, {
        'copy': copy.id,
        'member': member.id,
        'due_date': '2025-12-31'
    })
    
    assert response.status_code == 201
    assert response.data['status'] == 'active'
    
    # Проверяем статус копии
    copy.refresh_from_db()
    assert copy.status == 'borrowed'

@pytest.mark.django_db
def test_cannot_issue_to_suspended_member(logged_in_client):
    """Выдача заблокированному читателю → ошибка"""
    member = MemberFactory(membership_status='suspended')
    copy = BookCopyFactory(status='available')
    
    url = reverse('loan-list')
    response = logged_in_client.post(url, {
        'copy': copy.id,
        'member': member.id,
        'due_date': '2025-12-31'
    })
    
    assert response.status_code == 400
    assert 'неактивен' in str(response.data).lower() or 'suspended' in str(response.data).lower()

@pytest.mark.django_db
def test_cannot_issue_nonexistent_copy(logged_in_client):
    """Выдача несуществующей копии → ошибка"""
    member = MemberFactory(membership_status='active')
    invalid_copy_id = 999999
    
    url = reverse('loan-list')
    response = logged_in_client.post(url, {
        'copy': invalid_copy_id,
        'member': member.id,
        'due_date': '2025-12-31'
    })
    
    assert response.status_code == 400
    assert 'неверный' in str(response.data).lower() or 'not found' in str(response.data).lower()

@pytest.mark.django_db
def test_custom_due_date_is_saved(logged_in_client):
    """Выдача с кастомной датой возврата — сохраняется указанная дата"""
    member = MemberFactory(membership_status='active')
    copy = BookCopyFactory(status='available')
    today = date.today()
    due_date = today + timedelta(days=30)  # через 30 дней
    
    url = reverse('loan-list')
    response = logged_in_client.post(url, {
        'copy': copy.id,
        'member': member.id,
        'due_date': due_date.isoformat()
    }, content_type='application/json')
    
    assert response.status_code == 201
    assert response.json()['due_date'] == due_date.isoformat()