from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    AuthorViewSet, PublisherViewSet, BookViewSet, BookAuthorViewSet,
    BookCopyViewSet, MemberViewSet, StaffViewSet,
    LoanViewSet, FineViewSet, ReservationViewSet,
    login_view, logout_view,
    PopularBooksReport, MemberActivityReport, FinesSummaryReport, prepare_fines
)

router = DefaultRouter(trailing_slash=False)

# Регистрируем ViewSet'ы — каждый автоматически получает маршруты вида:
#   GET /authors/         → список авторов
#   POST /authors/        → создание автора
#   GET /authors/{id}/    → детали автора
#   PUT /authors/{id}/    → полное обновление
#   PATCH /authors/{id}/  → частичное обновление
#   DELETE /authors/{id}/ → удаление
router.register(r'authors', AuthorViewSet)
router.register(r'publishers', PublisherViewSet)
router.register(r'books', BookViewSet)
router.register(r'book-authors', BookAuthorViewSet)
router.register(r'copies', BookCopyViewSet)        # физические копии книг
router.register(r'members', MemberViewSet)        # читатели
router.register(r'staff', StaffViewSet)           # сотрудники (библиотекари и админы)
router.register(r'loans', LoanViewSet)            # выдачи
router.register(r'fines', FineViewSet)            # штрафы
router.register(r'reservations', ReservationViewSet)  # бронирования


# Объединяем маршруты: сначала специальные (аутентификация и отчёты), потом CRUD
urlpatterns = [
    # -------------------------------------------------------------------------
    # АУТЕНТИФИКАЦИЯ СОТРУДНИКОВ
    # -------------------------------------------------------------------------
    # Используется сессионная аутентификация через request.session['staff_id']
    # (а не встроенная в DRF), поэтому реализована как простые функции.
    path("auth/login", login_view),
    path("auth/logout", logout_view),

    # -------------------------------------------------------------------------
    # ОТЧЁТЫ (аналитика для администратора)
    # -------------------------------------------------------------------------
    # Согласно ТЗ:
    # - popular-books: самые популярные книги, жанры, авторы
    # - member-activity: активность читателей, топ по просрочкам
    # - fines-summary: статистика по штрафам
    path("reports/popular-books", PopularBooksReport.as_view()),
    path("reports/member-activity", MemberActivityReport.as_view()),
    path("reports/fines-summary", FinesSummaryReport.as_view()),

    # -------------------------------------------------------------------------
    # СТАНДАРТНЫЕ CRUD-МАРШРУТЫ ДЛЯ ВСЕХ МОДЕЛЕЙ
    # -------------------------------------------------------------------------
    # Подключаем все маршруты, сгенерированные DefaultRouter
    path("", include(router.urls)),


    path('fines/prepare/', prepare_fines, name='prepare-fines'),
]