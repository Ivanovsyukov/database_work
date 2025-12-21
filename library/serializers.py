"""
Сериализаторы для API библиотечной системы.

Сериализаторы делятся на две категории:
1. **Простые (Simple Serializers)** — для базовых операций чтения/записи моделей (авторы, издательства, книги и т.д.).
2. **Бизнес-сериализаторы (Business Serializers)** — для сложных сущностей (выдачи, штрафы, бронирования),
   где требуется валидация по бизнес-логике, управление статусами и защита от прямого изменения полей.

Все сериализаторы используют ModelSerializer, чтобы автоматически сопоставлять поля модели и JSON.
"""

from rest_framework import serializers
from .models import (
    Author, Publisher, Book, BookAuthor, BookCopy,
    Member, Staff, Loan, Fine, Reservation
)


# -------------------------
#   SIMPLE SERIALIZERS
# -------------------------

class AuthorSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Author. Используется в каталоге книг и при создании/редактировании книг."""
    class Meta:
        model = Author
        fields = '__all__'  # Все поля модели: first_name, last_name, birth_date, bio


class PublisherSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Publisher. Используется как вложенный объект в BookSerializer."""
    class Meta:
        model = Publisher
        fields = '__all__'


class BookSerializer(serializers.ModelSerializer):
    
    publisher = PublisherSerializer(read_only=True)

    publisher_id = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(),
        source='publisher',  
        write_only=True
    )

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'isbn', 'publication_year',
            'genre', 'publisher', 'publisher_id'
        ]


class BookSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Book с поддержкой вложенного отображения издательства.
    
    При чтении — возвращает полную информацию об издательстве (через nested-сериализатор).
    При записи — принимает только ID издательства (publisher_id), чтобы избежать создания
    нового издательства при POST-запросе.
    """
    # Только для чтения — полный объект Publisher
    publisher = PublisherSerializer(read_only=True)
    # Только для записи — принимаем ID и связываем с существующим объектом
    publisher_id = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(),
        source='publisher', # связывает поле publisher_id с полем publisher модели
        write_only=True
    )
    authors = AuthorSerializer(many=True, read_only=True)
    author_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Author.objects.all(),
        write_only=True,
        required=False
    )

    total_copies = serializers.SerializerMethodField(read_only=True)
    available_copies = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'isbn', 'publication_year',
            'genre', 'publisher', 'publisher_id',
            'authors', 'author_ids',
            'total_copies', 'available_copies'
        ]

    def create(self, validated_data):
        author_ids = validated_data.pop('author_ids', [])
        book = Book.objects.create(**validated_data)
        book.authors.set(author_ids)
        return book

    def update(self, instance, validated_data):
        author_ids = validated_data.pop('author_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if author_ids is not None:
            instance.authors.set(author_ids)
        return instance
    
    def get_total_copies(self, obj):
        return obj.copies.count()

    def get_available_copies(self, obj):
        return obj.copies.filter(status='available').count()

class BookAuthorSerializer(serializers.ModelSerializer):
    """
    Промежуточная модель для связи книги и автора (многие-ко-многим).
    Используется при детальном просмотре книги, если нужно получить список авторов с ID.
    """
    class Meta:
        model = BookAuthor
        fields = '__all__'


class BookCopySerializer(serializers.ModelSerializer):
    """
    Сериализатор для физической копии книги.
    Включает штрихкод, дату поступления и текущий статус (available, borrowed и т.д.).
    """
    class Meta:
        model = BookCopy
        fields = '__all__'


class MemberSerializer(serializers.ModelSerializer):
    """
    Сериализатор для читателя библиотеки.
    Содержит персональные данные, email, телефон и текущий статус членства (active/suspended/expired).
    """
    class Meta:
        model = Member
        fields = '__all__'


class StaffSerializer(serializers.ModelSerializer):
    """
    Сериализатор для сотрудника библиотеки (библиотекарь или админ).
    Используется при аутентификации и управлении аккаунтами (например, в админке или внутреннем API).
    """
    class Meta:
        model = Staff
        fields = '__all__'


# -------------------------
#   BUSINESS SERIALIZERS
# -------------------------

class LoanSerializer(serializers.ModelSerializer):
    """
    Сериализатор для операции выдачи книги.
    
    Особенности:
    - Поля `return_date` и `status` защищены от прямого редактирования через API (read_only).
      Статус и дата возврата обновляются только логикой в модели.
    - Валидация выполняется через вызов `full_clean()`, чтобы активировать:
        - ограничение на 5 активных выдач,
        - проверку статуса читателя,
        - проверку доступности копии.
    """
    class Meta:
        model = Loan
        fields = '__all__'
        read_only_fields = ['return_date', 'status']

    def validate(self, data):
        """
        Выполняет полную валидацию модели через Django-валидаторы.
        Если в данных ошибка (например, читатель уже имеет 5 книг),
        вызывается ValidationError с человекочитаемым сообщением.
        """
        instance = Loan(**data)
        try:
            instance.full_clean()
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return data

    def create(self, validated_data):
        """Создаёт выдачу и автоматически обновляет статус копии и читателя при необходимости."""
        loan = Loan.objects.create(**validated_data)
        return loan

    def update(self, instance, validated_data):
        """
        Обновление выдачи (например, при ручном возврате через API).
        После внесения изменений вызывается `full_clean()` и `save()`.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance


class FineSerializer(serializers.ModelSerializer):
    """
    Сериализатор для штрафа.
    
    Поля `issue_date` и `status` — только для чтения.
    Статус меняется не через API, а через метод `fine.pay()` или автоматически при создании.
    """
    class Meta:
        model = Fine
        fields = '__all__'
        read_only_fields = ['issue_date']


class ReservationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для бронирования книги.
    
    Статус бронирования (active, fulfilled, cancelled) управляется только через бизнес-логику.
    При создании проверяется:
      - отсутствие дублирующего активного бронирования,
      - корректность даты истечения.
    """
    class Meta:
        model = Reservation
        fields = '__all__'
        read_only_fields = ['status']

    def validate(self, data):
        """
        Запускает валидацию уровня модели (через full_clean),
        чтобы применить правила из Reservation.clean().
        """
        instance = Reservation(**data)
        try:
            instance.full_clean()
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return data

    def create(self, validated_data):
        """Создаёт бронирование с учётом всех проверок."""
        reservation = Reservation.objects.create(**validated_data)
        return reservation