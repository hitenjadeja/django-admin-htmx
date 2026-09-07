from django.contrib import admin
from .models import Publisher, Publication, Page

@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    search_fields = ['name']
    ordering = ['name']

class PageInline(admin.TabularInline):
    model = Page
    extra = 1

@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    search_fields = ['title']
    prepopulated_fields = {'slug': ['title']}
    autocomplete_fields = ['publisher']
    inlines = [PageInline]
