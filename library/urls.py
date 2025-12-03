from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    AuthorViewSet, PublisherViewSet, BookViewSet, BookAuthorViewSet,
    BookCopyViewSet, MemberViewSet, StaffViewSet,
    LoanViewSet, FineViewSet, ReservationViewSet, login_view, logout_view,
    PopularBooksReport, MemberActivityReport, FinesSummaryReport
)

router = DefaultRouter()
router.register(r'authors', AuthorViewSet)
router.register(r'publishers', PublisherViewSet)
router.register(r'books', BookViewSet)
router.register(r'book-authors', BookAuthorViewSet)
router.register(r'copies', BookCopyViewSet)
router.register(r'members', MemberViewSet)
router.register(r'staff', StaffViewSet)
router.register(r'loans', LoanViewSet)
router.register(r'fines', FineViewSet)
router.register(r'reservations', ReservationViewSet)

urlpatterns = [
    # Аутентификация
    path("auth/login", login_view),
    path("auth/logout", logout_view),

    # Отчёты
    path("reports/popular-books", PopularBooksReport.as_view()),
    path("reports/member-activity", MemberActivityReport.as_view()),
    path("reports/fines-summary", FinesSummaryReport.as_view()),

    # Все CRUD маршруты
    path("", include(router.urls)),
]
