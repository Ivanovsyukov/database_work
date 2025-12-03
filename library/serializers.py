from rest_framework import serializers
from .models import (
    Author, Publisher, Book, BookAuthor, BookCopy,
    Member, Staff, Loan, Fine, Reservation
)

# -------------------------
#   SIMPLE SERIALIZERS
# -------------------------

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = '__all__'


class BookSerializer(serializers.ModelSerializer):
    publisher = PublisherSerializer(read_only=True)
    publisher_id = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(), source='publisher', write_only=True
    )

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'isbn', 'publication_year',
            'genre', 'publisher', 'publisher_id'
        ]


class BookAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookAuthor
        fields = '__all__'


class BookCopySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookCopy
        fields = '__all__'


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = '__all__'


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = '__all__'


# -------------------------
#   BUSINESS SERIALIZERS
# -------------------------

class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = '__all__'
    def validate(self, data):
        instance = Loan(**data)
        instance.full_clean()
        return data

    def create(self, validated_data):
        loan = Loan(**validated_data)
        loan.full_clean()
        loan.save()
        return loan

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.full_clean()
        instance.save()
        return instance


class FineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fine
        fields = '__all__'


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'
    
    def validate(self, data):
        instance = Reservation(**data)
        instance.full_clean()
        return data

    def create(self, validated_data):
        reservation = Reservation(**validated_data)
        reservation.full_clean()
        reservation.save()
        return reservation