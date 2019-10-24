from django.urls import reverse_lazy, reverse
from django import forms

try:
    from django_select2.forms import Select2Widget
    _select2 = True
except ImportError:
    _select2 = False

from popupcrud.widgets import RelatedFieldPopupFormWidget
from popupcrud.views import PopupCrudViewSet

from .models import Author, Book

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
        obj.pk = obj.pk or 1
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
    item_actions = [
        ('Up', 'glyphicon glyphicon-ok', 'up_vote'),
        ('Down', 'glyphicon glyphicon-remove', 'down_vote'),
    ]

    @staticmethod
    def get_edit_url(obj):
        return reverse_lazy("books:update", kwargs={'pk': obj.pk})

    @staticmethod
    def get_delete_url(obj):
        return reverse_lazy("books:delete", kwargs={'pk': obj.pk})

    @staticmethod
    def get_detail_url(obj):
        return reverse_lazy("books:detail", kwargs={'pk': obj.pk})

    def up_vote(self, request, book):
        return True, "Up vote successful"

    def down_vote(self, request, book):
        return True, "Down vote successful"


class BookUUIDCrudViewSet(PopupCrudViewSet):
    '''CRUD views using slug field as url kwarg instead of the default pk'''

    model = Book
    form_class = BookForm
    list_display = ('title', 'author')
    list_url = reverse_lazy("uuidbooks:list")
    new_url = reverse_lazy("uuidbooks:create")
    pk_url_kwarg = None
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    @staticmethod
    def get_edit_url(obj):
        return reverse("uuidbooks:update", kwargs={'uuid': obj.uuid.hex})

    @staticmethod
    def get_delete_url(obj):
        return reverse("uuidbooks:delete", kwargs={'uuid': obj.uuid.hex})

    @staticmethod
    def get_detail_url(obj):
        return reverse("uuidbooks:detail", kwargs={'uuid': obj.uuid.hex})
