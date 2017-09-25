# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Author, Book

# Register your models here.
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'double_age')

    def double_age(self, obj):
        return obj.age*2
    double_age.short_description = "Double Age"

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    pass
