# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render
from django.views import generic
from django import forms
from django.contrib import messages
from popupcrud.widgets import RelatedFieldPopupFormWidget

try:
    from django_select2.forms import Select2Widget
    _select2 = True
except ImportError:
    _select2 = False


from .models import Author, Book, AuthorRating, BookRating
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
    list_display = ('name', 'penname', 'age', 'half_age', 'double_age')
    list_url = reverse_lazy("library:authors")
    new_url = reverse_lazy("library:new-author")
    legacy_crud = True

    """
    form_class = AuthorForm
    list_permission_required = ('library.add_author',)
    create_permission_required = ('library.add_author',)
    update_permission_required = ('library.change_author',)
    delete_permission_required = ('library.delete_author',)
    """

    def half_age(self, author):
        return author.age/2
    half_age.label = "Half life"

    def get_edit_url(self, obj):
        return reverse_lazy("library:edit-author", kwargs={'pk': obj.pk})

    def get_delete_url(self, obj):
        if obj.age < 18:
            return None
        return reverse_lazy("library:delete-author", kwargs={'pk': obj.pk})


class BookCrudViewset(PopupCrudViewSet):
    model = Book
    fields = ('title', 'author')
    list_display = ('title', 'author')
    list_url = reverse_lazy("library:books")
    new_url = reverse_lazy("library:new-book")
    #paginate_by = None # disable pagination
    related_object_popups = {
        'author': reverse_lazy("library:new-author")
    }

    @staticmethod
    def get_edit_url(obj):
        return reverse_lazy("library:edit-book", kwargs={'pk': obj.pk})

    @staticmethod
    def get_delete_url(obj):
        return reverse_lazy("library:delete-book", kwargs={'pk': obj.pk})


class AuthorRatingForm(forms.Form):
    author = forms.ModelChoiceField(queryset=Author.objects.all())
    rating = forms.ChoiceField(label="Rating", choices=(
        ('1', '1 Star'),
        ('2', '2 Stars'),
        ('3', '3 Stars'),
        ('4', '4 Stars')
    ))

    def __init__(self, *args, **kwargs):
        super(AuthorRatingForm, self).__init__(*args, **kwargs)
        author = self.fields['author']
        author.widget = RelatedFieldPopupFormWidget(
            widget=forms.Select(choices=author.choices),
            new_url=reverse_lazy("library:new-author"))


class AuthorRatingView(generic.FormView):
    form_class = AuthorRatingForm
    template_name = "library/rating.html"
    success_url = reverse_lazy("library:author-rating")

    def form_valid(self, form):
        messages.info(self.request, "Thank you for your rating")
        return super(AuthorRatingView, self).form_valid(form)


class BookRatingForm(forms.ModelForm):

    class Meta:
        model = BookRating
        fields = ('book', 'rating')


class BookRatingView(generic.FormView):
    form_class = BookRatingForm
    template_name = "library/form.html"
    success_url = reverse_lazy("library:book-rating")

    def form_valid(self, form):
        messages.info(self.request, "Thank you for your rating")
        return super(BookRatingView, self).form_valid(form)


class MultipleRelatedObjectForm(forms.Form):
    author = forms.ModelChoiceField(queryset=Author.objects.all())
    book = forms.ModelChoiceField(queryset=Book.objects.all())

    def __init__(self, *args, **kwargs):
        super(MultipleRelatedObjectForm, self).__init__(*args, **kwargs)
        author = self.fields['author']
        author.widget = RelatedFieldPopupFormWidget(
            widget=Select2Widget(choices=author.choices) if _select2 else \
                    forms.Select(choices=author.choices),
            new_url=reverse_lazy("library:new-author"))
        book = self.fields['book']
        book.widget = RelatedFieldPopupFormWidget(
            widget=forms.Select(choices=book.choices),
            new_url=reverse_lazy("library:new-book"))


class MultipleRelatedObjectDemoView(generic.FormView):
    form_class = MultipleRelatedObjectForm
    template_name = "library/form.html"
    success_url = reverse_lazy("library:multi-related-object-demo")
