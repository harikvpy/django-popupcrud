# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render
from django.views import generic

from .models import Author, Book
from popupcrud.views import PopupCrudViewSet

# Create your views here.

class AuthorList(generic.ListView):
    model = Author


class CreateAuthor(generic.CreateView):
    model = Author
    fields = ('name', 'penname', 'age')
    success_url = reverse_lazy("library:authors-list")


class EditAuthor(generic.UpdateView):
    model = Author
    fields = ('name', 'penname', 'age')
    success_url = reverse_lazy("library:authors-list")


class DeleteAuthor(generic.DeleteView):
    model = Author
    success_url = reverse_lazy("library:authors-list")


class BookList(generic.ListView):
    model = Book


class CreateBook(generic.CreateView):
    model = Book
    fields = ('title', 'author',)
    success_url = reverse_lazy("library:books-list")


# class BookDetail(generic.DetailView):
#     model = Book
#     fields = ('title', 'author',)
#
#

class EditBook(generic.UpdateView):
    model = Book
    fields = ('title', 'author',)
    success_url = reverse_lazy("library:books-list")


class DeleteBook(generic.DeleteView):
    model = Book
    success_url = reverse_lazy("library:books-list")


class AuthorCrudViewset(PopupCrudViewSet):
    model = Author
    fields = ('name', 'penname', 'age')
    success_url = reverse_lazy("library:writers-list")


class BookCrudViewset(PopupCrudViewSet):
    model = Book
    fields = ('title', 'author')
    success_url = reverse_lazy("library:books-list")
