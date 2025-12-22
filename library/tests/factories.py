import factory
from django.utils import timezone
from library.models import *

class AuthorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Author
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')

class PublisherFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Publisher
    name = factory.Faker('company')

class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Book
    title = factory.Faker('sentence', nb_words=4)
    isbn = factory.Faker('isbn13', separator='')
    publication_year = factory.Faker('year')
    publisher = factory.SubFactory(PublisherFactory)

class MemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Member
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')

class StaffFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Staff
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    role = 'librarian'

class BookCopyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BookCopy
    book = factory.SubFactory(BookFactory)
    barcode = factory.Sequence(lambda n: f"BC{n:06d}")

class LoanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Loan
    copy = factory.SubFactory(BookCopyFactory)
    member = factory.SubFactory(MemberFactory)
    loan_date = factory.LazyFunction(timezone.now().date)
    due_date = factory.LazyAttribute(
        lambda obj: obj.loan_date + timezone.timedelta(days=14)
    )
    status = 'active'