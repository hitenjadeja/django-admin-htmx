from django.db import models

class Publisher(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self): return self.name

class Publication(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    publisher = models.ForeignKey(Publisher, on_delete=models.PROTECT)
    published_at = models.DateTimeField(null=True, blank=True)
    def __str__(self): return self.title

class Page(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    text = models.CharField(max_length=100)
