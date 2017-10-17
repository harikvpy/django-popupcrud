from django.core.urlresolvers import reverse_lazy, reverse
from django import forms

try:
    from django_select2.forms import Select2Widget
    _select2 = True
except ImportError:
    _select2 = False

from .models import Author, Book
from popupcrud.widgets import RelatedFieldPopupFormWidget
from popupcrud.views import PopupCrudViewSet

# Create your views here.

class AuthorForm(forms.ModelForm):
    sex = forms.ChoiceField(label="Sex", choices=(('M', 'Male'), ('F', 'Female')))
    class Meta:
        model = Author
        fields = ('name', 'age')


class AuthorCrudViewset(PopupCrudViewSet):
    model = Author
    fields = ('name', 'age')
    list_display = ('name', 'age', 'half_age', 'double_age')
    list_url = reverse_lazy("authors")
    new_url = reverse_lazy("new-author")
    page_title = "Author List"

    """
    form_class = AuthorForm
    list_permission_required = ('tests.add_author',)
    create_permission_required = ('tests.add_author',)
    update_permission_required = ('tests.change_author',)
    delete_permission_required = ('tests.delete_author',)
    """

    def half_age(self, author):
        return int(author.age/2)
    half_age.short_description = "Half Age"
    half_age.order_field = 'age'

    def get_detail_url(self, obj):
        return reverse("author-detail", kwargs={'pk': obj.pk})

    def get_edit_url(self, obj):
        return reverse("edit-author", kwargs={'pk': obj.pk})

    def get_delete_url(self, obj):
        if obj.age < 18:
            return None
        return reverse("delete-author", kwargs={'pk': obj.pk})


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
            new_url=reverse_lazy("new-author"))


class BookCrudViewset(PopupCrudViewSet):
    model = Book
    form_class = BookForm
    list_display = ('title', 'author')
    list_url = reverse_lazy("books:list")
    new_url = reverse_lazy("books:create")
    related_object_popups = {
        'author': reverse_lazy("new-author")
    }
    legacy_crud = True

    @staticmethod
    def get_edit_url(obj):
        return reverse_lazy("books:update", kwargs={'pk': obj.pk})

    @staticmethod
    def get_delete_url(obj):
        return reverse_lazy("books:delete", kwargs={'pk': obj.pk})

    @staticmethod
    def get_detail_url(obj):
        return reverse_lazy("books:detail", kwargs={'pk': obj.pk})
