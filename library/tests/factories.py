import factory
from factory.django import DjangoModelFactory
from library.models import Author, Publisher, Book, BookCopy, Member, Staff


class PublisherFactory(DjangoModelFactory):
    class Meta:
        model = Publisher
    name = factory.Sequence(lambda n: f"Publisher {n}")


class AuthorFactory(DjangoModelFactory):
    class Meta:
        model = Author
    first_name = "John"
    last_name = "Doe"


class BookFactory(DjangoModelFactory):
    class Meta:
        model = Book
        skip_postgeneration_save = True
    title = "Test Book"
    isbn = factory.Sequence(lambda n: f"{str(n).zfill(13)}")
    publication_year = 2020
    publisher = factory.SubFactory(PublisherFactory)

    @factory.post_generation
    def authors(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for author in extracted:
                self.authors.add(author)
        else:
            self.authors.add(AuthorFactory())


class MemberFactory(DjangoModelFactory):
    class Meta:
        model = Member
    first_name = "Alice"
    last_name = "Smith"
    email = factory.Sequence(lambda n: f"alice{n}@example.com")


class StaffFactory(DjangoModelFactory):
    class Meta:
        model = Staff

    first_name = "Bob"
    last_name = "Admin"
    email = factory.Sequence(lambda n: f"staff{n}@example.com")
    role = "librarian"


class BookCopyFactory(DjangoModelFactory):
    class Meta:
        model = BookCopy
    book = factory.SubFactory(BookFactory)
    barcode = factory.Sequence(lambda n: f"BC{n}")
