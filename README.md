ТЕХНИЧЕСКОЕ ЗАДАНИЕ

#Наименование

"База данных системы управления библиотечным фондом"
#Предметная область

Система предназначена для автоматизации работы библиотеки. Она позволяет вести учет книг, авторов, издательств, регистрировать читателей, оформлять выдачу и возврат литературы, управлять бронированиями и начислять штрафы за просрочку.
#Данные
##Для каждого элемента данных - ограничения

###Таблица authors (Авторы)

    author_id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL

    first_name: VARCHAR(50), NOT NULL, CHECK(first_name <> '')

    last_name: VARCHAR(50), NOT NULL, CHECK(last_name <> '')

    birth_date: DATE, NULL

    bio: TEXT, NULL

###Таблица publishers (Издательства)

    publisher_id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL

    name: VARCHAR(100), NOT NULL, UNIQUE, CHECK(name <> '')

    address: TEXT, NULL

###Таблица books (Книги)

    book_id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL

    title: VARCHAR(255), NOT NULL, CHECK(title <> '')

    isbn: VARCHAR(13), UNIQUE, CHECK(LENGTH(isbn) = 13)

    publication_year: INTEGER, NOT NULL, CHECK(publication_year BETWEEN 1450 AND EXTRACT(YEAR FROM CURRENT_DATE))

    genre: VARCHAR(50), NULL

    publisher_id: INTEGER, NOT NULL, FOREIGN KEY REFERENCES publishers(publisher_id)

###Таблица book_authors (Связь книг и авторов)

    book_id: INTEGER, NOT NULL, FOREIGN KEY REFERENCES books(book_id) ON DELETE CASCADE

    author_id: INTEGER, NOT NULL, FOREIGN KEY REFERENCES authors(author_id) ON DELETE CASCADE

    PRIMARY KEY (book_id, author_id)

###Таблица book_copies (Копии книг)

    copy_id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL

    book_id: INTEGER, NOT NULL, FOREIGN KEY REFERENCES books(book_id) ON DELETE CASCADE

    barcode: VARCHAR(20), NOT NULL, UNIQUE, CHECK(barcode <> '')

    acquisition_date: DATE, NOT NULL, DEFAULT CURRENT_DATE

    status: VARCHAR(20), NOT NULL, CHECK(status IN ('available', 'borrowed', 'under maintenance', 'lost'))

###Таблица members (Читатели)

    member_id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL

    first_name: VARCHAR(50), NOT NULL, CHECK(first_name <> '')

    last_name: VARCHAR(50), NOT NULL, CHECK(last_name <> '')

    email: VARCHAR(100), NOT NULL, UNIQUE, CHECK(email LIKE '%@%')

    phone: VARCHAR(20), NULL

    address: TEXT, NULL

    membership_start_date: DATE, NOT NULL, DEFAULT CURRENT_DATE

    membership_status: VARCHAR(20), NOT NULL, CHECK(membership_status IN ('active', 'suspended', 'expired'))

###Таблица staff (Сотрудники)

    staff_id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL

    first_name: VARCHAR(50), NOT NULL, CHECK(first_name <> '')

    last_name: VARCHAR(50), NOT NULL, CHECK(last_name <> '')

    email: VARCHAR(100), NOT NULL, UNIQUE, CHECK(email LIKE '%@%')

    role: VARCHAR(20), NOT NULL, CHECK(role IN ('librarian', 'admin'))

###Таблица loans (Выдачи книг)

    loan_id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL

    copy_id: INTEGER, NOT NULL, FOREIGN KEY REFERENCES book_copies(copy_id)

    member_id: INTEGER, NOT NULL, FOREIGN KEY REFERENCES members(member_id)

    loan_date: DATE, NOT NULL, DEFAULT CURRENT_DATE

    due_date: DATE, NOT NULL, CHECK(due_date > loan_date)

    return_date: DATE, NULL, CHECK(return_date IS NULL OR return_date >= loan_date)

    status: VARCHAR(20), NOT NULL, CHECK(status IN ('active', 'returned', 'overdue'))

###Таблица fines (Штрафы)

    fine_id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL

    loan_id: INTEGER, NOT NULL, UNIQUE, FOREIGN KEY REFERENCES loans(loan_id) ON DELETE CASCADE

    member_id: INTEGER, NOT NULL, FOREIGN KEY REFERENCES members(member_id) ON DELETE CASCADE

    fine_amount: DECIMAL(10,2), NOT NULL, CHECK(fine_amount >= 0)

    issue_date: DATE, NOT NULL, DEFAULT CURRENT_DATE

    paid_date: DATE, NULL

    status: VARCHAR(20), NOT NULL, CHECK(status IN ('pending', 'paid'))

###Таблица reservations (Бронирования)

    reservation_id: INTEGER, PRIMARY KEY, AUTOINCREMENT, NOT NULL

    book_id: INTEGER, NOT NULL, FOREIGN KEY REFERENCES books(book_id) ON DELETE CASCADE

    member_id: INTEGER, NOT NULL, FOREIGN KEY REFERENCES members(member_id) ON DELETE CASCADE

    reservation_date: TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP

    expiry_date: DATE, NOT NULL

    status: VARCHAR(20), NOT NULL, CHECK(status IN ('active', 'fulfilled', 'cancelled'))

##Общие ограничения целостности

    Все внешние ключи должны ссылаться на существующие записи

    При удалении книги каскадно удаляются все её копии и связи с авторами

    При удалении читателя каскадно удаляются все его выдачи, штрафы и бронирования

    Один читатель не может иметь более 5 активных выдач одновременно

    Нельзя оформить выдачу для книги со статусом, отличным от 'available'

    Читатель не может бронировать одну и ту же книгу повторно

    В таблице book_authors запрещены дублирующиеся пары (book_id, author_id)

    Автоматическое изменение статуса выдачи на 'overdue' при просрочке возврата

    Автоматическое начисление штрафа при переходе выдачи в статус 'overdue'

    Сумма штрафа рассчитывается как: количество дней просрочки × 10 рублей

#Пользовательские роли
##Для каждой роли - наименование, ответственность, количество пользователей в этой роли?

Роль Администратор

    Наименование: Администратор системы

    Ответственность: Полный доступ ко всем данным, управление сотрудниками, генерация отчетов

    Количество пользователей: 1-2

Роль Библиотекарь

    Наименование: Сотрудник библиотеки

    Ответственность: Оформление выдачи/возврата, регистрация читателей, управление книгами

    Количество пользователей: 5-10

Роль Читатель

    Наименование: Читатель библиотеки

    Ответственность: Просмотр каталога, бронирование книг, соблюдение сроков возврата

    Количество пользователей: не ограничено

#UI / API

    Аутентификация и профили

    POST /auth/login - авторизация

    GET /members - список читателей

    POST /members - регистрация читателя

    Управление книгами

    GET /books - каталог книг

    POST /books - добавление книги

    GET /books/{id} - информация о книге

    Выдача и возврат

    POST /loans - оформление выдачи

    PUT /loans/{id}/return - возврат книги

    GET /loans/active - активные выдачи

    Бронирование

    POST /reservations - бронирование книги

    GET /reservations/active - активные бронирования

    Штрафы

    GET /fines - список штрафов

    PUT /fines/{id}/pay - оплата штрафа

    Отчеты

    GET /reports/popular-books - популярные книги

    GET /reports/member-activity - активность читателей

#Технологии разработки
##Язык программирования

Python с фреймворком FastAPI для бэкенда, React для фронтенда
##СУБД

PostgreSQL
#Тестирование

    pytest для модульного тестирования

    pytest-cov для измерения покрытия кода

    factory_boy для создания тестовых данных

    httpx для тестирования API

    Тестирование всех ограничений целостности БД

    Тестирование бизнес-логики системы
