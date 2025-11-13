from django.core.validators import RegexValidator
from django.db import models


class Author(models.Model):
    no_digits_validator = RegexValidator(
        regex=r'^\D+$',
        message='Field cannot contain digits.',
    )

    first_name = models.CharField(max_length=50, validators=[no_digits_validator])
    last_name = models.CharField(max_length=50, validators=[no_digits_validator])
    birth_date = models.DateField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(first_name=''),
                name='author_first_name_not_empty',
            ),
            models.CheckConstraint(
                check=~models.Q(last_name=''),
                name='author_last_name_not_empty',
            ),
            models.CheckConstraint(
                check=models.Q(birth_date__gt='1500-01-01') | models.Q(birth_date__isnull=True),
                name='author_birth_date_valid',
            ),
        ]

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Publisher(models.Model):
    
    name = models.CharField(max_length=100, null = False, blank = False, unique=True)
    address = models.CharField(null = True, blank = True)
    
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check= ~models.Q(name=''),
                name='publisher_name_not_empty'
            ),
        ]