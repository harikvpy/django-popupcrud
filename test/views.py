from django.core.urlresolvers import reverse_lazy, reverse
from django import forms

from .models import Author
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

    """
    form_class = AuthorForm
    list_permission_required = ('tests.add_author',)
    create_permission_required = ('tests.add_author',)
    update_permission_required = ('tests.change_author',)
    delete_permission_required = ('tests.delete_author',)
    """

    def half_age(self, author):
        return int(author.age/2)
    half_age.label = "Half Age"

    def get_edit_url(self, obj):
        return reverse("edit-author", kwargs={'pk': obj.pk})

    def get_delete_url(self, obj):
        if obj.age < 18:
            return None
        return reverse("delete-author", kwargs={'pk': obj.pk})
