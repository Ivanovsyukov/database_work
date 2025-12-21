from datetime import date, timedelta
from django.db.models import Count, Q, Sum
from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction

from .models import (
    Author, Publisher, Book, BookAuthor, BookCopy,
    Member, Staff, Loan, Fine, Reservation
)
from .serializers import (
    AuthorSerializer, PublisherSerializer, BookSerializer, BookAuthorSerializer,
    BookCopySerializer, MemberSerializer, StaffSerializer,
    LoanSerializer, FineSerializer, ReservationSerializer
)

def update_overdue_fines():
    """Обновляет статусы и штрафы для всех просроченных выдач"""
    today = date.today()
    with transaction.atomic():
        overdue_loans = Loan.objects.filter(due_date__lt=today)
        for loan in overdue_loans:
            loan.save()

# ---------------------------- Аутентификация сотрудников ----------------------------

@api_view(["POST"])
def login_view(request):
    """
    Авторизация сотрудника библиотеки по email.
    
    Согласно ТЗ, доступ к API имеют только сотрудники (админы).
    Аутентификация сессионная: при успешном входе ID сотрудника сохраняется в сессии.
    Пароль не используется — предполагается, что вход осуществляется в защищённой
    внутренней сети или через отдельную систему учётных записей.
    """
    email = (request.data.get("email") or "").strip()
    if not email:
        return Response({"error": "Email обязателен"}, status=400)
    try:
        staff = Staff.objects.get(email__iexact=email)
        # Сохраняем ID сотрудника в сессии — основа кастомной аутентификации
        request.session['staff_id'] = staff.id
        return Response({
            "id": staff.id,
            "first_name": staff.first_name,
            "last_name": staff.last_name, 
            "email": staff.email,
            "role": staff.role,
        })
    except Staff.DoesNotExist:
        return Response({"error": "Сотрудник не найден"}, status=400)


@api_view(["POST"])
def logout_view(request):
    """
    Выход из системы: удаляет все данные сессии.
    """
    request.session.flush() 
    return Response({"status": "ok"})


# ----- Простые CRUD ViewSet'ы (без сложной логики) -----

class AuthorViewSet(viewsets.ModelViewSet):
    """CRUD для авторов."""
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    def get_queryset(self):
        queryset = Author.objects.all()
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(last_name__icontains=search) | Q(first_name__icontains=search)
            )
        return queryset


class PublisherViewSet(viewsets.ModelViewSet):
    """CRUD для издательств с возможностью фильтрации по названию."""
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer

    def get_queryset(self):
        queryset = Publisher.objects.all()
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class BookViewSet(viewsets.ModelViewSet):
    """CRUD для книг с фильтрацией по автору, жанру, году и названию."""
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def list(self, request, *args, **kwargs):
        """
        Поддержка фильтрации:
          - ?author=ID — книги конкретного автора
          - ?genre=... — по жанру (частичное совпадение)
          - ?year=2020 — по году публикации
          - ?title=... — по названию (частичное совпадение)
        """
        queryset = self.get_queryset()

        author = request.query_params.get("author")
        genre = request.query_params.get("genre")
        year = request.query_params.get("year")
        title = request.query_params.get("title")

        if title:
            queryset = queryset.filter(title__icontains=title)
        if author:
            queryset = queryset.filter(authors__id=author)
        if genre:
            queryset = queryset.filter(genre__icontains=genre)
        if year and year.isdigit():
            queryset = queryset.filter(publication_year=int(year))

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BookAuthorViewSet(viewsets.ModelViewSet):
    """CRUD для промежуточной модели связи многие-ко-многим (книга ↔ автор)."""
    queryset = BookAuthor.objects.all()
    serializer_class = BookAuthorSerializer


class BookCopyViewSet(viewsets.ModelViewSet):
    """CRUD для физических копий книг с фильтрацией по статусу и ID книги."""
    queryset = BookCopy.objects.all()
    serializer_class = BookCopySerializer

    def get_queryset(self):
        queryset = BookCopy.objects.all()
        book_id = self.request.query_params.get('book_id')
        status = self.request.query_params.get('status')
        if book_id:
            queryset = queryset.filter(book_id=book_id)
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class MemberViewSet(viewsets.ModelViewSet):
    """CRUD для читателей."""
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

    def get_queryset(self):
        queryset = Member.objects.all()
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(last_name__icontains=search) | Q(first_name__icontains=search)
            )
        return queryset


class StaffViewSet(viewsets.ModelViewSet):
    """CRUD для сотрудников """
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer


# ---------------------------- Вспомогательные функции ----------------------------

def get_current_staff(request):
    """
    Получает объект Staff по ID из сессии.
    Используется для проверки авторизации в бизнес-логике.
    """
    staff_id = request.session.get('staff_id')
    if staff_id:
        return Staff.objects.filter(id=staff_id).first()
    return None


# ----- Бизнес-логика: Выдачи (Loans) -----

class LoanViewSet(viewsets.ModelViewSet):
    """Управление выдачами книг с валидацией правил из ТЗ."""
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer

    def create(self, request, *args, **kwargs):
        """
        Создание новой выдачи.
        Проверки:
          - Только авторизованный сотрудник может оформить выдачу.
          - Книга должна быть в статусе 'available'.
          - Читатель должен быть 'active'.
          - Лимит: не более 5 активных выдач на одного читателя.
        Срок возврата — 14 дней по умолчанию.
        """
        staff = get_current_staff(request)
        if not staff:
            return Response({"error": "Требуется вход"}, status=401)

        copy_id = request.data.get("copy")
        member_id = request.data.get("member")

        try:
            copy = BookCopy.objects.get(id=copy_id)
            member = Member.objects.get(id=member_id)
        except (BookCopy.DoesNotExist, Member.DoesNotExist):
            return Response({"error": "Неверный ID копии или читателя"}, status=400)

        if copy.status != 'available':
            return Response({"error": "Книга недоступна для выдачи"}, status=400)

        if member.membership_status != 'active':
            return Response({"error": "Читатель неактивен"}, status=400)

        if member.active_loans_count() >= 5:
            return Response({"error": "Превышен лимит активных выдач (макс. 5)"}, status=400)

        # Создаём выдачу с автоматическим расчётом срока (14 дней)
        due_date_for_input = request.data.get("due_date")
        if due_date_for_input:
            due_date_for_input = date.fromisoformat(due_date_for_input)
        else:
            due_date_for_input = date.today() + timedelta(days=14)
        loan = Loan.objects.create(
            copy=copy,
            member=member,
            loan_date=date.today(),
            due_date=due_date_for_input
        )

        serializer = self.get_serializer(loan)
        return Response(serializer.data, status=201)

    @action(detail=True, methods=["put"], url_path="return")
    def return_book(self, request, pk=None):
        """
        Возврат книги: переводит статус выдачи в 'returned',
        обновляет статус копии и читателя (возможно, снятие блокировки).
        """
        loan = self.get_object()
        if loan.status == 'returned':
            return Response({"error": "Книга уже возвращена"}, status=400)

        loan.status = 'returned'
        loan.return_date = date.today()
        loan.save()  # Триггерит логику в модели: обновление статусов и штрафов

        return Response({"message": "Книга возвращена"})

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Список активных выдач (статус 'active')."""
        loans = Loan.objects.filter(status='active')
        return Response(self.get_serializer(loans, many=True).data)

    @action(detail=False, methods=["get"])
    def overdue(self, request):
        """Список просроченных выдач (статус 'overdue')."""
        loans = Loan.objects.filter(status='overdue')
        return Response(self.get_serializer(loans, many=True).data)


# ----- Бизнес-логика: Штрафы (Fines) -----

class FineViewSet(viewsets.ModelViewSet):
    """Управление штрафами за просрочку."""
    queryset = Fine.objects.all()
    serializer_class = FineSerializer

    @action(detail=False, methods=["get"], url_path="member/(?P<member_id>[^/.]+)")
    def by_member(self, request, member_id=None):
        """Получение всех штрафов конкретного читателя."""
        fines = Fine.objects.filter(loan__member_id=member_id)
        return Response(self.get_serializer(fines, many=True).data)

    @action(detail=True, methods=["put"])
    def pay(self, request, pk=None):
        """
        Оплата штрафа.
        Вызывает метод `pay()` из модели, который:
          - переводит статус в 'paid',
          - обновляет статус читателя (возможно, восстанавливает 'active').
        """
        fine = self.get_object()
        if fine.status == 'paid':
            return Response({"error": "Штраф уже оплачен"}, status=400)

        fine.pay()
        return Response({"message": "Штраф оплачен"})


# ----- Бизнес-логика: Бронирования (Reservations) -----

class ReservationViewSet(viewsets.ModelViewSet):
    """Управление бронированием книг."""
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Список активных бронирований."""
        reservations = Reservation.objects.filter(status='active')
        return Response(self.get_serializer(reservations, many=True).data)

    @action(detail=True, methods=["put"])
    def cancel(self, request, pk=None):
        """Отмена бронирования (только если статус 'active')."""
        reservation = self.get_object()
        if reservation.status != 'active':
            return Response({"error": "Бронирование уже отменено или выполнено"}, status=400)

        reservation.status = 'cancelled'
        reservation.save()
        return Response({"message": "Бронирование отменено"})


# ---------------------------- Отчёты (аналитика) ----------------------------

class PopularBooksReport(APIView):
    """
    Отчёт: самые популярные книги (по количеству выдач).
    Используется для анализа спроса — согласно ТЗ.
    """
    def get(self, request):
        books = (
            Book.objects
            .annotate(num_loans=Count("copies__loans"))
            .order_by("-num_loans")[:10]
        )
        data = [
            {
                "id": b.id,
                "title": b.title,
                "isbn": b.isbn,
                "num_loans": b.num_loans,
            }
            for b in books
        ]
        return Response(data)


class MemberActivityReport(APIView):
    """
    Отчёт: активность читателей.
    Включает:
      - общее число выдач,
      - число просрочек.
    Помогает выявлять активных читателей и нарушителей.
    """
    def get(self, request):
        members = (
            Member.objects
            .annotate(
                loans_count=Count("loans"),
                overdue_count=Count("loans", filter=Q(loans__status='overdue'))
            )
            .order_by("-loans_count")[:10]
        )
        data = [
            {
                "id": m.id,
                "first_name": m.first_name,
                "last_name": m.last_name,
                "loans_count": m.loans_count,
                "overdue_count": m.overdue_count,
            }
            for m in members
        ]
        return Response(data)


class FinesSummaryReport(APIView):
    """
    Сводка по штрафам:
      - общая сумма начисленных штрафов,
      - сумма оплаченных,
      - количество и сумма непогашенных.
    Используется администратором для финансового контроля.
    """
    def get(self, request):
        # ШАГ 1: Обновляем ВСЕ выдачи, у которых срок истёк
        update_overdue_fines()

        # ШАГ 2: Теперь считаем сумму — данные актуальны
        total_sum = Fine.objects.aggregate(total=Sum("fine_amount"))["total"] or 0
        paid_sum = Fine.objects.filter(paid_date__isnull=False).aggregate(total=Sum("fine_amount"))["total"] or 0
        unpaid_count = Fine.objects.filter(paid_date__isnull=True).count()

        return Response({
            "total_fines": float(total_sum),
            "paid_fines": float(paid_sum),
            "unpaid_count": unpaid_count,
            "unpaid_total": float(total_sum - paid_sum),
        })

@api_view(['POST'])
def prepare_fines(request):
    """Endpoint для подготовки штрафов (используется на странице FineManagement)"""
    update_overdue_fines()
    return Response({"status": "fines_updated"})