import csv
import secrets

from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.urls import path

from .models import Author, Book, Chapter, Edition, Note, Tag


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 1


class NoteInline(admin.StackedInline):
    model = Note
    extra = 1


@admin.action(description="Publish selected books")
def publish(modeladmin, request, queryset):
    count = queryset.update(status=Book.Status.PUBLISHED)
    modeladmin.message_user(request, f"Published {count} books.", messages.SUCCESS)


@admin.action(description="Archive selected books (confirm)")
def archive(modeladmin, request, queryset):
    if request.POST.get("confirm_archive"):
        count = queryset.update(status=Book.Status.ARCHIVED)
        modeladmin.message_user(request, f"Archived {count} books.")
        return None
    return TemplateResponse(
        request,
        "admin/catalog/book/archive.html",
        {
            **modeladmin.admin_site.each_context(request),
            "title": "Confirm archive",
            "books": queryset,
            "opts": modeladmin.model._meta,
            "action_checkbox_name": ACTION_CHECKBOX_NAME,
        },
    )


@admin.action(description="Export selected books (CSV)")
def export(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="books.csv"'
    writer = csv.writer(response)
    writer.writerow(["title", "status"])
    writer.writerows(queryset.values_list("title", "status"))
    return response


class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "status", "price", "published_at"]
    list_editable = ["status", "price"]
    list_filter = ["status", "author"]
    search_fields = ["title", "author__name"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["author"]
    raw_id_fields = ["reviewer"]
    filter_horizontal = ["tags"]
    date_hierarchy = "published_at"
    list_per_page = 5
    save_as = True
    inlines = [ChapterInline, NoteInline]
    actions = [publish, archive, export]
    fieldsets = [
        (None, {"fields": ["title", "slug", "author", "reviewer", "tags"]}),
        ("Publication", {"fields": ["status", "price", "published_at", "attachment"]}),
        ("Notes", {"fields": ["notes"], "classes": ["collapse"]}),
    ]


class AuthorAdmin(admin.ModelAdmin):
    ordering = ["name"]
    search_fields = ["name"]
    list_display = ["name", "email"]


class EditionAdmin(admin.ModelAdmin):
    filter_horizontal = ["contributors"]


admin.site.site_header = "Fieldwork · Administration"
admin.site.site_title = "Fieldwork admin"
admin.site.index_title = "Workspace overview"
for model, cls in [
    (Book, BookAdmin),
    (Author, AuthorAdmin),
    (Tag, admin.ModelAdmin),
    (Edition, EditionAdmin),
]:
    admin.site.register(model, cls)


class EditorialSite(admin.AdminSite):
    site_header = "Editorial · Administration"
    site_title = "Editorial admin"
    index_title = "Editorial workspace"

    def get_urls(self):
        return [
            path("report/", self.admin_view(self.report), name="report")
        ] + super().get_urls()

    def report(self, request):
        request.current_app = self.name
        nonce = secrets.token_urlsafe(24) if "csp" in request.GET else None
        response = TemplateResponse(
            request,
            "admin/catalog/report.html",
            {
                **self.each_context(request),
                "title": "Editorial report",
                "native": "native" in request.GET,
                "csp_nonce": nonce,
            },
        )
        if nonce:
            response["Content-Security-Policy"] = (
                f"script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'self'"
            )
        return response


editorial_site = EditorialSite(name="editorial")
for model, cls in [
    (Book, BookAdmin),
    (Author, AuthorAdmin),
    (Tag, admin.ModelAdmin),
    (Edition, EditionAdmin),
]:
    editorial_site.register(model, cls)
