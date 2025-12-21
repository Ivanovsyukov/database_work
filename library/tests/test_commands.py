import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.core.management import call_command

from library.tests.factories import BookCopyFactory, MemberFactory
from library.models import Loan, Fine


@pytest.mark.django_db
def test_check_overdue_loans_creates_fine_and_updates_status():
    # Arrange: создаём данные
    copy = BookCopyFactory()
    member = MemberFactory()
    
    # Создаём выдачу, просроченную на 1 день
    loan = Loan.objects.create(
        copy=copy,
        member=member,
        loan_date=date.today() - timedelta(days=10),
        due_date=date.today() - timedelta(days=1),  # вчера
        status='active'
    )

    # Убеждаемся: штрафа нет
    assert Fine.objects.filter(loan=loan).exists() is False
    assert loan.status == 'active'
    assert copy.status == 'borrowed'  # Loan.save() уже пометил как borrowed

    # Act: запускаем команду из ТЗ
    call_command('check_overdue_loans')

    # Reload from DB
    loan.refresh_from_db()
    copy.refresh_from_db()
    member.refresh_from_db()

    # Assert
    assert loan.status == 'overdue'
    assert copy.status == 'borrowed'  # остаётся выданной

    fine = Fine.objects.get(loan=loan)
    assert fine.fine_amount == Decimal('10.00')  # 1 день × 10 руб
    assert fine.paid_date is None
    assert fine.loan.member == member


@pytest.mark.django_db
def test_member_suspended_when_fine_exceeds_100():
    copy = BookCopyFactory()
    member = MemberFactory()
    
    loan = Loan.objects.create(
        copy=copy,
        member=member,
        loan_date=date.today() - timedelta(days=20),
        due_date=date.today() - timedelta(days=5),
        status='active'
    )
    
    call_command('check_overdue_loans')  # создаёт штраф на 50 руб
    member.refresh_from_db()
    assert member.membership_status == 'active'  # ещё не >100

    # Вручную делаем штраф большим
    fine = Fine.objects.get(loan=loan)
    fine.fine_amount = Decimal('150.00')
    fine.save()

    member.refresh_from_db()
    assert member.membership_status == 'suspended'


@pytest.mark.django_db
def test_member_restored_after_fine_paid():
    copy = BookCopyFactory()
    member = MemberFactory()
    
    loan = Loan.objects.create(
        copy=copy,
        member=member,
        loan_date=date.today() - timedelta(days=15),
        due_date=date.today() - timedelta(days=11),
        status='active'
    )
    
    call_command('check_overdue_loans')  # штраф = 40 руб
    
    # Делаем штраф >100
    fine = Fine.objects.get(loan=loan)
    fine.fine_amount = Decimal('150.00')
    fine.save()
    
    member.refresh_from_db()
    assert member.membership_status == 'suspended'

    # Оплачиваем
    fine.pay()

    member.refresh_from_db()
    assert member.membership_status == 'active'
