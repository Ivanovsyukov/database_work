import pytest
from django.urls import reverse
from .factories import MemberFactory, BookCopyFactory
from django.utils import timezone
from django.utils import timezone
from datetime import timedelta
from library.models import Loan

@pytest.mark.django_db
def test_register_new_member(auth_client):
    """Регистрация нового читателя — email уникален, статус 'active'"""
    url = reverse('member-list')
    response = auth_client.post(url, {
        'first_name': 'Иван',
        'last_name': 'Иванов',
        'email': 'ivan@example.com',
        'phone': '+79991234567',
        'address': 'г. Москва, ул. Ленина, д. 1'
    })
    
    assert response.status_code == 201
    assert response.data['email'] == 'ivan@example.com'
    assert response.data['membership_status'] == 'active'
    
    # Проверяем уникальность email
    response2 = auth_client.post(url, {
        'first_name': 'Другой',
        'last_name': 'Человек',
        'email': 'ivan@example.com',  # ← тот же email!
        'phone': '+79999876543',
    })
    assert response2.status_code == 400
    assert 'email' in str(response2.data).lower()

@pytest.mark.django_db
def test_search_member_by_name(auth_client):
    """Поиск читателя по ФИО — совпадения по имени или фамилии"""
    MemberFactory(first_name='Александр', last_name='Пушкин', email='pushkin@example.com')
    MemberFactory(first_name='Анна', last_name='Каренина', email='karenina@example.com')
    MemberFactory(first_name='Иван', last_name='Грозный', email='grozny@example.com')
    
    # Поиск по имени
    url = reverse('member-list')
    response = auth_client.get(url, {'search': 'Анна'})
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['first_name'] == 'Анна'
    
    # Поиск по фамилии
    response = auth_client.get(url, {'search': 'Пушкин'})
    assert len(response.data) == 1
    assert response.data[0]['last_name'] == 'Пушкин'
    
    # Поиск по части имени
    response = auth_client.get(url, {'search': 'Ив'})
    assert len(response.data) == 1
    assert response.data[0]['first_name'] == 'Иван'

@pytest.mark.django_db
def test_member_blocked_on_large_fine(admin_client):
    """Блокировка читателя — при штрафе > 100 руб → статус 'suspended'"""
    from library.models import Loan
    member = MemberFactory()
    
    # Создаём выдачу в прошлом
    loan_date = timezone.now().date() - timedelta(days=20)
    due_date = loan_date + timedelta(days=14)  # срок возврата — через 14 дней
    # Сегодня: loan_date + 20 дней → просрочка = 6 дней → штраф = 60 руб
    
    # Нам нужно > 100 руб → просрочка > 10 дней
    # Устанавливаем due_date так, чтобы просрочка была 11 дней
    due_date = timezone.now().date() - timedelta(days=11)
    loan_date = due_date - timedelta(days=5)  # выдали за 5 дней до срока
    
    loan = Loan.objects.create(
        copy=BookCopyFactory(),  # ← нужно создать копию
        member=member,
        loan_date=loan_date,
        due_date=due_date,
        status='active'
    )
    
    # Переводим в статус overdue → создаём штраф
    loan.status = 'overdue'
    loan.save()
    
    member.refresh_from_db()
    assert member.membership_status == 'suspended'

@pytest.mark.django_db
def test_member_unblocked_after_fine_payment(admin_client):
    """Разблокировка читателя — после оплаты → статус 'active'"""
    
    member = MemberFactory()
    
    # То же самое: создаём корректную выдачу в прошлом
    due_date = timezone.now().date() - timedelta(days=15)
    loan_date = due_date - timedelta(days=5)
    
    loan = Loan.objects.create(
        copy=BookCopyFactory(),
        member=member,
        loan_date=loan_date,
        due_date=due_date,
        status='active'
    )
    
    loan.status = 'overdue'
    loan.save()
    
    member.refresh_from_db()
    assert member.membership_status == 'suspended'
    
    # Оплачиваем штраф
    url = reverse('fine-pay', args=[loan.fine.id])
    response = admin_client.put(url)
    assert response.status_code == 200
    
    member.refresh_from_db()
    assert member.membership_status == 'active'