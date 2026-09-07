import os
import tempfile
from pathlib import Path
import pytest
from django.contrib.auth import get_user_model
from example.catalog.models import Author, Book, Tag

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".cache/ms-playwright"))
(ROOT / ".cache/tmp").mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(ROOT / ".cache/tmp")
os.environ["TMPDIR"] = tempfile.tempdir


@pytest.fixture
def data(db):
    User = get_user_model()
    admin = User.objects.create_superuser("admin", "admin@example.test", "Local-demo-2026!")
    author = Author.objects.create(name="Maya Rivers", email="maya@example.test")
    tag = Tag.objects.create(name="Design")
    book = Book.objects.create(title="Field notes", slug="field-notes", author=author, price=12)
    return {"admin": admin, "author": author, "tag": tag, "book": book}


@pytest.fixture
def auth_client(client, data):
    client.force_login(data["admin"])
    return client


def book_payload(author, **overrides):
    fields = dict(title="A new book", slug="a-new-book", author=str(author.pk), reviewer="", status="draft", price="12.00", published_at_0="2026-09-07", published_at_1="12:30:00", notes="", **{
        "chapter_set-TOTAL_FORMS": "0", "chapter_set-INITIAL_FORMS": "0", "chapter_set-MIN_NUM_FORMS": "0", "chapter_set-MAX_NUM_FORMS": "1000",
        "note_set-TOTAL_FORMS": "0", "note_set-INITIAL_FORMS": "0", "note_set-MIN_NUM_FORMS": "0", "note_set-MAX_NUM_FORMS": "1000", "_save": "Save",
    })
    fields.update(overrides)
    return fields
