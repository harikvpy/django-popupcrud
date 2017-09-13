# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Author, Book

# Register your models here.
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    pass

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    pass
