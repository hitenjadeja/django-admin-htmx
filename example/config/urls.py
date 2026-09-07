from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from example.catalog.admin import editorial_site

urlpatterns = [path("admin/", admin.site.urls), path("editorial/", editorial_site.urls), path("", lambda request: HttpResponse("Fieldwork example site"))]
