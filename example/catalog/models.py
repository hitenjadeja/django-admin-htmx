from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Book(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    author = models.ForeignKey(Author, on_delete=models.PROTECT, related_name="books")
    reviewer = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed")
    tags = models.ManyToManyField(Tag, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=12, validators=[MinValueValidator(0)])
    published_at = models.DateTimeField(default=timezone.now)
    attachment = models.FileField(upload_to="books/", blank=True)
    notes = models.TextField(blank=True)

    def clean(self):
        if self.title.lower() == "invalid":
            raise ValidationError("Choose a descriptive title; ‘invalid’ is reserved for validation checks.")

    def __str__(self):
        return self.title


class Chapter(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    position = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    def __str__(self):
        return self.title


class Note(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)

    def __str__(self):
        return self.text


class Edition(models.Model):
    name = models.CharField(max_length=100)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    contributors = models.ManyToManyField(Author, blank=True)

    def __str__(self):
        return self.name
