from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
from example.catalog.models import Author, Book, Chapter, Tag


class Command(BaseCommand):
    help = "Seed local demonstration data and test-only accounts. Never run in production."

    def handle(self, *args, **options):
        user, _ = get_user_model().objects.get_or_create(username="admin", defaults={"is_staff": True, "is_superuser": True})
        user.set_password("Local-demo-2026!")
        user.save()
        viewer, _ = get_user_model().objects.get_or_create(username="viewer", defaults={"is_staff": True})
        viewer.set_password("Local-demo-2026!")
        viewer.save()
        viewer.user_permissions.set(Permission.objects.filter(codename__in=["view_book", "view_author", "view_tag"]))
        authors = [Author.objects.get_or_create(name=name, defaults={"email": email})[0] for name, email in [("Maya Rivers", "maya@example.test"), ("Alex Chen", "alex@example.test"), ("Sam Wilson", "sam@example.test")]]
        tags = [Tag.objects.get_or_create(name=name)[0] for name in ["Design", "Research", "Field notes"]]
        titles = ["A practice of observation", "The shape of everyday things", "Small spaces, thoughtful places", "Notes from the field", "A guide to slow discovery", "Patterns in the landscape", "Making room for ideas", "The working notebook", "Quiet systems", "Ways of seeing", "The considered collection", "Building with care"]
        for i, title in enumerate(titles):
            book, _ = Book.objects.get_or_create(slug=f"fieldwork-{i + 1}", defaults={"title": title, "author": authors[i % 3], "status": "published" if i % 3 == 0 else "draft", "price": 12 + i})
            book.tags.set(tags[:1 + i % 3])
            Chapter.objects.get_or_create(book=book, title="Introduction", defaults={"position": 1})
        self.stdout.write(self.style.SUCCESS("Seeded local example. admin / Local-demo-2026!; viewer / Local-demo-2026!"))
