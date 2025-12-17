from decimal import Decimal
from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator, EmailValidator
from django.db import models, transaction
from django.db.models import Q, Sum, F, Count
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone

def get_today_date():
    return timezone.now().date()

# --- Constants / Choices ---
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

FINE_STATUS = (
    ('pending', 'Pending'),
    ('paid', 'Paid'),
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

# --- Validators ---
no_digits_validator = RegexValidator(regex=r'^\D+$', message='Field cannot contain digits.')
not_empty_validator = RegexValidator(regex=r'.+', message='Field cannot be empty.')
isbn_validator = RegexValidator(regex=r'^\d{13}$', message='ISBN must be exactly 13 digits.')


# --- Models ---

class Author(models.Model):
    first_name = models.CharField(max_length=50, validators=[no_digits_validator])
    last_name = models.CharField(max_length=50, validators=[no_digits_validator])
    birth_date = models.DateField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "authors"
        constraints = [
            models.CheckConstraint(condition=~models.Q(first_name=''), name='author_first_name_not_empty'),
            models.CheckConstraint(condition=~models.Q(last_name=''), name='author_last_name_not_empty'),
            models.CheckConstraint(
                condition=(Q(birth_date__gt=date(1500, 1, 1)) | Q(birth_date__isnull=True)),
                name='author_birth_date_valid'
            ),
        ]
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Publisher(models.Model):
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
        ]
        ordering = ['title']

    def clean(self):
        # publication_year <= current year
        current_year = timezone.now().year
        if self.publication_year is not None and self.publication_year > current_year:
            raise ValidationError({'publication_year': f'Publication year cannot be in the future ({current_year}).'})

    def __str__(self):
        return f'{self.title} ({self.publication_year})'


class BookAuthor(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    class Meta:
        db_table = "book_authors"
        unique_together = ('book', 'author')
        # primary key is implicit (id), but unique_together enforces pair uniqueness
        verbose_name = 'Book-Author relation'
        verbose_name_plural = 'Book-Author relations'

    def __str__(self):
        return f'{self.book} — {self.author}'


class BookCopy(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies')
    barcode = models.CharField(max_length=20, unique=True, validators=[not_empty_validator])
    acquisition_date = models.DateField(default=get_today_date)
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
            models.CheckConstraint(condition=Q(membership_status__in=[s[0] for s in MEMBER_STATUS]), name='member_status_valid'),
        ]
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def active_loans_count(self):
        return self.loans.filter(status='active').count()

    def overdue_loans_count(self):
        return self.loans.filter(status='overdue').count()

    def unpaid_fines_total(self):
        res = self.fines.filter(status='pending').aggregate(total=Sum('fine_amount'))
        return res['total'] or Decimal('0.00')


class Staff(models.Model):
    first_name = models.CharField(max_length=50, validators=[no_digits_validator])
    last_name = models.CharField(max_length=50, validators=[no_digits_validator])
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    role = models.CharField(max_length=20, choices=STAFF_ROLES)

    class Meta:
        db_table = "staff"
        constraints = [
            models.CheckConstraint(condition=~models.Q(first_name=''), name='staff_first_name_not_empty'),
            models.CheckConstraint(condition=~models.Q(last_name=''), name='staff_last_name_not_empty'),
            models.CheckConstraint(condition=Q(role__in=[r[0] for r in STAFF_ROLES]), name='staff_role_valid'),
        ]
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.role})'


class Loan(models.Model):
    copy = models.ForeignKey(BookCopy, on_delete=models.RESTRICT, related_name='loans')
    member = models.ForeignKey(Member, on_delete=models.RESTRICT, related_name='loans')
    loan_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=LOAN_STATUS, default='active')

    class Meta:
        db_table = "loans"
        constraints = [
            models.CheckConstraint(condition=Q(due_date__gt=F('loan_date')), name='loan_due_after_loan'),
            models.CheckConstraint(condition=Q(status__in=[s[0] for s in LOAN_STATUS]), name='loan_status_valid'),
        ]
        ordering = ['-loan_date']

    def clean(self):
        errors = {}
        # due_date must be after loan_date
        if self.due_date and self.loan_date and self.due_date <= self.loan_date:
            errors['due_date'] = 'Due date must be after loan date.'

        # return_date must be None or >= loan_date
        if self.return_date and self.return_date < self.loan_date:
            errors['return_date'] = 'Return date cannot be before loan date.'

        # copy must be available when creating an active loan
        if not self.pk and self.status == 'active':
            if self.copy.status != 'available':
                errors['copy'] = 'Cannot loan a copy that is not available.'

            if self.member.membership_status != 'active':
                errors['member'] = 'Member is not active and cannot borrow books.'

            # active loans limit
            active_loans = self.member.loans.filter(status='active').count()
            if active_loans >= 5:
                errors['member'] = f'Member already has {active_loans} active loans (limit 5).'

        # prevent creating loan if copy is lost/under maintenance etc
        if self.copy and self.copy.status not in dict(BOOK_COPY_STATUSES).keys():
            errors['copy'] = 'Invalid copy status.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Ensure clean is called
        self.full_clean()
        creating = self._state.adding
        prev_status = None
        if not creating:
            try:
                prev = Loan.objects.get(pk=self.pk)
                prev_status = prev.status
            except Loan.DoesNotExist:
                prev_status = None

        with transaction.atomic():
            super().save(*args, **kwargs)  # save loan first

            # If loan is active -> mark copy as borrowed
            if self.status == 'active':
                if self.copy.status != 'borrowed':
                    self.copy.status = 'borrowed'
                    self.copy.save(update_fields=['status'])
            # If loan is returned -> free the copy
            if self.status == 'returned':
                if self.copy.status != 'available':
                    self.copy.status = 'available'
                    self.copy.save(update_fields=['status'])
                # ensure return_date set
                if not self.return_date:
                    self.return_date = timezone.now().date()
                    super().save(update_fields=['return_date'])

            # If loan is overdue and there is no fine -> create fine
            if self.status == 'overdue':
                # create fine only if not exists
                if not hasattr(self, 'fine'):
                    days_overdue = (timezone.now().date() - self.due_date).days
                    if days_overdue < 0:
                        days_overdue = 0
                    amount = Decimal(days_overdue) * Decimal('10.00')
                    Fine.objects.create(loan=self, member=self.member, fine_amount=amount, status='pending')

    def __str__(self):
        return f'Loan #{self.pk}: {self.copy} to {self.member}'


class Fine(models.Model):
    loan = models.OneToOneField(Loan, on_delete=models.CASCADE, related_name='fine')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='fines')
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    issue_date = models.DateField(default=timezone.now)
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=FINE_STATUS, default='pending')

    class Meta:
        db_table = "fines"
        constraints = [
            models.CheckConstraint(condition=Q(fine_amount__gte=0), name='fine_amount_non_negative'),
            models.CheckConstraint(condition=Q(status__in=[s[0] for s in FINE_STATUS]), name='fine_status_valid'),
        ]
        ordering = ['-issue_date']

    def pay(self, paid_date=None):
        """Mark fine as paid and update member status accordingly."""
        with transaction.atomic():
            if self.status == 'paid':
                return
            self.status = 'paid'
            self.paid_date = paid_date or timezone.now().date()
            self.save(update_fields=['status', 'paid_date'])
            update_member_membership_status(self.member)

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        # after creation / update, enforce membership status
        update_member_membership_status(self.member)

    def __str__(self):
        return f'Fine #{self.pk} for {self.member} — {self.fine_amount}'


class Reservation(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='reservations')
    reservation_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=RESERVATION_STATUS, default='active')

    class Meta:
        db_table = "reservations"
        constraints = [
            models.CheckConstraint(condition=Q(status__in=[s[0] for s in RESERVATION_STATUS]), name='reservation_status_valid'),
        ]
        ordering = ['-reservation_date']

    def clean(self):
        errors = {}
        # expiry_date > reservation_date.date()
        if self.expiry_date and self.reservation_date and self.expiry_date <= self.reservation_date.date():
            errors['expiry_date'] = 'Expiry date must be after reservation date.'

        # Prevent duplicate active reservation for same book & member
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
# Helper functions and signals
# ----------------------------

def update_member_membership_status(member: Member):
    """
    Apply automatic suspension/activation rules:
    - If unpaid fines total > 100 -> suspended
    - If overdue loans > 3 -> suspended
    - If no unpaid fines and overdue <= 3 and membership was suspended due to fines/overdue -> set active
    """
    unpaid_total = member.unpaid_fines_total()
    overdue_count = member.overdue_loans_count()

    # Determine new status
    new_status = member.membership_status
    if unpaid_total > Decimal('100.00') or overdue_count > 3:
        new_status = 'suspended'
    else:
        # if not expired, restore to active
        if member.membership_status == 'suspended':
            new_status = 'active'

    if new_status != member.membership_status:
        member.membership_status = new_status
        member.save(update_fields=['membership_status'])


@receiver(pre_save, sender=Loan)
def loan_pre_save(sender, instance: Loan, **kwargs):
    """
    Before saving a loan - auto-update status to overdue if due_date < today and still active.
    """
    if instance.pk is None:
        # new loan - nothing to auto-change yet
        return

    try:
        prev = Loan.objects.get(pk=instance.pk)
    except Loan.DoesNotExist:
        return

    # If previously active and due_date passed, mark overdue
    if instance.status == 'active':
        today = timezone.now().date()
        if instance.due_date < today:
            instance.status = 'overdue'


@receiver(post_save, sender=Loan)
def loan_post_save(sender, instance: Loan, created, **kwargs):
    """
    After saving a loan:
    - ensure book copy status aligns with loan
    - create fine when loan becomes overdue (if not exists)
    - update member status
    """
    # ensure copy status
    if instance.status == 'active' and instance.copy.status != 'borrowed':
        instance.copy.status = 'borrowed'
        instance.copy.save(update_fields=['status'])

    if instance.status == 'returned' and instance.copy.status != 'available':
        instance.copy.status = 'available'
        instance.copy.save(update_fields=['status'])

    # if overdue and fine not exists -> create fine
    if instance.status == 'overdue':
        if not hasattr(instance, 'fine'):
            days_overdue = (timezone.now().date() - instance.due_date).days
            if days_overdue < 0:
                days_overdue = 0
            amount = Decimal(days_overdue) * Decimal('10.00')
            Fine.objects.create(loan=instance, member=instance.member, fine_amount=amount, status='pending')

    # update member membership (suspend/restore)
    update_member_membership_status(instance.member)


@receiver(post_save, sender=Fine)
def fine_post_save(sender, instance: Fine, created, **kwargs):
    # Whenever a fine changes, update member status
    update_member_membership_status(instance.member)