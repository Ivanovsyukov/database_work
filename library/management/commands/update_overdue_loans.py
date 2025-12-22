from django.core.management.base import BaseCommand
from django.utils import timezone
from library.models import Loan

class Command(BaseCommand):
    help = 'Обновляет статус всех просроченных выдач и создаёт/обновляет штрафы'

    def handle(self, *args, **options):
        today = timezone.now().date()
        overdue_loans = Loan.objects.filter(
            due_date__lt=today,
            status='active'
        )
        
        updated_count = 0
        for loan in overdue_loans:
            loan.status = 'overdue'
            loan.save()  # ← вызывает создание/обновление штрафа и проверку статуса читателя
            updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Обновлено {updated_count} просроченных выдач')
        )