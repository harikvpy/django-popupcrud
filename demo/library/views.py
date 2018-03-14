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

    def clean_sex(self):
        data = self.cleaned_data['sex']
        if data == 'M':
            raise forms.ValidationError('Sex has to be Female!')
        return data


class AuthorCrudViewset(PopupCrudViewSet):
    model = Author
    form_class = AuthorForm
    #fields = ('name', 'penname', 'age')
    list_display = ('name', 'penname', 'age', 'half_age', 'double_age')
    list_url = reverse_lazy("library:authors")
    new_url = reverse_lazy("library:new-author")
    legacy_crud = False

    """
    form_class = AuthorForm
    list_permission_required = ('library.add_author',)
    create_permission_required = ('library.add_author',)
    update_permission_required = ('library.change_author',)
    delete_permission_required = ('library.delete_author',)
    """

    def half_age(self, author):
        return author.age/2 if author.age else '-'
    half_age.label = "Half life"
    half_age.order_field = 'age'

    def get_edit_url(self, obj):
        return reverse_lazy("library:edit-author", kwargs={'pk': obj.pk})

    def get_delete_url(self, obj):
        if not obj.age or obj.age < 18:
            return None
        return reverse_lazy("library:delete-author", kwargs={'pk': obj.pk})


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ('title', 'author')

    def __init__(self, *args, **kwargs):
        super(BookForm, self).__init__(*args, **kwargs)
        author = self.fields['author']
        author.widget = RelatedFieldPopupFormWidget(
            widget=Select2Widget(choices=author.choices) if _select2 else \
                    forms.Select(choices=author.choices),
            new_url=reverse_lazy("library:new-author"))


class BookCrudViewset(PopupCrudViewSet):
    model = Book
    form_class = BookForm
    list_display = ('title', 'author')
    list_url = reverse_lazy("library:books:list")
    new_url = reverse_lazy("library:books:create")
    #paginate_by = None # disable pagination
    related_object_popups = {
        'author': reverse_lazy("library:new-author")
    }
    legacy_crud = {
        'create': True,
    }
    item_actions = [
        ('Approve', 'glyphicon glyphicon-ok', 'approve')
    ]
    empty_list_icon = 'glyphicon glyphicon-book'
    empty_list_message = 'You have not defined any books.<br/>Create a book to get started.'

    @staticmethod
    def get_edit_url(obj):
        return reverse_lazy("library:books:update", kwargs={'pk': obj.pk})

    @staticmethod
    def get_delete_url(obj):
        return reverse_lazy("library:books:delete", kwargs={'pk': obj.pk})

    @staticmethod
    def get_detail_url(obj):
        return reverse_lazy("library:books:detail", kwargs={'pk': obj.pk})

    def approve(self, request, item_or_list):
        return True, "Request has been approved"


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
            new_url=reverse_lazy("library:books:create"))


class MultipleRelatedObjectDemoView(generic.FormView):
    form_class = MultipleRelatedObjectForm
    template_name = "library/form.html"
    success_url = reverse_lazy("library:multi-related-object-demo")


class CustomBookForm(forms.ModelForm):
    price = forms.DecimalField()
    # role = forms.ChoiceField(choices=(
    #     ('A', 'Administrator'),
    #     ('B', 'Manager'),
    #     ('C', 'Resident'),
    #     ('C', 'Guest'),
    # ))

    class Meta:
        model = Book
        fields = ('title', 'isbn')

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise forms.ValidationError('Price has to be > 0!')
        return price

class FormsetAuthorCrudViewset(AuthorCrudViewset):

    list_url = reverse_lazy("library:formset-authors:list")

    new_url = reverse_lazy("library:formset-authors:create")
    modal_sizes = {
        'create_edit': 'large',
        'delete': 'small',
        'detail': 'normal'
    }

    def get_edit_url(self, obj):
        return reverse_lazy("library:formset-authors:update", kwargs={'pk': obj.pk})

    def get_delete_url(self, obj):
        if not obj.age or obj.age < 18:
            return None
        return reverse_lazy("library:formset-authors:delete", kwargs={'pk': obj.pk})

    def get_formset_class(self):
        """
        Returns the inline formset class for adding Books to this author.
        """
        return forms.models.inlineformset_factory(
            Author,
            Book,
            form=CustomBookForm,
            fields=('title', 'isbn'),
            can_delete=True,
            extra=2)
