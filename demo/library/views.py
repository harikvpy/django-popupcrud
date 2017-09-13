# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render
from django.views import generic
from django import forms

from .models import Author, Book
from popupcrud.views import PopupCrudViewSet

# Create your views here.

class AuthorForm(forms.ModelForm):
    sex = forms.ChoiceField(label="Sex", choices=(('M', 'Male'), ('F', 'Female')))
    class Meta:
        model = Author
        fields = ('name', 'penname', 'age')


class AuthorCrudViewset(PopupCrudViewSet):
    model = Author
    fields = ('name', 'penname', 'age')
    list_display = ('name', 'penname', 'age')
    list_url = reverse_lazy("library:authors")
    new_url = reverse_lazy("library:new-author")
    """
    form_class = AuthorForm
    list_permission_required = ('library.add_author',)
    create_permission_required = ('library.add_author',)
    update_permission_required = ('library.change_author',)
    delete_permission_required = ('library.delete_author',)

    def half_age(self, author):
        return author.age/2
    half_age.label = "Half life"
    """

    def get_edit_url(self, obj):
        return reverse_lazy("library:edit-author", kwargs={'pk': obj.pk})

    def get_delete_url(self, obj):
        return reverse_lazy("library:delete-author", kwargs={'pk': obj.pk})


class BookCrudViewset(PopupCrudViewSet):
    model = Book
    fields = ('title', 'author')
    list_display = ('title', 'author')
    list_url = reverse_lazy("library:books")
    new_url = reverse_lazy("library:new-book")
    paginate_by = None # disable pagination

    @staticmethod
    def get_edit_url(obj):
        return reverse_lazy("library:edit-book", kwargs={'pk': obj.pk})

    @staticmethod
    def get_delete_url(obj):
        return reverse_lazy("library:delete-book", kwargs={'pk': obj.pk})
