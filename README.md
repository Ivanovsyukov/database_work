# Техническое задание

### Наименование
**"База данных системы управления библиотечным фондом для учета книг, читателей, выдачи литературы и управления библиотечными процессами"**

### Предметная область
База данных системы управления библиотечным фондом - это комплексная система для автоматизации работы библиотеки. Она обеспечивает учет книжного фонда, регистрацию читателей, оформление выдачи и возврата книг, управление бронированиями и начисление штрафов.

Основные цели системы:
- Учет библиотечного инвентаря (книги, авторы, издательства, физические копии)
- Регистрация и управление читателями (членами библиотеки)
- Оформление выдачи и возврата книг с контролем сроков
- Управление бронированием книг
- Автоматическое начисление и учет штрафов за просрочку возврата
- Учет сотрудников библиотеки и разграничение их прав доступа
- Генерация отчетов по активности читателей и популярности книг

## Данные
### Для каждого элемента данных - ограничения

### Таблица authors
- id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL
- first_name: VARCHAR(50), NOT NULL, CHECK(first_name <> '' AND first_name !~ '\d') - имя не пустое и без цифр
- last_name: VARCHAR(50), NOT NULL, CHECK(last_name <> '' AND last_name !~ '\d') - фамилия не пустая и без цифр
- birth_date: DATE, NULL, CHECK(birth_date > '1500-01-01') - дата рождения не ранее 1500 года
- bio: TEXT, NULL

### Таблица publishers
- id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL
- name: VARCHAR(100), NOT NULL, UNIQUE, CHECK(name <> '') - название не пустое
- address: TEXT, NULL

### Таблица books
- id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL
- title: VARCHAR(255), NOT NULL, CHECK(title <> '') - название не пустое
- isbn: VARCHAR(13), UNIQUE, CHECK(LENGTH(isbn) = 13) - ISBN строго 13 символов
- publication_year: INTEGER, NOT NULL, CHECK(publication_year >= 1450 AND publication_year <= EXTRACT(YEAR FROM CURRENT_DATE))
- genre: VARCHAR(50), NULL
- publisher_id: INTEGER, NOT NULL, FOREIGN KEY -> publishers(id), ON DELETE RESTRICT

### Таблица book_authors
- book_id: INTEGER, NOT NULL, FOREIGN KEY -> books(id), ON DELETE CASCADE
- author_id: INTEGER, NOT NULL, FOREIGN KEY -> authors(id), ON DELETE CASCADE
- PRIMARY KEY (book_id, author_id)

### Таблица book_copies
- id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL
- book_id: INTEGER, NOT NULL, FOREIGN KEY -> books(id), ON DELETE CASCADE
- barcode: VARCHAR(20), NOT NULL, UNIQUE, CHECK(barcode <> '') - штрих-код не пустой
- acquisition_date: DATE, NOT NULL, DEFAULT CURRENT_DATE
- status: VARCHAR(20), NOT NULL, CHECK(status IN ('available', 'borrowed', 'under maintenance', 'lost'))

### Таблица members
- id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL
- first_name: VARCHAR(50), NOT NULL, CHECK(first_name <> '' AND first_name !~ '\d')
- last_name: VARCHAR(50), NOT NULL, CHECK(last_name <> '' AND last_name !~ '\d')
- email: VARCHAR(100), NOT NULL, UNIQUE, CHECK(email LIKE '%@%') - email должен содержать @
- phone: VARCHAR(20), NULL
- address: TEXT, NULL
- membership_start_date: DATE, NOT NULL, DEFAULT CURRENT_DATE
- membership_status: VARCHAR(20), NOT NULL, CHECK(membership_status IN ('active', 'suspended', 'expired'))

### Таблица staff
- id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL
- first_name: VARCHAR(50), NOT NULL, CHECK(first_name <> '' AND first_name !~ '\d')
- last_name: VARCHAR(50), NOT NULL, CHECK(last_name <> '' AND last_name !~ '\d')
- email: VARCHAR(100), NOT NULL, UNIQUE, CHECK(email LIKE '%@%')
- role: VARCHAR(20), NOT NULL, CHECK(role IN ('librarian', 'admin'))

### Таблица loans
- id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL
- copy_id: INTEGER, NOT NULL, FOREIGN KEY -> book_copies(id), ON DELETE RESTRICT
- member_id: INTEGER, NOT NULL, FOREIGN KEY -> members(id), ON DELETE RESTRICT
- loan_date: DATE, NOT NULL, DEFAULT CURRENT_DATE
- due_date: DATE, NOT NULL, CHECK(due_date > loan_date) - срок возврата должен быть после даты выдачи
- return_date: DATE, NULL, CHECK(return_date IS NULL OR return_date >= loan_date)
- status: VARCHAR(20), NOT NULL, CHECK(status IN ('active', 'returned', 'overdue'))

### Таблица fines
- id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL
- loan_id: INTEGER, NOT NULL, UNIQUE, FOREIGN KEY -> loans(id), ON DELETE CASCADE
- member_id: INTEGER, NOT NULL, FOREIGN KEY -> members(id), ON DELETE CASCADE
- fine_amount: DECIMAL(10,2), NOT NULL, CHECK(fine_amount >= 0) - сумма штрафа неотрицательная
- issue_date: DATE, NOT NULL, DEFAULT CURRENT_DATE
- paid_date: DATE, NULL
- status: VARCHAR(20), NOT NULL, CHECK(status IN ('pending', 'paid'))

### Таблица reservations
- id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL
- book_id: INTEGER, NOT NULL, FOREIGN KEY -> books(id), ON DELETE CASCADE
- member_id: INTEGER, NOT NULL, FOREIGN KEY -> members(id), ON DELETE CASCADE
- reservation_date: TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP
- expiry_date: DATE, NOT NULL
- status: VARCHAR(20), NOT NULL, CHECK(status IN ('active', 'fulfilled', 'cancelled'))

## Общие ограничения целостности

- Все внешние ключи (FOREIGN KEY) должны ссылаться на существующие записи
- Нельзя оформить выдачу для книги со статусом, отличным от 'available'
- Один читатель не может иметь более 5 активных выдач одновременно
- Читатель не может бронировать одну и ту же книгу повторно
- В таблице book_authors запрещены дублирующиеся пары (book_id, author_id)
- Поля, участвующие в связях (book_id, author_id, member_id, copy_id и др.), не могут быть NULL
- Поля, критичные для бизнес-логики (title, isbn, email, role, status), не могут быть NULL
- При удалении книги должны каскадно удаляться все её копии и связи с авторами
- При удалении читателя должны удаляться все его выдачи, штрафы и бронирования
- В таблице loans срок возврата должен быть больше даты выдачи
- Автоматическое изменение статуса выдачи на 'overdue' при просрочке возврата
- Автоматическое начисление штрафа при переходе выдачи в статус 'overdue'
- Сумма штрафа рассчитывается как: количество дней просрочки × 10 рублей

## Пользовательские роли
### Для каждой роли - наименование, ответственность, количество пользователей в этой роли?

**Роль Администратор**
- **Наименование:** Администратор системы
- **Ответственность:** Полный доступ ко всем данным системы. Управление учетными записями сотрудников. Генерация отчетов по работе библиотеки. Настройка системных параметров (размер штрафа, сроки выдачи). Просмотр и анализ статистики.
- **Количество пользователей:** 1-2

**Роль Библиотекарь**
- **Наименование:** Сотрудник библиотеки
- **Ответственность:** Оформление выдачи и возврата книг. Регистрация новых читателей. Обслуживание бронирований. Начисление и снятие штрафов. Управление информацией о книгах и копиях.
- **Количество пользователей:** 5-10

**Роль Читатель**
- **Наименование:** Читатель библиотеки
- **Ответственность:** Просмотр каталога книг. Бронирование доступных книг. Просмотр своей истории выдач и текущих штрафов. Соблюдение сроков возврата книг.
- **Количество пользователей:** не ограничено

## UI / API

* Аутентификация и управление профилями
- POST /auth/login - авторизация сотрудников
- POST /auth/logout - выход из системы
- GET /members - список читателей
- POST /members - регистрация нового читателя
- GET /members/{id} - информация о читателе
- PUT /members/{id} - редактирование данных читателя

* Управление книгами и авторами
- GET /books - каталог книг (с фильтрацией по автору, жанру, году)
- POST /books - добавление новой книги
- GET /books/{id} - информация о книге
- PUT /books/{id} - редактирование данных книги
- GET /authors - список авторов
- POST /authors - добавление нового автора

* Выдача и возврат книг
- POST /loans - оформление выдачи книги
- PUT /loans/{id}/return - оформление возврата книги
- GET /loans/active - активные выдачи
- GET /loans/overdue - просроченные выдачи

* Бронирование книг
- POST /reservations - создание бронирования
- GET /reservations/active - активные бронирования
- PUT /reservations/{id}/cancel - отмена бронирования

* Управление штрафами
- GET /fines - список штрафов
- PUT /fines/{id}/pay - отметка об оплате штрафа
- GET /fines/member/{id} - штрафы конкретного читателя

* Отчеты и аналитика
- GET /reports/popular-books - самые популярные книги
- GET /reports/member-activity - активность читателей
- GET /reports/fines-summary - сводка по штрафам

## Технологии разработки

### Язык программирования
Мы будем использовать Python для бэкенд части, а конкретнее фреймворк FastAPI. Для фронтенд разработки воспользуемся React с TypeScript.

### СУБД
- PostgreSQL

## Тестирование
- pytest - основной фреймворк для тестирования
- pytest-asyncio - для асинхронного тестирования FastAPI
- pytest-cov - измерение покрытия кода тестами
- factory_boy - создание тестовых данных
- httpx - тестирование API эндпоинтов
- pytest-postgresql - временная PostgreSQL для тестов
- Тестирование всех ограничений целостности базы данных
- Тестирование бизнес-логики (начисление штрафов, проверка доступности книг)
