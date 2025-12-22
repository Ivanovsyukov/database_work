from django.core.management.base import BaseCommand
from django.utils import timezone
from library.models import Loan, Reservation

class Command(BaseCommand):
    help = 'Обновляет просроченные выдачи и отменяет просроченные брони'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # 1. Обновляем выдачи
        overdue_loans = Loan.objects.filter(due_date__lt=today, status='active')
        for loan in overdue_loans:
            loan.status = 'overdue'
            loan.save()  # ← создаёт штрафы, обновляет статусы
        
        # 2. Отменяем брони
        expired_reservations = Reservation.objects.filter(
            expiry_date__lt=today,
            status='active'
        )
        count_reservations = expired_reservations.count()
        expired_reservations.update(status='cancelled')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Обновлено {overdue_loans.count()} выдач, '
                f'отменено {count_reservations} бронирований'
            )
        )
        