import pytest
from io import StringIO
from django.core.management import call_command
from django.utils import timezone
from .factories import MemberFactory, BookCopyFactory
from datetime import timedelta

@pytest.mark.django_db
def test_update_overdue_loans_command():
    from library.models import Loan
    
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
    out = StringIO()
    call_command('update_overdue_loans', stdout=out)
    
    # Проверяем
    loan.refresh_from_db()
    assert loan.status == 'overdue'
    assert hasattr(loan, 'fine')
    assert 'Обновлено 1 просроченных выдач' in out.getvalue()