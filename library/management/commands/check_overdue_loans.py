from django.core.management.base import BaseCommand
from django.utils import timezone
from library.models import Loan

class Command(BaseCommand):
    help = 'Automatically mark overdue loans and create fines'

    def handle(self, *args, **options):
        today = timezone.now().date()
        # Найти все активные выдачи с просроченной датой возврата
        overdue_loans = Loan.objects.filter(
            status='active',
            due_date__lt=today
        )
        count = 0
        for loan in overdue_loans:
            loan.status = 'overdue'
            loan.save(update_fields=['status'])  # это вызовет создание штрафа и обновление статуса читателя
            count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {count} loans to overdue')
        )