# -*- coding: utf-8 -*-
import re
import json

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.utils import six

from .models import Author, Book
from .views import AuthorCrudViewset, BookCrudViewset

RE_CREATE_EDIT_FORM = r"\n<form class='form-horizontal' id='create-edit-form' action='{0}' method='post' accept-charset='utf-8'>.*</form>\n"

MODAL_PATTERNS = [
    r'<div class="modal fade".*id="create-edit-modal"',
    r'<div class="modal fade".*id="delete-modal"',
    r'<div class="modal fade".*id="action-result-modal"',
    r'<div class="modal fade".*id="add-related-modal"',
]

class PopupCrudViewSetTests(TestCase):

    def test_settings(self):
        from popupcrud.views import POPUPCRUD
        self.assertEquals(POPUPCRUD['base_template'], "test/base.html")

    def test_template(self):
        author = Author.objects.create(name="John", age=26)
        response = self.client.get(reverse("authors"))
        self.assertTemplateUsed(response, "popupcrud/list.html")
        # template should have the three embedded bootstrap modals
        for pattern in MODAL_PATTERNS:
            self.assertTrue(
                re.search(pattern, response.content.decode('utf-8')))

    def test_list_display(self):
        name = "John"
        author = Author.objects.create(name=name, age=26)
        response = self.client.get(reverse("authors"))
        html = response.content.decode('utf-8')
        self.assertTrue(
            re.search(r'<th.*sortable.*>.*Name.*</th>', html, re.DOTALL))
        self.assertTrue(
            re.search(r'<th.*sortable.*>.*Age.*</th>', html, re.DOTALL))
        self.assertTrue(
            re.search(r'<th.*sortable.*>.*Half Age.*</th>', html, re.DOTALL))
        self.assertTrue(
            re.search(r'<th.*Double Age.*</th>', html, re.DOTALL))
        self.assertFalse(
            re.search(r'<th.*sortable.*>.*DOUBLE AGE.*</th>', html, re.DOTALL))
        # also tests the get_obj_name() method
        first_col = """<a name="object_detail" data-url="{0}" data-title="Author Detail" href="javascript:void(0);">{1}</a><div data-name=\'{1}\'></div>"""
        self.assertContains(
            response,
            first_col.format(
                reverse("author-detail", kwargs={'pk': author.pk}),
                name)
        )
        self.assertContains(response, "<td>26</td>")
        self.assertContains(response, "<td>13</td>") # Author.half_age
        self.assertContains(response, "<td>52</td>") # AuthorCrudViewSet.double_age

        # test half_age field header has sortable as it has 'order_field'
        # attribute.

    def test_get_obj_name(self):
        # Also tests that unicode characters are rendered correctly
        name = "何瑞理"
        author = Author.objects.create(name=name, age=46)
        response = self.client.get(reverse("authors"))
        first_col = """<a name="object_detail" data-url="{0}" data-title="Author Detail" href="javascript:void(0);">{1}</a><div data-name=\'{1}\'></div>"""
        self.assertContains(
            response,
            first_col.format(
                reverse("author-detail", kwargs={'pk': author.pk}),
                name)
        )
        # "<div data-name=\'Peter Parker - 46\'></div>")

    def test_page_title(self):
        author = Author.objects.create(name="John", age=26)
        response = self.client.get(reverse("authors"))
        self.assertEquals(response.context['page_title'], "Author List")

    def test_empty_data(self):
        response = self.client.get(reverse("authors"))
        self.assertNotContains(response, "<table class='table")
        self.assertNotContains(response, "<th>Name</th>")
        self.assertNotContains(response, "<th>Age</th>")
        self.assertContains(response, "No records found")

    def test_urls(self):
        for _ in range(0, 10):
            Author.objects.create(name="John", age=25)
        response = self.client.get(reverse("authors"))
        self.assertContains(response, "New Author")
        self.assertContains(response, AuthorCrudViewset.new_url)
        for obj in Author.objects.all():
            self.assertContains(response, AuthorCrudViewset().get_edit_url(obj))
            self.assertContains(response, AuthorCrudViewset().get_delete_url(obj))
            self.assertContains(response, AuthorCrudViewset().get_detail_url(obj))

    def test_pagination(self):
        for _ in range(0, 30):
            Author.objects.create(name="John", age=25)
        response = self.client.get(reverse("authors"))
        po = response.context['page_obj']
        self.assertEqual(po.number, 1)
        self.assertTrue(po.has_next())
        self.assertFalse(po.has_previous())
        self.assertEqual(po.paginator.num_pages, 3)

    def test_create_form_template(self):
        # when requested through an AJAX, should only contain the <form></form>
        url = reverse("new-author")
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        match = re.search(RE_CREATE_EDIT_FORM.format(url),
                          response.content.decode('utf-8'), re.DOTALL)
        self.assertEqual(match.pos, 0)

    def test_update_form_template(self):
        # when requested through an AJAX, should only contain the <form></form>
        john = Author.objects.create(name="John", age=25)
        url = reverse("edit-author", kwargs={'pk': john.pk})
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        match = re.search(RE_CREATE_EDIT_FORM.format(url),
                          response.content.decode('utf-8'), re.DOTALL)
        self.assertEqual(match.pos, 0)

    def test_create(self):
        url = reverse("new-author")
        response = self.client.post(
            url,
            data={'name': 'John', 'age': 55},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        john = Author.objects.get(name='John', age=55)
        result = json.loads(response.content.decode('utf-8'))
        self.assertEquals(result, {'name': 'John', 'pk': john.pk})

    def test_update(self):
        john = Author.objects.create(name="John", age=25)
        url = reverse("edit-author", kwargs={'pk': john.pk})
        response = self.client.post(
            url,
            data={'name': 'Peter', 'age': 35},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        result = json.loads(response.content.decode('utf-8'))
        self.assertEquals(result, {'name': 'Peter', 'pk': john.pk})
        john.refresh_from_db()
        self.assertEquals(john.name, 'Peter')

    def test_detail(self):
        john = Author.objects.create(name="John", age=25)
        url = reverse("author-detail", kwargs={'pk': john.pk})
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTemplateUsed(response, "popupcrud/detail_inner.html")
        self.assertContains(response, "John")

    def test_legacy_crud_boolean(self):
        prev_value = AuthorCrudViewset.legacy_crud
        AuthorCrudViewset.legacy_crud = True
        response = self.client.get(reverse("authors"))
        for pattern in MODAL_PATTERNS:
            self.assertIsNone(
                re.search(pattern, response.content.decode('utf-8')))
        AuthorCrudViewset.legacy_crud = prev_value

    def test_legacy_crud_dict_create(self):
        prev_value = AuthorCrudViewset.legacy_crud
        AuthorCrudViewset.legacy_crud = {
            'create': True
        }
        response = self.client.get(reverse("authors"))
        # New Author button's href should be AuthorCrudViewset.new_url's value,
        # and not 'javascript:void(0)'
        NEW_BUTTON_RE = r'<a.*class="btn btn-primary".*href="%s.*">' % \
                str(AuthorCrudViewset.new_url)
        self.assertTrue(re.search(NEW_BUTTON_RE,
                        response.content.decode('utf-8'), re.DOTALL))
        AuthorCrudViewset.legacy_crud = prev_value

    def test_legacy_crud_dict_create_n_update(self):
        john = Author.objects.create(name="John", age=25)
        prev_value = AuthorCrudViewset.legacy_crud
        AuthorCrudViewset.legacy_crud = {
            'create': True,
            'update': True
        }
        response = self.client.get(reverse("authors"))
        # create_edit_modal modal dialog should not exist
        self.assertIsNone(
            re.search(MODAL_PATTERNS[0], response.content.decode('utf-8')))
        self.assertIsNone(
            re.search(MODAL_PATTERNS[3], response.content.decode('utf-8')))
        AuthorCrudViewset.legacy_crud = prev_value

    def test_legacy_crud_dict_detail(self):
        name = "John"
        john = Author.objects.create(name=name, age=25)
        prev_value = AuthorCrudViewset.legacy_crud
        AuthorCrudViewset.legacy_crud = {
            'detail': True,
        }
        response = self.client.get(reverse("authors"))
        # All the modal dialog's should be present, but Detail view should
        # point to the detail url and not javascript:void(0)
        for pattern in MODAL_PATTERNS:
            self.assertIsNotNone(
                re.search(pattern, response.content.decode('utf-8')))

        # note href != "javascript:void(0)"
        ITEM_DETAIL_RE = r'<a href="{0}".*>{1}</a>'.format(
            reverse("author-detail", kwargs={'pk': john.pk}),
            name)
        self.assertIsNotNone(
            re.search(ITEM_DETAIL_RE, response.content.decode('utf-8')))
        AuthorCrudViewset.legacy_crud = prev_value

    def test_legacy_create_contains_add_related_modal(self):
        prev_value = AuthorCrudViewset.legacy_crud
        AuthorCrudViewset.legacy_crud = {
            'create': True
        }
        response = self.client.get(reverse("new-author"))
        # modal id=add_related_modal pattern should exist in response
        self.assertIsNotNone(
            re.search(MODAL_PATTERNS[3], response.content.decode('utf-8')))

    def test_viewset_urls(self):
        # default arguments generates all views
        urls = BookCrudViewset.urls()
        for pattern in urls[0]:
            self.assertTrue(pattern.name in ('list', 'create', 'detail', 'update', 'delete'))

        # namespace defaults to model's verbose_name_plural
        self.assertEqual(urls[2], 'books')

        urls = BookCrudViewset.urls(views=('create', 'detail'))
        for pattern in urls[0]:
            self.assertTrue(pattern.name in ('list', 'create', 'detail'))

        urls = BookCrudViewset.urls(views=('update', 'delete'))
        for pattern in urls[0]:
            self.assertTrue(pattern.name in ('list', 'update', 'delete'))

        # test namespace argument
        urls = BookCrudViewset.urls(namespace='titles')
        self.assertEqual(urls[2], 'titles')

    def test_viewset_urls(self):
        # Integration test for urls(). Verify that the generated CRUD urls are
        # registered in URLconf correctly.
        name = "John"
        john = Author.objects.create(name=name, age=25)
        book = Book.objects.create(title='Title', author=john)
        self.assertIsNotNone(reverse("books:list"))
        self.assertIsNotNone(reverse("books:create"))
        self.assertIsNotNone(reverse("books:detail", kwargs={'pk': book.pk}))
        self.assertIsNotNone(reverse("books:update", kwargs={'pk': book.pk}))
        self.assertIsNotNone(reverse("books:delete", kwargs={'pk': book.pk}))

    def test_item_action_links(self):
        """
        Tests that item custom action links are added to standard action
        items for each row in the list.
        """
        name = "John"
        john = Author.objects.create(name=name, age=25)
        peter = Author.objects.create(name="Peter", age=30)
        book1 = Book.objects.create(title='Title 1', author=john)
        book2 = Book.objects.create(title='Title 2', author=peter)
        response = self.client.get(reverse("books:list"))
        item_action = "<a name=\'custom_action\' href=\'javascript:void(0);\' title=\'{0}\' data-action=\'{1}\' data-obj=\'{2}\'><span class=\'{3}\'></span></a>"
        for book in response.context['object_list']:
            up_pattern = item_action.format(
                "Up", "0", book1.pk, "glyphicon glyphicon-ok")
            down_pattern = item_action.format(
                "Down", "1", book2.pk, "glyphicon glyphicon-remove")
            self.assertContains(response, up_pattern)
            self.assertContains(response, down_pattern)

    def test_item_action(self):
        """
        Test that item custom action POST request results in a call to the
        CrudViewSet method specified.

        We cannot test JavaScript from unit test framework, but we can simulate
        the relevant JS script behavior and run through the backend python code
        for custom item actions.
        """
        name = "John"
        john = Author.objects.create(name=name, age=25)
        book = Book.objects.create(title='Title 1', author=john)
        response = self.client.post(reverse("books:list"), data={
            'action': '0', 'item': book.pk})
        result = json.loads(response.content.decode('utf-8'))
        self.assertEquals(result, {'result': True,
                                   'message': "Up vote successful"})

        response = self.client.post(reverse("books:list"), data={
            'action': '1', 'item': book.pk})
        result = json.loads(response.content.decode('utf-8'))
        self.assertEquals(result, {'result': True,
                                   'message': "Down vote successful"})
