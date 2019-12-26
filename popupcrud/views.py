# -*- coding: utf-8 -*-
# pylint: disable=too-many-lines
""" Popupcrud views """

from collections import OrderedDict
import copy

from django import forms
from django.db import transaction
from django.conf import settings
from django.conf.urls import include, url
from django.core.exceptions import (
    FieldDoesNotExist, ObjectDoesNotExist)
from django.shortcuts import render
from django.views import generic
from django.http import JsonResponse
from django.template import loader
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.utils.decorators import classonlymethod
from django.utils.translation import ugettext_lazy as _, ugettext, override
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.functional import cached_property

try:
    from django.utils import six
except ImportError:
    import six

#from django.contrib.admin import ModelAdmin

from pure_pagination import PaginationMixin

from .widgets import RelatedFieldPopupFormWidget


POPUPCRUD_DEFAULTS = {
    'base_template': 'base.html',

    'page_title_context_variable': 'page_title',

    'paginate_by': 10,
}
"""django-popupcrud global settings are specified as the dict variable
``POPUPCRUD`` in settings.py.

``POPUPCRUD`` currently supports the following settings with their
default values:

    - ``base_template``: The prjoject base template from which all popupcrud
      templates should be derived.

      Defaults to ``base.html``.

    - ``page_title_context_variable``: Name of the context variable whose value
      will be set as the title for the CRUD list view page. This title is
      specified as the value for the class attribute ``ViewSet.page_title`` or
      as the return value of ``ViewSet.get_page_title()``.

      Defaults to ``page_title``.

    - ``paginate_by``: Default number of rows per page for queryset pagination.
      This is the same as ListView.paginate_by.

      Defaults to 10.
"""

# build effective settings by merging any user settings with defaults
POPUPCRUD = POPUPCRUD_DEFAULTS.copy()
POPUPCRUD.update(getattr(settings, 'POPUPCRUD', {}))

ALL_VAR = 'all'
ORDER_VAR = 'o'
ORDER_TYPE_VAR = 'ot'
PAGE_VAR = 'p'
SEARCH_VAR = 'q'
ERROR_FLAG = 'e'

IGNORED_PARAMS = (
    ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR)

DEFAULT_MODAL_SIZES = {
    'create_update': 'normal',
    'delete': 'normal',
    'detail': 'normal',
}

class AjaxObjectFormMixin(object):
    """
    Mixin facilitates single object create/edit functions to be performed
    through an AJAX request.

    Views that provide the feature of creating/editing model objects
    via AJAX requests should derive from this class.

    So if CRUD for a model wants to allow creation of its objects via a popup,
    its CreateView should include this mixin in its derivation chain. Such a
    view an also support its objects being created from the view for another
    model which has a ForeignKey into it and wants to provide 'inline-creation'
    of releated objects from a popup without leaving the context of the model
    object view being created/edited.
    """
    def get_context_data(self, **kwargs):
        if 'formset' not in kwargs:
            formset = self._viewset.get_formset()
            if formset:
                kwargs['formset'] = formset
        return super(AjaxObjectFormMixin, self).get_context_data(**kwargs)

    def get_ajax_response(self):
        return JsonResponse({
            'name': str(self.object), # object representation
            'pk': self.object.pk          # object id
        })

    # following two methods are applicable only to Create/Edit views
    def get_form_class(self):
        if getattr(self._viewset, 'form_class', None):
            return self._viewset.form_class
        return super(AjaxObjectFormMixin, self).get_form_class()

    def get_form(self, form_class=None):
        form = super(AjaxObjectFormMixin, self).get_form(form_class)
        if not getattr(self._viewset, 'form_class', None):
            self._init_related_fields(form)
        return form

    def _init_related_fields(self, form):
        related_popups = getattr(self._viewset, 'related_object_popups', {})
        for fname in related_popups:
            if fname in form.fields:
                _ = form.fields[fname]
                if isinstance(form.fields[fname], forms.ModelChoiceField):
                    form.fields[fname].widget = RelatedFieldPopupFormWidget(
                        widget=forms.Select(choices=form.fields[fname].choices),
                        new_url=related_popups[fname])

    @transaction.atomic
    def form_valid(self, form): # pylint: disable=missing-docstring
        self.object = form.save(commit=False)
        formset_class = self._viewset.formset_class
        formset = None
        if formset_class:
            formset = formset_class(
                self.request.POST,
                instance=self.object)

        if not formset or formset.is_valid():
            self.object.save()
            form.save_m2m()
            if formset:
                formset.save()

            if self.request.is_ajax():
                return self.get_ajax_response()

            return super(AjaxObjectFormMixin, self).form_valid(form)

        kwargs = {'form': form}
        if formset:
            kwargs.update({'formset': formset})
        return self.render_to_response(self.get_context_data(**kwargs))

    def handle_no_permission(self):
        if self.request.is_ajax():
            return render(self.request, 'popupcrud/403.html')
        return super(AjaxObjectFormMixin, self).handle_no_permission()


class AttributeThunk(object):
    """
    Class thunks various attributes expected by Django generic CRUD views as
    properties of the parent viewset class instance. This allows us to
    normalize all CRUD view attributes as ViewSet properties and/or methods.
    """
    def __init__(self, viewset, *args, **kwargs):
        self._viewset = viewset()   # Sat 9/9, changed to store Viewset object
                                    # instead of viewset class
        self._viewset.view = self   # allow viewset methods to access view
        super(AttributeThunk, self).__init__(*args, **kwargs)

    @property
    def model(self):
        return self._viewset.model

    @property
    def fields(self):
        return self._viewset.fields

    @property
    def context_object_name(self):
        return self._viewset.context_object_name

    @property
    def pk_url_kwarg(self):
        return self._viewset.pk_url_kwarg

    @property
    def slug_field(self):
        return self._viewset.slug_field

    @property
    def slug_url_kwarg(self):
        return self._viewset.slug_url_kwarg

    def get_success_url(self):
        return self._viewset.get_list_url()

    def get_form_kwargs(self):
        kwargs = super(AttributeThunk, self).get_form_kwargs() # pylint: disable=E1101
        kwargs.update(self._viewset.get_form_kwargs())
        return kwargs

    def get_context_data(self, **kwargs):
        kwargs['base_template'] = POPUPCRUD['base_template']
        title_cv = POPUPCRUD['page_title_context_variable']
        kwargs[title_cv] = kwargs['pagetitle'] #self._viewset.get_page_title()
        kwargs['viewset'] = self._viewset
        kwargs[self._viewset.breadcrumbs_context_variable] = \
                copy.deepcopy(self._viewset.get_breadcrumbs())
        if not self.request.is_ajax() and not isinstance(self, ListView): # pylint: disable=E1101
            # for legacy crud views, add the listview url to the breadcrumb
            kwargs[self._viewset.breadcrumbs_context_variable].append(
                (self._viewset.get_page_title('list'), self._viewset.get_list_url()))
        self._viewset.get_context_data(kwargs)
        return super(AttributeThunk, self).get_context_data(**kwargs) # pylint: disable=E1101

    @property
    def login_url(self):
        # If view specific attribute is set in PopupCrudViewSet, return it.
        # Otherwise, return the ViewSet global 'login_url' attr value.
        return getattr(self._viewset,
                       "%s_login_url" % self._get_view_code(),
                       self._viewset.login_url)

    @property
    def raise_exception(self):
        # If view specific attribute is set in PopupCrudViewSet, return it.
        # Otherwise, return the ViewSet global 'raise_exception' attr value.
        return getattr(self._viewset,
                       "%s_raise_exception" % self._get_view_code(),
                       self._viewset.raise_exception)

    def get_permission_required(self):
        return self._viewset.get_permission_required(self._get_view_code())

    def _get_view_code(self):
        """ Returns the short code for this ViewSet view """
        codes = {
            'ListView': 'list',
            'DetailView': 'detail',
            'CreateView': 'create',
            'UpdateView': 'update',
            'DeleteView': 'delete'
        }
        return codes[self.__class__.__name__]

    @property
    def media(self):
        popups = self._viewset.popups
        # don't load popupcrud.js if all crud views are set to 'legacy'
        popupcrud_media = forms.Media(
            css={'all': ('popupcrud/css/popupcrud.css',)},
            js=('popupcrud/js/popupcrud.js',))

        # Optimization: add the form and formset media only if we're either
        # (CreateView or UpdateView) or in a ListView with popups enabled for
        # either of 'create' or 'update' operation.
        if isinstance(self, (CreateView, UpdateView)) or \
            popups['create'] or popups['update']:
            # Can't we load media of forms created using modelform_factory()?
            # Need to investigate.
            if self._viewset.form_class:
                popupcrud_media += self._viewset.form_class(
                    **self._viewset.get_form_kwargs()).media

            formset_class = self._viewset.formset_class
            if formset_class:
                popupcrud_media += forms.Media(js=('popupcrud/js/jquery.formset.js',))
                fs_media = formset_class().media
                popupcrud_media += fs_media

        return popupcrud_media


class ListView(AttributeThunk, PaginationMixin, PermissionRequiredMixin,
               generic.ListView):
    """ Model list view """

    def __init__(self, viewset_cls, *args, **kwargs):
        super(ListView, self).__init__(viewset_cls, *args, **kwargs)
        request = kwargs['request']
        self.params = dict(request.GET.items())
        self.query = request.GET.get(SEARCH_VAR, '')
        self.lookup_opts = self.model._meta

    def get_paginate_by(self, queryset):
        return self._viewset.get_paginate_by()

    def get_queryset(self):
        qs = super(ListView, self).get_queryset()
        qs = self._viewset.get_queryset(qs)

        # Apply any filters

        # Set ordering.
        ordering = self._get_ordering(self.request, qs)
        qs = qs.order_by(*ordering)

        # Apply search results

        return qs

    def get_template_names(self):
        templates = super(ListView, self).get_template_names()

        # if the viewset customized listview template, make sure that is
        # looked for first by putting its name in the front of the list
        if getattr(self._viewset, 'list_template', None):
            templates.insert(0, self._viewset.list_template)

        # make the default template of lower priority than the one
        # determined by default -- <model>_list.html
        templates.append("popupcrud/list.html")
        return templates

    def get_context_data(self, **kwargs):
        kwargs['pagetitle'] = self._viewset.get_page_title('list')
        context = super(ListView, self).get_context_data(**kwargs)
        context['model_options'] = self._viewset.model._meta
        context['new_button_text'] = ugettext("New {0}").format(
            self._viewset.model._meta.verbose_name)
        context['new_url'] = self._viewset.get_new_url()
        context['new_item_dialog_title'] = ugettext("New {0}").format(
            self.model._meta.verbose_name)
        context['edit_item_dialog_title'] = ugettext("Edit {0}").format(
            self.model._meta.verbose_name)
        context['legacy_crud'] = self._viewset.legacy_crud
        modal_sizes = copy.deepcopy(DEFAULT_MODAL_SIZES)
        modal_sizes.update(self._viewset.modal_sizes)
        context['modal_sizes'] = modal_sizes
        return context

    def _get_default_ordering(self):
        ordering = []
        if self._viewset.ordering:
            ordering = self._viewset.ordering
        elif self.lookup_opts.ordering:
            ordering = self.lookup_opts.ordering
        return ordering

    def get_ordering_field(self, field_name):
        """
        Returns the proper model field name corresponding to the given
        field_name to use for ordering. field_name may either be the name of a
        proper model field or the name of a method (on the admin or model) or a
        callable with the 'order_field' attribute. Returns None if no
        proper model field name can be matched.
        """
        try:
            field = self.lookup_opts.get_field(field_name)
            return field.name
        except FieldDoesNotExist:
            # See whether field_name is a name of a non-field
            # that allows sorting.
            if callable(field_name):
                attr = field_name
            elif hasattr(self._viewset, field_name):
                attr = getattr(self._viewset, field_name)
            else:
                attr = getattr(self.model, field_name)
            return getattr(attr, 'order_field', None)

    def _get_ordering(self, request, queryset):
        """
        Returns the list of ordering fields for the change list.
        First we check the get_ordering() method in model admin, then we check
        the object's default ordering. Then, any manually-specified ordering
        from the query string overrides anything. Finally, a deterministic
        order is guaranteed by ensuring the primary key is used as the last
        ordering field.
        """
        params = self.params
        ordering = list(self._get_default_ordering())
        if ORDER_VAR in params:
            # Clear ordering and used params
            ordering = []
            order_params = params[ORDER_VAR].split('.')
            for p in order_params:
                try:
                    _, pfx, idx = p.rpartition('-')
                    field_name = self._viewset.list_display[int(idx)]
                    order_field = self.get_ordering_field(field_name)
                    if not order_field:
                        continue  # No 'order_field', skip it
                    # reverse order if order_field has already "-" as prefix
                    if order_field.startswith('-') and pfx == "-":
                        ordering.append(order_field[1:])
                    else:
                        ordering.append(pfx + order_field)
                except (IndexError, ValueError):
                    continue  # Invalid ordering specified, skip it.

        # Add the given query's ordering fields, if any.
        ordering.extend(queryset.query.order_by)

        # Ensure that the primary key is systematically present in the list of
        # ordering fields so we can guarantee a deterministic order across all
        # database backends.
        pk_name = self.lookup_opts.pk.name
        if not (set(ordering) & {'pk', '-pk', pk_name, '-' + pk_name}):
            # The two sets do not intersect, meaning the pk isn't present. So
            # we add it.
            ordering.append('-pk')

        return ordering

    def get_ordering_field_columns(self):
        """
        Returns an OrderedDict of ordering field column numbers and asc/desc
        """

        # We must cope with more than one column having the same underlying sort
        # field, so we base things on column numbers.
        ordering = self._get_default_ordering()
        ordering_fields = OrderedDict()
        if ORDER_VAR not in self.params:
            # for ordering specified on ModelAdmin or model Meta, we don't know
            # the right column numbers absolutely, because there might be more
            # than one column associated with that ordering, so we guess.
            for field in ordering:
                if field.startswith('-'):
                    field = field[1:]
                    order_type = 'desc'
                else:
                    order_type = 'asc'
                for index, attr in enumerate(self._viewset.list_display):
                    if self.get_ordering_field(attr) == field:
                        ordering_fields[index] = order_type
                        break
        else:
            for p in self.params[ORDER_VAR].split('.'):
                _, pfx, idx = p.rpartition('-')
                try:
                    idx = int(idx)
                except ValueError:
                    continue  # skip it
                ordering_fields[idx] = 'desc' if pfx == '-' else 'asc'
        return ordering_fields

    def get_query_string(self, new_params=None, remove=None):
        if new_params is None:
            new_params = {}
        if remove is None:
            remove = []
        p = self.params.copy()
        for r in remove:
            for k in list(p):
                if k.startswith(r):
                    del p[k]
        for k, v in new_params.items():
            if v is None:
                if k in p:
                    del p[k]
            else:
                p[k] = v
        return '?%s' % urlencode(sorted(p.items()))

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        pk = request.POST.get('item', None)
        try:
            if action and pk:
                obj = self.model.objects.get(pk=pk)
                result = self._viewset.invoke_action(
                    self.request, int(action), obj)
                return JsonResponse({
                    'result': result[0],
                    'message': result[1]
                })

        except (ValueError, IndexError, ObjectDoesNotExist):
            pass

        return JsonResponse({
            'result': False,
            'message': "Invalid operation"
        })


class TemplateNameMixin(object):
    """
    Mixin adds the ViewSet attribute, set by 'popupcrud_template_name` view
    attribute value, as one of the templates to the list of templates to be
    looked up for rendering the view.

    And if the incoming request is an AJAX request, it replaces all the template
    filenames with '_inner' such that site common embellishments are removed
    while rendering the view content inside a modal popup. Of course it's assumed
    that the '_inner.html' template is written as a pure template, which doesn't
    derive from the site common base template.
    """
    def get_template_names(self):
        templates = super(TemplateNameMixin, self).get_template_names()

        # if the viewset customized listview template, make sure that is
        # looked for first by putting its name in the front of the list
        template_attr_name = getattr(self, "popupcrud_template_name", None)

        if hasattr(self._viewset, template_attr_name):
            templates.insert(0, getattr(self._viewset, template_attr_name))

        # make the default template of lower priority than the one
        # determined by default -- <model>_list.html
        templates.append(getattr(self, template_attr_name))

        if self.request.is_ajax():
            # If this is an AJAX request, replace all the template names with
            # their <template_name>_inner.html counterparts.
            # These 'inner' templates are expected to be a bare-bones templates,
            # sans the base template's site-common embellishments.
            for index, template in enumerate(templates):
                parts = template.split('.')
                templates[index] = "{0}_inner.{1}".format(parts[0], parts[1])

        return templates


class CreateView(AttributeThunk, TemplateNameMixin, AjaxObjectFormMixin,
                 PermissionRequiredMixin, generic.CreateView):

    popupcrud_template_name = "form_template"
    form_template = "popupcrud/form.html"

    def get_context_data(self, **kwargs):
        kwargs['pagetitle'] = self._viewset.get_page_title('create')
            #ugettext("New {0}").format(self._viewset.model._meta.verbose_name)
        kwargs['form_url'] = self._viewset.get_new_url()
        # formset = self._viewset.get_formset()
        # if formset:
        #     kwargs['formset'] = formset
        return super(CreateView, self).get_context_data(**kwargs)


class DetailView(AttributeThunk, TemplateNameMixin, PermissionRequiredMixin,
                 generic.DetailView):

    popupcrud_template_name = "detail_template"
    detail_template = "popupcrud/detail.html"

    def get_context_data(self, **kwargs):
        kwargs['pagetitle'] = self._viewset.get_page_title('detail', self.object)
            #six.text_type(self.object)
        # _("{0} - {1}").format(
        #     self._viewset.model._meta.verbose_name,
        #     six.text_type(self.object))
        return super(DetailView, self).get_context_data(**kwargs)


class UpdateView(AttributeThunk, TemplateNameMixin, AjaxObjectFormMixin,
                 PermissionRequiredMixin, generic.UpdateView):

    popupcrud_template_name = "form_template"
    form_template = "popupcrud/form.html"

    def get_context_data(self, **kwargs):
        kwargs['pagetitle'] = self._viewset.get_page_title('update', obj=self.object)
            #ugettext("Edit {0}").format(self._viewset.model._meta.verbose_name)
        kwargs['form_url'] = self._viewset.get_edit_url(self.object)
        return super(UpdateView, self).get_context_data(**kwargs)


class DeleteView(AttributeThunk, PermissionRequiredMixin, generic.DeleteView):

    template_name = "popupcrud/confirm_delete.html"

    def get_context_data(self, **kwargs):
        kwargs['pagetitle'] = self._viewset.get_page_title('delete', obj=self.object)
            #ugettext("Delete {0}").format(self._viewset.model._meta.verbose_name)
        kwargs['model_options'] = self._viewset.model._meta
        return super(DeleteView, self).get_context_data(**kwargs)

    def handle_no_permission(self):
        """
        Slightly different form of handling no_permission from Create/Update
        views. Delete ajax request expects a JSON response to its AJAX request
        and therefore we render the 403 template and return the rendered context
        as error message text.
        """
        if self.request.is_ajax():
            temp = loader.get_template("popupcrud/403.html")
            return JsonResponse({
                'result': False,
                'message': temp.render({}, self.request)
            })
        return super(DeleteView, self).handle_no_permission()

    def delete(self, request, *args, **kwargs):
        """ Override to return JSON success response for AJAX requests """
        retval = super(DeleteView, self).delete(request, *args, **kwargs)
        if self.request.is_ajax():
            return JsonResponse({
                'result': True,
                'message': ugettext("{0} {1} deleted").format(
                    self.model._meta.verbose_name,
                    str(self.object))
            })

        messages.info(self.request, ugettext("{0} {1} deleted").format(
            self._viewset.model._meta.verbose_name,
            str(self.object)))
        return retval


class PopupCrudViewSet(object):
    """
    This is the base class from which you derive a class in your project
    for each model that you need to build CRUD views for.
    """

    _urls = None    # urls cache, so that we don't build it for every request

    #: The model to build CRUD views for. This is a required attribute.
    model = None

    #: URL to the create view for creating a new object. This is a required
    #: attribute.
    new_url = None

    #: Lists the fields to be displayed in the list view columns. This attribute
    #: is modelled after ModelAdmin.list_display and supports model methods as
    #: as ViewSet methods much like ModelAdmin. This is a required attribute.
    #:
    #: So you have four possible values that can be used in list_display:
    #:
    #:  - A field of the model
    #:  - A callable that accepts one parameter for the model instance.
    #:  - A string representing an attribute on ViewSet class.
    #:  - A string representing an attribute on the model
    #:
    #: See ModelAdmin.list_display `documentation
    #: <https://docs.djangoproject.com/en/1.11/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_display>`_
    #: for examples.
    #:
    #: A note about ``list_display`` fields with respect to how it differs from
    #: ``ModelAdmin``'s ``list_display``.
    #:
    #: In ``ModelAdmin``, if a field specified in ``list_display`` is not
    #: a database field, it can be set as a sortable field by setting
    #: the method's ``admin_order_field`` attribute to the relevant database
    #: field that can be used as the sort field. In ``PopupCrudViewSet``, this
    #: attribute is named ``order_Field``.
    list_display = ()

    #: A list of names of fields. This is interpreted the same as the Meta.fields
    #: attribute of ModelForm. This is a required attribute.
    fields = ()

    #: The form class to instantiate for Create and Update views. This is optional
    #: and if not specified a ModelForm using the values of fields attribute will
    #: be instantiated. An optional attribute, if specified, overrides fields
    #: attribute value.
    form_class = None

    #: The url where the list view is rooted. This will be used as the success_url
    #: attribute value for the individual CRUD views. This is a required attribute.
    list_url = None

    #: Number of entries per page in list view. Defaults to 10. Setting this
    #: to None will disable pagination. This is an optional attribute.
    paginate_by = POPUPCRUD['paginate_by'] #10 # turn on pagination by default

    #: List of permission names for the list view. Permission names are of the
    #: same format as what is specified in ``permission_required()`` decorator.
    #: Defaults to no permissions, meaning no permission is required.
    #:
    #: Depracated. Use :ref:`permissions_required <permissions_required>` dictionary instead.
    list_permission_required = ()

    #: List of permission names for the create view.
    #: Defaults to no permissions, meaning no permission is required.
    #:
    #: Depracated. Use :ref:`permissions_required <permissions_required>` dictionary instead.
    create_permission_required = ()

    #: List of permission names for the detail view.
    #: Defaults to no permissions, meaning no permission is required.
    #:
    #: Depracated. Use :ref:`permissions_required <permissions_required>` dictionary instead.
    detail_permission_required = ()

    #: List of permission names for the update view.
    #: Defaults to no permissions, meaning no permission is required.
    #:
    #: Depracated. Use :ref:`permissions_required <permissions_required>` dictionary instead.
    update_permission_required = ()

    #: List of permission names for the delete view.
    #: Defaults to no permissions, meaning no permission is required.
    #:
    #: Depracated. Use :ref:`permissions_required <permissions_required>` dictionary instead.
    delete_permission_required = ()

    #: .. _permissions_required:
    #:
    #: Permissions table for the various CRUD views. Use this instead
    #: of list_permission_required, create_permission_required, etc.
    #: Entries in this table are indexed by the CRUD view code and its
    #: required permissions tuple. CRUD view codes are: 'list', 'create',
    #: 'detail', 'update' & 'delete'.
    #:
    #: Note that if both the legacy `<crud-op>_permission_required` and
    #: `permissons_required` are specified, `permissions_required`
    #: setting value takes effect.
    #:
    #: For example you can specify::
    #:
    #:  permissions_required = {
    #:      'list': ('library.list_author',),
    #:      'create': ('library.list_author',),
    #:      'detail': ('library.view_author',),
    #:      'update': ('library.update_author',),
    #:      'delete': ('library.delete_author',)
    #:  }
    #:
    permissions_required = {}

    #: The template file to use for list view. If not specified, defaults
    #: to the internal template.
    list_template = None

    # #: The template file to use for create view. If not specified, defaults
    # #: to the internal template.
    #create_template: template to use for create new object view
    #edit_template: template to use for editing an existing object view
    #detail_template: template to use for detail view
    #delete_template: template to use for delete view

    #: A table that maps foreign keys to its target model's
    #: ``PopupCrudViewSet.create()`` view url. This would result in the select box
    #: for the foreign key to display a 'New {model}' link at its bottom, which
    #: the user can click to add a new {model} object from another popup. The
    #: newly created {model} object will be added to the select's options and
    #: set as its selected option.
    #:
    #: Defaults to empty dict, meaning creation of target model objects, for the
    #: foreign keys of a model, from a popup is disabled.
    related_object_popups = {}

    #: Page title for the list view page.
    page_title = ''

    ordering = None

    #: Enables legacy CRUD views where each of the Create, Detail, Update &
    #: Delete views are performed from their own dedicated web views like Django
    #: admin (hence the term ``legacy_crud`` :-)).
    #:
    #: This property can accept either a boolean value, which in turn enables/
    #: disables the legacy mode for all the CRUD views or it can accept
    #: a dict of CRUD operation codes and its corresponding legacy mode
    #: specified as boolean value.
    #:
    #: This dict looks like::
    #:
    #:      legacy_crud = {
    #:          'create': False,
    #:          'detail': False,
    #:          'update': False,
    #:          'delete': False
    #:      }
    #:
    #: So by setting ``legacy_crud[detail] = True``, you can enable legacy style
    #: crud for the detail view whereas the rest of the CRUD operations are
    #: performed from a modal popup.
    #:
    #: In other words, ``legacy_crud`` boolean value results in a dict that
    #: consists of ``True`` or ``False`` values for all its keys, as the case
    #: may be.
    #:
    #: This defaults to ``False``, which translates into a dict consisting of
    #: ``False`` values for all its keys.
    legacy_crud = False

    #: Same as ``django.contrib.auth.mixins.AccessMixin`` ``login_url``, but
    #: applicable for all CRUD views.
    login_url = None

    #: Same as ``django.contrib.auth.mixins.AccessMixin`` ``raise_exception``,
    #: but applicable for all CRUD views.
    raise_exception = False

    popup_views = {
        'create': True,
        'detail': True,
        'update': True,
        'delete': True,
    }

    #: Icon to be displayed above the empty list state message. Defaults to
    #: None, which displays no icon. To specify an icon, set this property
    #: to the CSS class of the required icon.
    #:
    #: For example to use the glyphicon-book icon, set this property to::
    #:
    #:  empty_list_icon = 'glyphicon glyphicon-book'
    #:
    #: Icons displayed are enlarged to 5 times the standard font size.
    empty_list_icon = None

    #: Message to be displayed when list view contains no records, that is,
    #: empty list state. Defaults to 'No records found`.
    #:
    #: Empty list state rendering can be customized further by overriding
    #: ``popupcrud/empty_list.html`` template in your own project.
    empty_list_message = _('No records found.')

    #: List of breadcrumbs that will be added to ViewSet views' context,
    #: allowing you build a breadcrumb hierarchy that reflects the ViewSet's
    #: location in the site.
    #:
    #: Note that for ``legacy_crud`` views, system would add the ``list view``
    #: url to the breadcrumbs list.
    breadcrumbs = []

    #: The template context variable name that will be initialized with the
    #: value of ``breadcrumbs`` property. You can enumerate this variable in
    #: your base template to build a breadcrumbs list that reflects the
    #: hierarchy of the page.
    breadcrumbs_context_variable = 'breadcrumbs'

    #: Item actions are user specified actions to be performed on a row item in
    #: list view. Each item action is specified as a 3-tuple with the following
    #: attributes:

    #:     * its title
    #:     * its icon css such as ``glyphicon glyphicon-ok``
    #:     * its action handler, which is the name of the CrudViewSet method to
    #:       be called when user selects the action. This method has the
    #:       following signature::
    #:
    #:           def action_handler(self, request, item):
    #:               # action processing
    #:
    #:               return (True, "Action completed")
    #:
    #:       The return value from the action handler is a 2-tuple that
    #:       consists of a boolean success indicator and a message. The message
    #:       is displayed to the user when the action is completed.
    #:
    #: Also see ``get_item_actions()`` documentation below.
    item_actions = []

    #: .. _modal_sizes:
    #:
    #: Allows specifying the size of the modal windows used for the CRUD operations.
    #: Value is a dictionary, where the key names indicate the modal whose size
    #: you want to adjust. Allowed values for these are: ``create_update``,
    #: ``delete`` & ``detail``. Value for the keys indicate the size of the
    #: modal and has to be one of: ``{small|normal|large}``.
    #:
    #: Defaults to::
    #:
    #:      modal_sizes = {
    #:          'create_update': 'normal',
    #:          'delete': 'normal',
    #:          'detail': 'normal'
    #:      }
    #:
    #: You only need to specify the modal whose size you want to adjust. So if
    #: you want to adjust the size of the ``create_update`` modal to large while
    #: leaving the rest to their default size, you may specify modal_sizes as::
    #:
    #:      modal_sizes = {
    #:          'create_update': 'large',
    #:      }
    modal_sizes = {}

    #: If specified, the name of the context variable that will be used to
    #: assign the object instance value. By default the context variable
    #: ``object`` will be assigned the object instance. If
    #: ``context_object_name`` is specified, that too will be assigned the
    #: object instance.
    context_object_name = None

    #: Same as `SingleObjectMixin.pk_url_kwarg
    #: <https://docs.djangoproject.com/en/1.11/ref/class-based-views/mixins-single-object/#django.views.generic.detail.SingleObjectMixin.pk_url_kwarg>`_,
    #: which is the name
    #: of the URLConf keyword argument that contains the primary key. By
    #: default, ``pk_url_kwarg`` is `pk``.
    pk_url_kwarg = 'pk'

    #: Same as `SingleObjectMixin.slug_field
    #: <https://docs.djangoproject.com/en/1.11/ref/class-based-views/mixins-single-object/#django.views.generic.detail.SingleObjectMixin.slug_field>`_,
    #: which is the name of the field
    #: on the model that contains the slug. By default, ``slug_field`` is
    #: ``slug``.
    #:
    #: To use ``slug_field`` as the key to access object instances
    #: (for detail, update & delete views), set ``pk_url_kwarg = None`` in the
    #: ViewSet class and initialize ``slug_field`` and ``slug_url_kwarg`` to the
    #: relevant slug field's name & its corresponding URLconf parameter name
    #: respectively.
    slug_field = 'slug'

    #: Same as `SingleObjectMixin.slug_url_kwarg
    #: <https://docs.djangoproject.com/en/1.11/ref/class-based-views/mixins-single-object/#django.views.generic.detail.SingleObjectMixin.slug_url_kwarg>`_,
    #: which is the name of the
    #: URLConf keyword argument that contains the slug. By default,
    #: ``slug_url_kwarg`` is ``slug``.
    slug_url_kwarg = 'slug'

    @classonlymethod
    def _generate_view(cls, crud_view_class, **initkwargs):
        """
        A closure that generates the view function by instantiating the view
        class specified in argument 2. This is a generalized function that is
        used by the four CRUD methods (list, create, read, update & delete) to
        generate their individual Django CBV based view instances.

        Returns the thus generated view function which can be used in url()
        function as second argument.

        Code is mostly extracted from django CBV View.as_view(), removing the
        update_wrapper() calls at the end.
        """
        def view(request, *args, **kwargs):
            initkwargs['request'] = request
            view = crud_view_class(cls, **initkwargs)
            if hasattr(view, 'get') and not hasattr(view, 'head'):
                view.head = view.get
            view.request = request
            view.args = args
            view.kwargs = kwargs
            return view.dispatch(request, *args, **kwargs)

        view.view_class = crud_view_class
        view.view_initkwargs = initkwargs

        # take name and docstring from class
        #update_wrapper(view, crud_view_class, updated=())

        # and possible attributes set by decorators
        # like csrf_exempt from dispatch
        #update_wrapper(view, crud_view_class.dispatch, assigned=())
        return view

    def __init__(self, *args, **kwargs):
        self.view = None

    @classonlymethod
    def list(cls, **initkwargs):
        """Returns the list view that can be specified as the second argument
        to url() in urls.py.
        """
        return cls._generate_view(ListView, **initkwargs)

    @classonlymethod
    def create(cls, **initkwargs):
        """Returns the create view that can be specified as the second argument
        to url() in urls.py.
        """
        return cls._generate_view(CreateView, **initkwargs)

    @classonlymethod
    def detail(cls, **initkwargs):
        """Returns the create view that can be specified as the second argument
        to url() in urls.py.
        """
        return cls._generate_view(DetailView, **initkwargs)

    @classonlymethod
    def update(cls, **initkwargs):
        """Returns the update view that can be specified as the second argument
        to url() in urls.py.
        """
        return cls._generate_view(UpdateView, **initkwargs)

    @classonlymethod
    def delete(cls, **initkwargs):
        """Returns the delete view that can be specified as the second argument
        to url() in urls.py.
        """
        return cls._generate_view(DeleteView, **initkwargs)

    def get_list_url(self):
        return self.list_url

    def get_new_url(self):
        """ Returns the URL to create a new model object. Returning None would
        disable the new object creation feature and will hide the ``New {model}``
        button.

        You may override this to dynamically determine if new object creation
        ought to be allowed. Default implementation returns the value of
        ``ViewSet.new_url``.
        """
        return self.new_url

    def get_detail_url(self, obj):
        """ Override this returning the URL where ``PopupCrudViewSet.detail()``
        is placed in the URL namespace such that ViewSet can generate the
        appropriate href to display item detail in list view.

        When this hyperlink is clicked, a popup containing the
        object's detail will be shown. By default this popup only shows the
        object's string representation. To show additional information in this
        popup, implement ``<object>_detail.html`` in your project, typically in
        the app's template folder. If this file exists, it will be used to
        render the object detail popup. True to Django's ``DetailView``
        convention, you may use the ``{{ object }}`` template variable in the
        template file to access the object and its properties.

        Default implementations returns None, which results in object detail
        popup being disabled.
        """
        return None

    def get_edit_url(self, obj):
        """ Override this returning the URL where PopupCrudViewSet.update() is
        placed in the URL namespace such that ViewSet can generate the
        appropriate href to the item edit hyperlink in list view.

        If None is returned, link to edit the specified item won't be
        shown in the object row.
        """
        return "#"

    def get_delete_url(self, obj):
        """ Override this returning the URL where PopupCrudViewSet.delete() is
        placed in the URL namespace such that ViewSet can generate the
        appropriate href to the item delete hyperlink in list view.

        If None is returned, link to delete the specified item won't be
        shown in the object row.
        """
        return "#"

    def get_obj_name(self, obj):
        """ Return the name of the object that will be displayed in item
        action prompts for confirmation. Defaults to ``str(obj)``, ie., the
        string representation of the object. Override this to provide the user
        with additional object details. The returned string may contain
        embedded HTML tags.

        For example, you might want to display the balance due from a customer
        when confirming user action to delete the customer record.
        """
        return six.text_type(obj)

    def get_permission_required(self, op):
        """
        Return the permission required for the CRUD operation specified in op.
        Default implementation returns the value of one
        ``{list|create|detail|update|delete}_permission_required`` class attributes.
        Overriding this allows you to return dynamically computed permissions.

        :param op: The CRUD operation code. One of
            ``{'list'|'create'|'detail'|'update'|'delete'}``.

        :rtype:
            The ``permission_required`` tuple for the specified operation.
            Determined by looking up the given ``op`` from the table::

                permission_table = {
                    'list': self.list_permission_required,
                    'create': self.create_permission_required,
                    'detail': self.detail_permission_required,
                    'update': self.update_permission_required,
                    'delete': self.delete_permission_required
                }
        """
        permission_table = {
            'list': self.list_permission_required,
            'create': self.create_permission_required,
            'detail': self.detail_permission_required,
            'update': self.update_permission_required,
            'delete': self.delete_permission_required
        }

        # Update with self.permissions_required dict values
        permission_table.update(self.permissions_required)

        return permission_table[op]

    def get_page_title(self, view, obj=None):
        """
        Returns page title for the CRUD view. Parameter `view`
        specifies the CRUD view whose page title is being queried
        and is one of `create`, `detail`, `update`, `delete` or `list`.

        For `detail`, `update` & `delete` views, the model instance is
        is passed as second argument. For the rest of the views, this
        is set to `None`.
        """
        if view == 'create':
            return ugettext("New {0}").format(
                self.model._meta.verbose_name)
        elif view == 'update':
            return ugettext("Edit {0}").format(
                self.model._meta.verbose_name)
        elif view == 'detail':
            return ugettext("{0} Details").format(
                self.model._meta.verbose_name)
        elif view == 'delete':
            return ugettext("Delete {0}").format(
                self.model._meta.verbose_name)

        # list view
        return self.page_title if self.page_title else \
                self.model._meta.verbose_name_plural

    def get_paginate_by(self):
        #: Returns the number of items to paginate by, or None for no
        #: pagination. By default this simply returns the value of
        #: ``paginate_by``.
        return self.paginate_by

    @classonlymethod
    def urls(cls, namespace=None, views=('create', 'update', 'delete', 'detail')):
        """
        Returns the CRUD urls for the viewset that can be added to the URLconf.
        The URLs returned can be controlled by the ``views`` parameter which
        is tuple of strings specifying the CRUD operations URLs to be returned.
        This defaults to all the CRUD operations: create, read(detail),
        update & delete (List view URL is added by default).

        This method can be seen as a wrapper to calling the individual view
        generator methods, ``list()``, ``detail()``, ``create()``, ``update()``
        & ``delete()``, to register them with the URLconf.

        The urls for CRUD actions involving a single object (detail, update
        & delete) are by default composed using ``pk`` as URLConf keyword
        argument. However, if ``pk_url_kwarg`` is set to None and ``slug_field``
        and ``slug_url_kwarg`` are initialized, it will be based as the field
        used to locate the individual object and URLConf keyword argument
        respectively.

        :param namespace: The namespace under which the CRUD urls are registered.
            Defaults to the value of ``<model>.Meta.verbose_name_plural`` (in
            lowercase and in English).
        :param views: A tuple of strings representing the CRUD views whose URL
            patterns are to be registered. Defaults to ``('create', 'update',
            'delete', 'detail')``, that is all the CRUD operations for the model.

        :rtype:
            A collection of URLs, packaged using ``django.conf.urls.include()``,
            that can be used as argument 2 to ``url()`` (see example below).

        :example:
            The following pattern registers all the CRUD urls
            for model Book (in app ``library``), generated by BooksCrudViewSet::

                urlpatterns += [
                    url(r'^books/', BooksCrudViewSet.urls())
                ]

            This allows us to refer to individual CRUD operation url as::

                reverse("library:books:list")
                reverse("library:books:create")
                reverse("library:books:detail", kwargs={'pk': book.pk})
                reverse("library:books:update", kwargs={'pk': book.pk})
                reverse("library:books:delete", kwargs={'pk': book.pk})

        """
        if not cls._urls:
            if not namespace:
                with override('en'): # force URLs to be in English even when
                                     # default language is set to something else
                    namespace = cls.model._meta.verbose_name_plural.lower()

            # start with only list url, the rest are optional based on views arg
            urls = [url(r'$', cls.list(), name='list')]

            obj_url_pattern = r'(?P<%s>\w+)' % (cls.pk_url_kwarg \
                if cls.pk_url_kwarg else cls.slug_url_kwarg)

            if 'detail' in views:
                urls.insert(0, url(r'^%s/$' % obj_url_pattern, cls.detail(), name='detail'))

            if 'delete' in views:
                urls.insert(0, url(r'^%s/delete/$' % obj_url_pattern, cls.delete(), name='delete'))

            if 'update' in views:
                urls.insert(0, url(r'^%s/update/$' % obj_url_pattern, cls.update(), name='update'))

            if 'create' in views:
                urls.insert(0, url(r'^create/$', cls.create(), name='create'))

            cls._urls = include((urls, namespace), namespace)

        return cls._urls

    @property
    def popups(self):
        """
        Provides a normalized dict of crud view types to use for the viewset
        depending on client.legacy_crud setting.

        Computes this dict only once per object as an optimization.
        """
        if not hasattr(self, '_popups'):
            popups_enabled = {
                'detail': True, 'create': True, 'update': True, 'delete': True
            }
            if isinstance(self.legacy_crud, dict):
                _popups = popups_enabled
                for k, v in self.legacy_crud.items(): # pylint: disable=E1101
                    _popups[k] = False if v else True
            else:
                popups_disabled = popups_enabled.copy()
                for k, v in popups_disabled.items():
                    popups_disabled[k] = False
                _popups = popups_disabled if self.legacy_crud else popups_enabled
            self._popups = _popups  # pylint: disable=W0201

        return self._popups

    def get_empty_list_icon(self):
        """
        Determine the icon used to display empty list state.

        Returns the value of ``empty_list_icon`` property by default.
        """
        return self.empty_list_icon

    def get_empty_list_message(self):
        """
        Determine the message used to display empty table state.

        Returns the value of ``empty_list_message`` property by default.
        """
        return mark_safe(self.empty_list_message)

    def get_breadcrumbs(self):
        """
        Returns the value of ``ViewSet.breadcrumbs`` property. You can use this
        method to return breadcrumbs that contain runtime computed values.
        """
        return self.breadcrumbs

    def get_queryset(self, qs):
        """
        Called by ListView allowing ViewSet to do further filtering of the
        queryset, if necessary. By default returns the queryset argument
        unchanged.

        :param qs: Queryset that is used for rendering ListView content.

        :rtype: A valid Django queryset.
        """
        return qs

    def get_form_kwargs(self):
        """
        For Create and Update views, this method allows passing custom arguments
        to the form class constructor. The return value from this method is
        combined with the default form constructor ``**kwargs`` before it is
        passed to the form class' ``__init__()`` routine's ``**kwargs``.

        Since Django CBVs use kwargs ``initial`` & ``instance``, be careful
        when using these, unless of course, you want to override the objects
        provided by these keys.
        """
        return {}

    @cached_property
    def formset_class(self):
        return self.get_formset_class()

    def get_formset_class(self):
        """
        Return the formset class to the child model of this parent model
        allowing create/edit of multiple objects of the child model.

        Typically, though not required, the return value will be a class
        generated by the django formset factory function `inlineformset_factory()
        <https://docs.djangoproject.com/en/1.11/ref/forms/models/#django.contrib.admin.inlineformset_factory>`_.

        By default, this method returns None, which indicates that the model
        Create/Edit forms do not have a formset for a child model.
        """
        return None

    def get_formset(self):
        """
        Returns the formset object instantiated from the class returned by
        the get_formset_class() method.

        By default returns None indicating no formset is associated with the model.
        """
        formset_class = self.formset_class
        if formset_class:
            return formset_class(**self.view.get_form_kwargs()) # pylint: disable=E1102
        return None

    def get_item_actions(self, obj):
        """
        Determine the custom actions for the given model object that
        is displayed after the standard Edit & Delete actions in list view.

        :param obj: The row object for which actions are being queried.

        :rtype: A list of action 3-tuple (as explained in ``item_actions``)
                objects relevant for the given object. If no actions are to be
                presented for the object, an empty list(``[]``) can be
                returned.

        Default implementation returns the value of ``item_actions`` class
        variable.

        Since this method is called once for each row item, you can customize the
        actions that is presented for each object. You can also altogether turn
        off all actions for an object by returning an empty list(``[]``).
        """
        return self.item_actions

    def invoke_action(self, request, index, item):
        """
        Invokes the custom action specified by the index.

        Parameters:
            request - HttpRequest object
            index - the index of the action into get_item_actions() list
            item_or_list - the item upon which action is to be performed

        Return:
            Action result as a 2-tuple: (bool, message)

        Raises:
            Index error if the action index specified is outside the scope
            of the array returned by get_item_actions().
        """
        actions = self.get_item_actions(item)
        if index >= len(actions):
            raise IndexError

        action = actions[index][2]  # method to invoke
        action_method = getattr(self, action)
        if callable(action_method):
            return action_method(request, item)

        return (False, ugettext("Action failed"))

    def get_context_data(self, kwargs):
        """
        Called for every CRUD view's get_context_data() method, this method
        allows additional data to be added to the CRUD view's template context.

        :param kwargs: The kwargs dictionary that is the usual argument to
            View.get_context_data()

        :rtype: None

        If you want to add context data for a specific CRUD view, you can
        achieve this by checking the view object's class type. For example the
        following code adds context data only for DetailView::

            if isinstance(self.view, DetailView):
                obj = kwargs['object']
                kwargs['user_fullname'] = obj.user.first_name + ' ' + obj.user.last_name
        """
        pass
