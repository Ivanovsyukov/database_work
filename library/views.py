from datetime import date
from django.db.models import Count, Q, Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout

from rest_framework import viewsets
from .models import (
    Author, Publisher, Book, BookAuthor, BookCopy,
    Member, Staff, Loan, Fine, Reservation
)
from .serializers import (
    AuthorSerializer, PublisherSerializer, BookSerializer, BookAuthorSerializer,
    BookCopySerializer, MemberSerializer, StaffSerializer,
    LoanSerializer, FineSerializer, ReservationSerializer
)


# ---------------------------- Аутентификация ----------------------------

@api_view(["POST"])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(request, username=username, password=password)

    if not user:
        return Response({"error": "Invalid credentials"}, status=400)

    login(request, user)
    return Response({"status": "ok", "message": "Logged in"})


@api_view(["POST"])
def logout_view(request):
    logout(request)
    return Response({"status": "ok", "message": "Logged out"})


# ----- Simple CRUD ViewSets -----

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class PublisherViewSet(viewsets.ModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    # GET /books?author=&genre=&year=
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        author = request.query_params.get("author")
        genre = request.query_params.get("genre")
        year = request.query_params.get("year")

        if author:
            queryset = queryset.filter(authors__id=author)
        if genre:
            queryset = queryset.filter(genre__icontains=genre)
        if year:
            queryset = queryset.filter(year=year)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BookAuthorViewSet(viewsets.ModelViewSet):
    queryset = BookAuthor.objects.all()
    serializer_class = BookAuthorSerializer


class BookCopyViewSet(viewsets.ModelViewSet):
    queryset = BookCopy.objects.all()
    serializer_class = BookCopySerializer


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer


# ----- Business Logic ViewSets -----

class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer

    # POST /loans — выдача книги
    def create(self, request, *args, **kwargs):
        copy_id = request.data.get("copy")
        member_id = request.data.get("member")

        # копия должна быть свободной
        if Loan.objects.filter(copy_id=copy_id, return_date__isnull=True).exists():
            return Response(
                {"error": "Копия книги уже выдана"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().create(request, *args, **kwargs)

    # PUT /loans/{id}/return
    @action(detail=True, methods=["put"])
    def return_book(self, request, pk=None):
        loan = self.get_object()

        if loan.return_date:
            return Response({"error": "Книга уже возвращена"}, status=400)

        loan.return_date = date.today()
        loan.save()

        return Response({"message": "Книга возвращена"})

    # GET /loans/active
    @action(detail=False, methods=["get"])
    def active(self, request):
        loans = Loan.objects.filter(return_date__isnull=True)
        return Response(self.get_serializer(loans, many=True).data)

    # GET /loans/overdue
    @action(detail=False, methods=["get"])
    def overdue(self, request):
        today = date.today()
        overdue = Loan.objects.filter(return_date__isnull=True, due_date__lt=today)
        return Response(self.get_serializer(overdue, many=True).data)


class FineViewSet(viewsets.ModelViewSet):
    queryset = Fine.objects.all()
    serializer_class = FineSerializer

    # GET /fines/member/{id}
    @action(detail=False, methods=["get"], url_path="member/(?P<member_id>[^/.]+)")
    def by_member(self, request, member_id=None):
        fines = Fine.objects.filter(member_id=member_id)
        return Response(self.get_serializer(fines, many=True).data)

    # PUT /fines/{id}/pay
    @action(detail=True, methods=["put"])
    def pay(self, request, pk=None):
        fine = self.get_object()
        fine.paid = True
        fine.save()
        return Response({"message": "Штраф оплачен"})


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    # GET /reservations/active
    @action(detail=False, methods=["get"])
    def active(self, request):
        reservations = Reservation.objects.filter(active=True)
        return Response(self.get_serializer(reservations, many=True).data)

    # PUT /reservations/{id}/cancel
    @action(detail=True, methods=["put"])
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        reservation.active = False
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

        return Response(data, status=200)


class MemberActivityReport(APIView):
    def get(self, request):
        data = (
            Member.objects
            .annotate(loans_count=Count("loans"))
            .order_by("-loans_count")[:10]
            .values("id", "first_name", "last_name", "loans_count")
        )
        return Response(list(data))


class FinesSummaryReport(APIView):
    def get(self, request):
        total_sum = Fine.objects.aggregate(total=Sum("fine_amount"))["total"] or 0

        paid = Fine.objects.filter(status="paid").count()
        unpaid = Fine.objects.filter(status="pending").count()

        return Response({
            "total_fines": total_sum,
            "paid_count": paid,
            "unpaid_count": unpaid,
        })
