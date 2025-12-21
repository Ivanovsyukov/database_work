from datetime import date, timedelta
from django.db.models import Count, Q, Sum
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout

from .models import (
    Author, Publisher, Book, BookAuthor, BookCopy,
    Member, Staff, Loan, Fine, Reservation, update_member_membership_status,
    recalculate_fines_for_reports
)
from .serializers import (
    AuthorSerializer, PublisherSerializer, BookSerializer, BookAuthorSerializer,
    BookCopySerializer, MemberSerializer, StaffSerializer,
    LoanSerializer, FineSerializer, ReservationSerializer
)


# ---------------------------- Аутентификация ----------------------------

@api_view(["POST"])
def login_view(request):
    email = (request.data.get("email") or "").strip()
    if not email:
        return Response({"error": "Email обязателен"}, status=400)
    try:
        staff = Staff.objects.get(email__iexact=email)
        # Сохраняем ID сотрудника в сессии
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
    request.session.flush() 
    return Response({"status": "ok"})


# ----- Simple CRUD ViewSets -----

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class PublisherViewSet(viewsets.ModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer

    def get_queryset(self):
        queryset = Publisher.objects.all()
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def list(self, request, *args, **kwargs):
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
    queryset = BookAuthor.objects.all()
    serializer_class = BookAuthorSerializer


class BookCopyViewSet(viewsets.ModelViewSet):
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
    queryset = Member.objects.all()
    serializer_class = MemberSerializer


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer


# ----- Business Logic ViewSets -----

def get_current_staff(request):
    staff_id = request.session.get('staff_id')
    if staff_id:
        return Staff.objects.filter(id=staff_id).first()
    return None

class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer

    def create(self, request, *args, **kwargs):
        staff = get_current_staff(request)
        if not staff:
            return Response({"error": "Требуется вход"}, status=401)
        copy_id = request.data.get("copy")
        member_id = request.data.get("member")

        try:
            copy = BookCopy.objects.get(id=copy_id)
            member = Member.objects.get(id=member_id)
        except (BookCopy.DoesNotExist, Member.DoesNotExist):
            return Response({"error": "Invalid copy or member ID"}, status=400)

        if copy.status != 'available':
            return Response({"error": "Книга недоступна для выдачи"}, status=400)

        if member.membership_status != 'active':
            return Response({"error": "Читатель неактивен"}, status=400)

        if member.active_loans_count() >= 5:
            return Response({"error": "Превышен лимит активных выдач (макс. 5)"}, status=400)

        # Создаём выдачу — статус по умолчанию 'active'
        loan = Loan.objects.create(
            copy=copy,
            member=member,
            loan_date=date.today(),
            due_date=date.today() + timedelta(days=14)  # или брать из настроек
        )

        serializer = self.get_serializer(loan)
        return Response(serializer.data, status=201)

    @action(detail=True, methods=["put"], url_path="return")
    def return_book(self, request, pk=None):
        loan = self.get_object()
        if loan.status == 'returned':
            return Response({"error": "Книга уже возвращена"}, status=400)

        loan.status = 'returned'
        loan.return_date = date.today()
        loan.save()  # вызовет update copy.status + member status

        return Response({"message": "Книга возвращена"})

    @action(detail=False, methods=["get"])
    def active(self, request):
        loans = Loan.objects.filter(status='active')
        return Response(self.get_serializer(loans, many=True).data)

    @action(detail=False, methods=["get"])
    def overdue(self, request):
        loans = Loan.objects.filter(status='overdue')
        return Response(self.get_serializer(loans, many=True).data)

class FineViewSet(viewsets.ModelViewSet):
    queryset = Fine.objects.all()
    serializer_class = FineSerializer

    @action(detail=False, methods=["get"], url_path="member/(?P<member_id>[^/.]+)")
    def by_member(self, request, member_id=None):
        fines = Fine.objects.filter(member_id=member_id)
        return Response(self.get_serializer(fines, many=True).data)

    @action(detail=True, methods=["put"])
    def pay(self, request, pk=None):
        fine = self.get_object()
        if fine.status == 'paid':
            return Response({"error": "Штраф уже оплачен"}, status=400)

        fine.pay()  # <-- вызываем метод из модели (он обновит статус читателя)
        return Response({"message": "Штраф оплачен"})


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    @action(detail=False, methods=["get"])
    def active(self, request):
        reservations = Reservation.objects.filter(status='active')
        return Response(self.get_serializer(reservations, many=True).data)

    @action(detail=True, methods=["put"])
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        if reservation.status != 'active':
            return Response({"error": "Бронирование уже отменено или выполнено"}, status=400)

        reservation.status = 'cancelled'
        reservation.save()
        return Response({"message": "Бронирование отменено"})


# ---------------------------- Отчёты ----------------------------

class PopularBooksReport(APIView):
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
    def get(self, request):
        recalculate_fines_for_reports()
        total_sum = Fine.objects.aggregate(total=Sum("fine_amount"))["total"] or 0
        paid_sum = Fine.objects.filter(status="paid").aggregate(total=Sum("fine_amount"))["total"] or 0
        unpaid_count = Fine.objects.filter(status="pending").count()

        return Response({
            "total_fines": float(total_sum),
            "paid_fines": float(paid_sum),
            "unpaid_count": unpaid_count,
            "unpaid_total": float(total_sum - paid_sum),
        })
