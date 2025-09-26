# Техническое задание: Система управления библиотечным фондом

## Описание проекта

### Наименование
База данных системы управления библиотечным фондом

### Предметная область
Система предназначена для автоматизации работы библиотеки. Она позволяет вести учет книг, авторов, издательств, регистрировать читателей, оформлять выдачу и возврат литературы, управлять бронированиями и начислять штрафы за просрочку.

## Структура данных

### Таблицы и ограничения

#### Authors (Авторы)
| Поле | Тип | Ограничения |
|------|-----|-------------|
| author_id | INTEGER | PRIMARY KEY, AUTOINCREMENT, NOT NULL |
| first_name | VARCHAR(50) | NOT NULL, CHECK(first_name <> '') |
| last_name | VARCHAR(50) | NOT NULL, CHECK(last_name <> '') |
| birth_date | DATE | NULL |
| bio | TEXT | NULL |

#### Publishers (Издательства)
| Поле | Тип | Ограничения |
|------|-----|-------------|
| publisher_id | INTEGER | PRIMARY KEY, AUTOINCREMENT, NOT NULL |
| name | VARCHAR(100) | NOT NULL, UNIQUE, CHECK(name <> '') |
| address | TEXT | NULL |

####  Books (Книги)
| Поле | Тип | Ограничения |
|------|-----|-------------|
| book_id | INTEGER | PRIMARY KEY, AUTOINCREMENT, NOT NULL |
| title | VARCHAR(255) | NOT NULL, CHECK(title <> '') |
| isbn | VARCHAR(13) | UNIQUE, CHECK(LENGTH(isbn) = 13) |
| publication_year | INTEGER | NOT NULL, CHECK между 1450 и текущим годом |
| genre | VARCHAR(50) | NULL |
| publisher_id | INTEGER | FOREIGN KEY REFERENCES publishers(publisher_id) |

#### Book_Authors (Связь книг и авторов)
| Поле | Тип | Ограничения |
|------|-----|-------------|
| book_id | INTEGER | FOREIGN KEY, NOT NULL |
| author_id | INTEGER | FOREIGN KEY, NOT NULL |
| | | PRIMARY KEY (book_id, author_id) |

#### Book_Copies (Копии книг)
| Поле | Тип | Ограничения |
|------|-----|-------------|
| copy_id | INTEGER | PRIMARY KEY, AUTOINCREMENT, NOT NULL |
| book_id | INTEGER | FOREIGN KEY, NOT NULL |
| barcode | VARCHAR(20) | NOT NULL, UNIQUE, CHECK(barcode <> '') |
| acquisition_date | DATE | NOT NULL, DEFAULT CURRENT_DATE |
| status | VARCHAR(20) | NOT NULL, CHECK в ('available', 'borrowed', 'under maintenance', 'lost') |

#### Members (Читатели)
| Поле | Тип | Ограничения |
|------|-----|-------------|
| member_id | INTEGER | PRIMARY KEY, AUTOINCREMENT, NOT NULL |
| first_name | VARCHAR(50) | NOT NULL, CHECK(first_name <> '') |
| last_name | VARCHAR(50) | NOT NULL, CHECK(last_name <> '') |
| email | VARCHAR(100) | NOT NULL, UNIQUE, CHECK(email LIKE '%@%') |
| phone | VARCHAR(20) | NULL |
| address | TEXT | NULL |
| membership_start_date | DATE | NOT NULL, DEFAULT CURRENT_DATE |
| membership_status | VARCHAR(20) | NOT NULL, CHECK в ('active', 'suspended', 'expired') |

#### Staff (Сотрудники)
| Поле | Тип | Ограничения |
|------|-----|-------------|
| staff_id | INTEGER | PRIMARY KEY, AUTOINCREMENT, NOT NULL |
| first_name | VARCHAR(50) | NOT NULL, CHECK(first_name <> '') |
| last_name | VARCHAR(50) | NOT NULL, CHECK(last_name <> '') |
| email | VARCHAR(100) | NOT NULL, UNIQUE, CHECK(email LIKE '%@%') |
| role | VARCHAR(20) | NOT NULL, CHECK в ('librarian', 'admin') |

#### Loans (Выдачи книг)
| Поле | Тип | Ограничения |
|------|-----|-------------|
| loan_id | INTEGER | PRIMARY KEY, AUTOINCREMENT, NOT NULL |
| copy_id | INTEGER | FOREIGN KEY, NOT NULL |
| member_id | INTEGER | FOREIGN KEY, NOT NULL |
| loan_date | DATE | NOT NULL, DEFAULT CURRENT_DATE |
| due_date | DATE | NOT NULL, CHECK(due_date > loan_date) |
| return_date | DATE | NULL, CHECK(return_date >= loan_date) |
| status | VARCHAR(20) | NOT NULL, CHECK в ('active', 'returned', 'overdue') |

#### Fines (Штрафы)
| Поле | Тип | Ограничения |
|------|-----|-------------|
| fine_id | INTEGER | PRIMARY KEY, AUTOINCREMENT, NOT NULL |
| loan_id | INTEGER | FOREIGN KEY, UNIQUE, NOT NULL |
| member_id | INTEGER | FOREIGN KEY, NOT NULL |
| fine_amount | DECIMAL(10,2) | NOT NULL, CHECK(fine_amount >= 0) |
| issue_date | DATE | NOT NULL, DEFAULT CURRENT_DATE |
| paid_date | DATE | NULL |
| status | VARCHAR(20) | NOT NULL, CHECK в ('pending', 'paid') |

#### Reservations (Бронирования)
| Поле | Тип | Ограничения |
|------|-----|-------------|
| reservation_id | INTEGER | PRIMARY KEY, AUTOINCREMENT, NOT NULL |
| book_id | INTEGER | FOREIGN KEY, NOT NULL |
| member_id | INTEGER | FOREIGN KEY, NOT NULL |
| reservation_date | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| expiry_date | DATE | NOT NULL |
| status | VARCHAR(20) | NOT NULL, CHECK в ('active', 'fulfilled', 'cancelled') |

## Ограничения целостности

### Бизнес-правила
1. **Лимит выдач**: Читатель не может иметь более 5 активных выдач одновременно
2. **Доступность книг**: Нельзя оформить выдачу для книги со статусом, отличным от 'available'
3. **Уникальность бронирований**: Читатель не может бронировать одну и ту же книгу повторно
4. **Автоматизация штрафов**: 
   - Автоматическое изменение статуса выдачи на 'overdue' при просрочке
   - Автоматическое начисление штрафа при переходе в статус 'overdue'
   - Расчет штрафа: количество дней просрочки × 10 рублей

### Референциальная целостность
- Все внешние ключи ссылаются на существующие записи
- Каскадное удаление связанных данных
- Запрет на удаление записей с активными ссылками

## Пользовательские роли

### Администратор
- **Ответственность**: Полный доступ ко всем данным, управление сотрудниками, генерация отчетов
- **Количество**: 1-2 пользователя

### Библиотекарь
- **Ответственность**: Оформление выдачи/возврата, регистрация читателей, управление книгами
- **Количество**: 5-10 пользователей

### Читатель
- **Ответственность**: Просмотр каталога, бронирование книг, соблюдение сроков возврата
- **Количество**: Не ограничено

## API Endpoints

### Аутентификация и профили
- `POST /auth/login` - Авторизация
- `GET /members` - Список читателей
- `POST /members` - Регистрация читателя

### Управление книгами
- `GET /books` - Каталог книг (с фильтрацией)
- `POST /books` - Добавление книги
- `GET /books/{id}` - Информация о книге

### Выдача и возврат
- `POST /loans` - Оформление выдачи
- `PUT /loans/{id}/return` - Возврат книги
- `GET /loans/active` - Активные выдачи

### Бронирование
- `POST /reservations` - Бронирование книги
- `GET /reservations/active` - Активные бронирования

### Штрафы
- `GET /fines` - Список штрафов
- `PUT /fines/{id}/pay` - Оплата штрафа

### Отчеты
- `GET /reports/popular-books` - Популярные книги
- `GET /reports/member-activity` - Активность читателей

## Технологический стек

### Backend
- **Язык**: Python 3.11+
- **Фреймворк**: FastAPI
- **СУБД**: PostgreSQL 15+

### Frontend
- **Язык**: TypeScript
- **Фреймворк**: React 18+

### Тестирование
- **Фреймворк**: pytest
- **Покрытие**: pytest-cov
- **Данные**: factory_boy
- **API**: httpx

## Тестирование

### Модульное тестирование
- Тестирование моделей данных
- Проверка ограничений целостности
- Тестирование бизнес-логики

### Интеграционное тестирование
- Тестирование API endpoints
- Проверка работы с базой данных
- Тестирование сценариев использования

### Нагрузочное тестирование
- Тестирование производительности
- Проверка ограничений базы данных
- Оптимизация запросов
