# Импорты для работы с датами, проверками и базой данных
from decimal import Decimal
from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator, EmailValidator
from django.db import models, transaction  # transaction — для группировки операций
from django.db.models import Q, Sum, F
from django.db.models.functions import ExtractYear, Now
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

# Вспомогательная функция: возвращает сегодняшнюю дату (с учётом временной зоны)
def get_today_date():
    return timezone.now().date()


# --- Константы: статусы и роли ---
# Используем кортежи (значение в БД, человекочитаемое название) — так Django и ожидает

BOOK_COPY_STATUSES = (
    ('available', 'Available'),
    ('borrowed', 'Borrowed'),
    ('under maintenance', 'Under maintenance'),
    ('lost', 'Lost'),
)

MEMBER_STATUS = (
    ('active', 'Active'),
    ('suspended', 'Suspended'),
    ('expired', 'Expired'),
)

LOAN_STATUS = (
    ('active', 'Active'),
    ('returned', 'Returned'),
    ('overdue', 'Overdue'),
)

RESERVATION_STATUS = (
    ('active', 'Active'),
    ('fulfilled', 'Fulfilled'),
    ('cancelled', 'Cancelled'),
)

STAFF_ROLES = (
    ('librarian', 'Librarian'),
    ('admin', 'Admin'),
)


# --- Валидаторы полей ---
# Чтобы не дублировать код, вынесли общие проверки сюда

no_digits_validator = RegexValidator(
    regex=r'^\D+$',  # только не-цифры
    message='Field cannot contain digits.'
)
not_empty_validator = RegexValidator(
    regex=r'.+',  # хотя бы один символ
    message='Field cannot be empty.'
)
isbn_validator = RegexValidator(
    regex=r'^\d{13}$',  # ровно 13 цифр
    message='ISBN must be exactly 13 digits.'
)


# --- Модели данных ---

class Author(models.Model):
    """Автор книги"""
    first_name = models.CharField(max_length=50, validators=[no_digits_validator])
    last_name = models.CharField(max_length=50, validators=[no_digits_validator])
    birth_date = models.DateField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "authors"  # название таблицы в БД
        # Проверки на уровне БД
        constraints = [
            models.CheckConstraint(condition=~models.Q(first_name=''), name='author_first_name_not_empty'),
            models.CheckConstraint(condition=~models.Q(last_name=''), name='author_last_name_not_empty'),
            models.CheckConstraint(condition=~models.Q(first_name__regex=r'[0-9]'), name='author_first_name_no_digits'),
            models.CheckConstraint(condition=~models.Q(last_name__regex=r'[0-9]'), name='author_last_name_no_digits'),
            models.CheckConstraint(
                condition=(Q(birth_date__gt=date(1500, 1, 1)) | Q(birth_date__isnull=True)),
                name='author_birth_date_valid'
            ),
        ]
        ordering = ['last_name', 'first_name']  # сортировка по умолчанию

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Publisher(models.Model):
    """Издательство"""
    name = models.CharField(max_length=100, unique=True, validators=[not_empty_validator])
    address = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "publishers"
        constraints = [
            models.CheckConstraint(condition=~models.Q(name=''), name='publisher_name_not_empty'),
        ]

    def __str__(self):
        return self.name


class Book(models.Model):
    """Книга"""
    title = models.CharField(max_length=255, validators=[not_empty_validator])
    isbn = models.CharField(max_length=13, unique=True, validators=[isbn_validator])
    publication_year = models.IntegerField()
    genre = models.CharField(max_length=50, null=True, blank=True)
    publisher = models.ForeignKey(Publisher, on_delete=models.RESTRICT, related_name='books')
    authors = models.ManyToManyField(Author, through='BookAuthor', related_name='books')

    class Meta:
        db_table = "books"
        constraints = [
            models.CheckConstraint(condition=~models.Q(title=''), name='book_title_not_empty'),
            models.CheckConstraint(condition=Q(publication_year__gte=1450), name='book_publication_year_min'),
            models.CheckConstraint(
                condition=Q(publication_year__lte=ExtractYear(Now())),
                name='book_publication_year_max_current',
            ),
            models.CheckConstraint(condition=Q(isbn__regex=r'^[0-9]{13}$'), name='book_isbn_13_digits'),
        ]
        ordering = ['title']

    def clean(self):
        # Дополнительная проверка в Python: год не может быть в будущем
        current_year = timezone.now().year
        if self.publication_year is not None and self.publication_year > current_year:
            raise ValidationError({'publication_year': f'Publication year cannot be in the future ({current_year}).'})

    def __str__(self):
        return f'{self.title} ({self.publication_year})'


class BookAuthor(models.Model):
    """Промежуточная модель для связи многие-ко-многим между Book и Author"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    class Meta:
        db_table = "book_authors"
        unique_together = ('book', 'author')  # одна пара — одна запись

    def __str__(self):
        return f'{self.book} — {self.author}'


class BookCopy(models.Model):
    """Физическая копия книги (с штрихкодом и статусом)"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies')
    barcode = models.CharField(max_length=20, unique=True, validators=[not_empty_validator])
    acquisition_date = models.DateField(default=get_today_date)  # дата поступления в фонд
    status = models.CharField(max_length=20, choices=BOOK_COPY_STATUSES, default='available')

    class Meta:
        db_table = "book_copies"
        constraints = [
            models.CheckConstraint(condition=~models.Q(barcode=''), name='copy_barcode_not_empty'),
            models.CheckConstraint(condition=Q(status__in=[s[0] for s in BOOK_COPY_STATUSES]), name='copy_status_valid'),
        ]

    def __str__(self):
        return f'Copy {self.barcode} of "{self.book.title}"'


class Member(models.Model):
    """Читатель библиотеки"""
    first_name = models.CharField(max_length=50, validators=[no_digits_validator])
    last_name = models.CharField(max_length=50, validators=[no_digits_validator])
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    membership_start_date = models.DateField(default=get_today_date)
    membership_status = models.CharField(max_length=20, choices=MEMBER_STATUS, default='active')

    class Meta:
        db_table = "members"
        constraints = [
            models.CheckConstraint(condition=~models.Q(first_name=''), name='member_first_name_not_empty'),
            models.CheckConstraint(condition=~models.Q(last_name=''), name='member_last_name_not_empty'),
            models.CheckConstraint(condition=~models.Q(first_name__regex=r'[0-9]'), name='member_first_name_no_digits'),
            models.CheckConstraint(condition=~models.Q(last_name__regex=r'[0-9]'), name='member_last_name_no_digits'),
            models.CheckConstraint(condition=Q(email__contains='@'), name='member_email_contains_at'),
            models.CheckConstraint(condition=Q(membership_status__in=[s[0] for s in MEMBER_STATUS]), name='member_status_valid'),
        ]
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    # Вспомогательные методы для работы с бизнес-логикой
    def active_loans_count(self):
        """Сколько активных выдач у читателя"""
        return self.loans.filter(status='active').count()

    def overdue_loans_count(self):
        """Сколько просроченных выдач"""
        return self.loans.filter(status='overdue').count()

    def unpaid_fines_total(self):
        """Сумма всех неоплаченных штрафов"""
        # Суммируем fine_amount из Fine, связанного с Loan этого Member
        total = Fine.objects.filter(
            loan__member=self,
            paid_date__isnull=True
        ).aggregate(total=Sum('fine_amount'))['total']
        return total or Decimal('0.00')


class Staff(models.Model):
    """Сотрудник библиотеки (библиотекарь или админ)"""
    first_name = models.CharField(max_length=50, validators=[no_digits_validator])
    last_name = models.CharField(max_length=50, validators=[no_digits_validator])
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    role = models.CharField(max_length=20, choices=STAFF_ROLES)

    class Meta:
        db_table = "staff"
        constraints = [
            models.CheckConstraint(condition=~models.Q(first_name=''), name='staff_first_name_not_empty'),
            models.CheckConstraint(condition=~models.Q(last_name=''), name='staff_last_name_not_empty'),
            models.CheckConstraint(condition=~models.Q(first_name__regex=r'[0-9]'), name='staff_first_name_no_digits'),
            models.CheckConstraint(condition=~models.Q(last_name__regex=r'[0-9]'), name='staff_last_name_no_digits'),
            models.CheckConstraint(condition=Q(email__contains='@'), name='staff_email_contains_at'),
            models.CheckConstraint(condition=Q(role__in=[r[0] for r in STAFF_ROLES]), name='staff_role_valid'),
        ]
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.role})'


class Loan(models.Model):
    """Операция выдачи книги читателю"""
    copy = models.ForeignKey(BookCopy, on_delete=models.RESTRICT, related_name='loans')
    member = models.ForeignKey(Member, on_delete=models.RESTRICT, related_name='loans')
    loan_date = models.DateField(default=get_today_date)
    due_date = models.DateField()  # когда надо вернуть
    return_date = models.DateField(null=True, blank=True)  # когда реально вернули
    status = models.CharField(max_length=20, choices=LOAN_STATUS, default='active')

    class Meta:
        db_table = "loans"
        constraints = [
            models.CheckConstraint(condition=Q(due_date__gt=F('loan_date')), name='loan_due_after_loan'),
            models.CheckConstraint(
                condition=Q(return_date__isnull=True) | Q(return_date__gte=F('loan_date')),
                name='loan_return_date_valid',
            ),
            models.CheckConstraint(condition=Q(status__in=[s[0] for s in LOAN_STATUS]), name='loan_status_valid'),
        ]
        ordering = ['-loan_date']

    def clean(self):
        """Проверки при создании/изменении выдачи"""
        errors = {}

        if self.due_date and self.loan_date and self.due_date <= self.loan_date:
            errors['due_date'] = 'Due date must be after loan date.'

        if self.return_date and self.return_date < self.loan_date:
            errors['return_date'] = 'Return date cannot be before loan date.'

        # При создании новой активной выдачи:
        if not self.pk and self.status == 'active':
            if self.copy.status != 'available':
                errors['copy'] = 'Cannot loan a copy that is not available.'
            if self.member.membership_status != 'active':
                errors['member'] = 'Member is not active and cannot borrow books.'
            if self.member.active_loans_count() >= 5:
                errors['member'] = f'Member already has {self.member.active_loans_count()} active loans (limit 5).'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Сохранение с учётом бизнес-правил"""
        self.full_clean()

        # Если выдача активна и просрочена — меняем статус на 'overdue'
        if self.pk and self.status == 'active' and self.due_date and self.due_date < timezone.now().date():
            self.status = 'overdue'

        with transaction.atomic():  # Гарантируем, что всё пройдёт или ничего
            super().save(*args, **kwargs)

            # Синхронизируем статус копии книги
            if self.status in {'active', 'overdue'}:
                if self.copy.status != 'borrowed':
                    self.copy.status = 'borrowed'
                    self.copy.save(update_fields=['status'])
            elif self.status == 'returned':
                if self.copy.status != 'available':
                    self.copy.status = 'available'
                    self.copy.save(update_fields=['status'])
                    notify_first_reservation(self.copy)
                if not self.return_date:
                    self.return_date = timezone.now().date()
                    super().save(update_fields=['return_date'])

            # При переходе в 'overdue' — создаём штраф
            if self.status == 'overdue':
                days_overdue = (timezone.now().date() - self.due_date).days
                amount = Decimal(max(days_overdue, 0)) * Decimal('10.00')
                
                # Получаем ИЛИ создаём штраф
                fine, created = Fine.objects.get_or_create(
                    loan=self,
                    defaults={'fine_amount': amount},
                )
                # Если штраф уже существовал и не оплачен - обновляем сумму
                if not created and fine.paid_date is None and fine.fine_amount != amount:
                    fine.fine_amount = amount
                    fine.save(update_fields=['fine_amount'])

        # После сохранения — проверяем и, возможно, блокируем читателя
        update_member_membership_status(self.member)

        if self.status == 'active':
            Reservation.objects.filter(
                book=self.copy.book,
                member=self.member,
                status='active'
            ).update(status='fulfilled')

    def __str__(self):
        return f'Loan #{self.pk}: {self.copy} to {self.member}'


class Fine(models.Model):
    """Штраф за просрочку"""
    loan = models.OneToOneField(Loan, on_delete=models.CASCADE, related_name='fine')
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    issue_date = models.DateField(default=get_today_date)
    paid_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "fines"
        constraints = [
            models.CheckConstraint(condition=Q(fine_amount__gte=0), name='fine_amount_non_negative'),
        ]
        ordering = ['-issue_date']
    
    def is_paid(self):
        """Вспомогательный метод: оплачен ли штраф?"""
        return self.paid_date is not None

    def pay(self, paid_date=None):
        """Оплата штрафа - выставляет paid_date и обновляет статус читателя"""
        with transaction.atomic():
            if self.paid_date is not None:
                return
            self.paid_date = paid_date or timezone.now().date()
            self.save(update_fields=['paid_date'])
            update_member_membership_status(self.loan.member)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        update_member_membership_status(self.loan.member)  # при любом изменении — проверяем статус

    def __str__(self):
        return f'Fine #{self.pk} for {self.loan.member} — {self.fine_amount}'


class Reservation(models.Model):
    """Бронирование книги"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='reservations')
    reservation_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateField()  # когда бронь "сгорает"
    status = models.CharField(max_length=20, choices=RESERVATION_STATUS, default='active')

    class Meta:
        db_table = "reservations"
        constraints = [
            models.CheckConstraint(condition=Q(status__in=[s[0] for s in RESERVATION_STATUS]), name='reservation_status_valid'),
        ]
        ordering = ['-reservation_date']

    def clean(self):
        errors = {}
        if self.expiry_date and self.reservation_date and self.expiry_date <= self.reservation_date.date():
            errors['expiry_date'] = 'Expiry date must be after reservation date.'

        # Нельзя бронировать одну и ту же книгу дважды
        if self.status == 'active':
            qs = Reservation.objects.filter(book=self.book, member=self.member, status='active')
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                errors['member'] = 'An active reservation for this book by this member already exists.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Reservation #{self.pk} — {self.book.title} by {self.member}'


# ----------------------------
# Вспомогательные функции
# ----------------------------

def update_member_membership_status(member: Member):
    """
    Автоматически обновляет статус читателя:
    - Блокирует, если штрафов > 100 руб или просроченных книг > 3.
    - Разблокирует, если всё в порядке и статус был 'suspended' (но не 'expired').
    """
    unpaid_total = member.unpaid_fines_total()
    overdue_count = member.overdue_loans_count()

    new_status = member.membership_status

    if unpaid_total > Decimal('100.00') or overdue_count > 3:
        new_status = 'suspended'
    elif member.membership_status == 'suspended':
        # Если причины блокировки исчезли — восстанавливаем
        new_status = 'active'

    if new_status != member.membership_status:
        member.membership_status = new_status
        member.save(update_fields=['membership_status'])

def notify_first_reservation(book_copy):
    """Отправляет email первому в очереди бронировании для book_copy.book"""
    reservation = Reservation.objects.filter(
        book=book_copy.book,
        status='active'
    ).order_by('reservation_date').first()

    if reservation:
        try:
            send_mail(
                subject='Ваша бронь готова!',
                message=f'Книга "{book_copy.book.title}" доступна для выдачи.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[reservation.member.email],
            )
        except Exception as e:
            print(f"Ошибка email: {e}")
