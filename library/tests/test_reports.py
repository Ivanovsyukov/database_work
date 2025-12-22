import pytest
from django.urls import reverse
from .factories import MemberFactory, BookFactory, BookCopyFactory
from django.utils import timezone
from datetime import timedelta
from library.models import Loan

@pytest.mark.django_db
def test_fines_report_updates_overdue_loans(admin_client):
    """Отчёт по штрафам — при запросе обновляет все просрочки → суммы актуальны"""
    
    # Создаём просроченную выдачу (7 дней)
    member = MemberFactory()
    copy = BookCopyFactory(status='available')
    loan_date = timezone.now().date() - timedelta(days=21)
    due_date = loan_date + timedelta(days=14)  # просрочка = 7 дней
    
    loan = Loan.objects.create(
        copy=copy,
        member=member,
        loan_date=loan_date,
        due_date=due_date,
        status='active'
    )
    
    # Убеждаемся, что штрафа ещё нет
    assert not hasattr(loan, 'fine')
    
    # Запрашиваем отчёт
    url = reverse('fines-summary')
    response = admin_client.get(url)
    
    assert response.status_code == 200
    assert response.data['unpaid_total'] == 70.0  # 7 * 10
    
    # Проверяем, что штраф создан
    loan.refresh_from_db()
    assert hasattr(loan, 'fine')
    assert loan.fine.fine_amount == 70

@pytest.mark.django_db
def test_fines_page_preparation(admin_client):
    """Страница штрафов — при заходе вызывает подготовку данных → штрафы актуальны"""
    
    # Создаём просроченную выдачу
    member = MemberFactory()
    copy = BookCopyFactory(status='available')
    loan_date = timezone.now().date() - timedelta(days=25)
    due_date = loan_date + timedelta(days=14)  # просрочка = 11 дней
    
    loan = Loan.objects.create(
        copy=copy,
        member=member,
        loan_date=loan_date,
        due_date=due_date,
        status='active'
    )
    
    # Запрашиваем подготовку данных (как делает страница штрафов)
    prepare_url = reverse('prepare-fines')
    prepare_response = admin_client.post(prepare_url)
    assert prepare_response.status_code == 200
    
    # Теперь запрашиваем все штрафы
    fines_url = reverse('fine-list')
    fines_response = admin_client.get(fines_url)
    
    assert fines_response.status_code == 200
    fines_data = fines_response.data
    if hasattr(fines_data, 'data'):
        fines_data = fines_data['data']
    
    # Ищем наш штраф
    fine_found = False
    for fine in fines_data:
        if fine['loan'] == loan.id:
            assert fine['fine_amount'] == '110.00'  # 11 * 10
            fine_found = True
            break
    
    assert fine_found

@pytest.mark.django_db
def test_popular_books_report(admin_client):
    """Популярные книги — сортировка по количеству выдач (num_loans)"""
    
    # Создаём книги
    book1 = BookFactory()
    book2 = BookFactory()
    
    # Книга 1: 3 выдачи
    for _ in range(3):
        copy = BookCopyFactory(book=book1)
        Loan.objects.create(
            copy=copy,
            member=MemberFactory(),
            loan_date=timezone.now().date() - timedelta(days=10),
            due_date=timezone.now().date() + timedelta(days=4),
            status='active'
        )
    
    # Книга 2: 1 выдача
    copy = BookCopyFactory(book=book2)
    Loan.objects.create(
        copy=copy,
        member=MemberFactory(),
        loan_date=timezone.now().date() - timedelta(days=5),
        due_date=timezone.now().date() + timedelta(days=9),
        status='active'
    )
    
    # Запрашиваем отчёт
    url = reverse('popular-books')
    response = admin_client.get(url)
    
    assert response.status_code == 200
    books = response.data
    if hasattr(books, 'data'):  # pagination
        books = books['data']
    
    # Проверяем сортировку (книга1 должна быть первой)
    assert len(books) >= 2
    assert books[0]['id'] == book1.id
    assert books[0]['num_loans'] == 3
    assert books[1]['id'] == book2.id
    assert books[1]['num_loans'] == 1

@pytest.mark.django_db
def test_member_activity_report(admin_client):
    """Активность читателей — топ по выдачам и количеству просрочек"""
    
    # Читатель 1: 3 выдачи, 2 просрочки
    member1 = MemberFactory()
    for i in range(3):
        copy = BookCopyFactory()
        loan_date = timezone.now().date() - timedelta(days=20)
        # Гарантируем, что due_date > loan_date
        due_date = loan_date + timedelta(days=7 + i)  # min 7 дней, max 9
        status = 'overdue' if i < 2 else 'active'
        
        # Для просроченных — искусственно делаем due_date в прошлом
        if status == 'overdue':
            due_date = timezone.now().date() - timedelta(days=5 - i)
            loan_date = due_date - timedelta(days=10)  # выдали за 10 дней до срока
        
        Loan.objects.create(
            copy=copy,
            member=member1,
            loan_date=loan_date,
            due_date=due_date,
            status=status
        )
    
    # Читатель 2: 1 выдача, 0 просрочек
    member2 = MemberFactory()
    copy = BookCopyFactory()
    Loan.objects.create(
        copy=copy,
        member=member2,
        loan_date=timezone.now().date() - timedelta(days=5),
        due_date=timezone.now().date() + timedelta(days=9),
        status='active'
    )
    
    # Запрашиваем отчёт
    url = reverse('member-activity')
    response = admin_client.get(url)
    
    assert response.status_code == 200
    members = response.data
    if hasattr(members, 'data'):  # pagination
        members = members['data']
    
    # Сортировка по количеству выдач (member1 первый)
    assert len(members) >= 2
    assert members[0]['id'] == member1.id
    assert members[0]['loans_count'] == 3
    assert members[0]['overdue_count'] == 2
    
    assert members[1]['id'] == member2.id
    assert members[1]['loans_count'] == 1
    assert members[1]['overdue_count'] == 0