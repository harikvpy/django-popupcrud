# -*- coding: utf-8 -*-
""" Popupcrud views """

from functools import update_wrapper

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render_to_response
from django.utils.decorators import classonlymethod
from django.utils.translation import ugettext_lazy as _, ugettext
from django.views import generic
from django.http import JsonResponse
from django.template import loader
from django.contrib.auth.mixins import PermissionRequiredMixin
from django import forms

from pure_pagination import PaginationMixin

from .widgets import RelatedFieldPopupFormWidget


# default settings
POPUPCRUD_DEFAULTS = {
    'base_template': 'base.html'
}

# build effective settings by merging any user settings with defaults
POPUPCRUD = POPUPCRUD_DEFAULTS.copy()
POPUPCRUD.update(getattr(settings, 'POPUPCRUD', {}))

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
    _supports_ajax_object_op = False

    def dispatch(self, request, *args, **kwargs): # pylint: disable=missing-docstring
        if request.is_ajax():
            if not hasattr(self, 'ajax_template_name'):
                self.ajax_template_name = "popupcrud/form_inner.html"
            self.template_name = self.ajax_template_name
            self._supports_ajax_object_op = True

        return super(AjaxObjectFormMixin, self).dispatch(request, *args, **kwargs)

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
        related_popups  = getattr(self._viewset, 'related_object_popups', {})
        for fname in related_popups:
            if fname in form.fields:
                field = form.fields[fname]
                if isinstance(form.fields[fname], forms.ModelChoiceField):
                    form.fields[fname].widget = RelatedFieldPopupFormWidget(
                        widget=forms.Select(choices=form.fields[fname].choices),
                        new_url=related_popups[fname])

    def form_valid(self, form): # pylint: disable=missing-docstring
        retval = super(AjaxObjectFormMixin, self).form_valid(form)
        if self.request.is_ajax() and self._supports_ajax_object_op:
            return self.get_ajax_response()
        return retval

    def handle_no_permission(self):
        if self.request.is_ajax():
            return render_to_response('popupcrud/403.html')
        super(AjaxObjectFormMixin, self).handle_no_permission()


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

    def get_success_url(self):
        return self._viewset.list_url

    def get_context_data(self, **kwargs):
        kwargs['base_template'] = POPUPCRUD['base_template']
        return super(AttributeThunk, self).get_context_data(**kwargs)


class ListView(AttributeThunk, PaginationMixin, PermissionRequiredMixin,
               generic.ListView):
    """ Model list view """

    def __init__(self, viewset_cls, *args, **kwargs):
        super(ListView, self).__init__(viewset_cls, *args, **kwargs)

    def get_paginate_by(self, queryset):
        return self._viewset.paginate_by

    def get_queryset(self):
        qs = super(ListView, self).get_queryset()
        # TODO: 2017年09月06日 (週三) 06時13分10秒
        #		Apply custom ordering based on GET arguments
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

    def get_permission_required(self):
        return self._viewset.get_permission_required('list')

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['model_options'] = self._viewset.model._meta
        context['new_button_text'] = ugettext("New {0}").format(
            self._viewset.model._meta.verbose_name)
        context['new_url'] = getattr(self._viewset, 'new_url', None)
        context['new_item_dialog_title'] = ugettext("New {0}").format(
            self.model._meta.verbose_name)
        context['edit_item_dialog_title'] = ugettext("Edit {0}").format(
            self.model._meta.verbose_name)
        return context


class TemplateNameMixin(object):
    """
    Add popupcrud/form.html as a secondary choice template to the template
    name list
    """
    def get_template_names(self):
        templates = super(TemplateNameMixin, self).get_template_names()

        # if the viewset customized listview template, make sure that is
        # looked for first by putting its name in the front of the list
        template_attr_name = getattr(self, "popupcrud_template_name")

        if hasattr(self._viewset, template_attr_name):
            templates.insert(0, getattr(self._viewset, template_attr_name))

        # make the default template of lower priority than the one
        # determined by default -- <model>_list.html
        templates.append(getattr(self, template_attr_name))
        return templates


class CreateView(AttributeThunk, TemplateNameMixin, AjaxObjectFormMixin,
                 PermissionRequiredMixin, generic.CreateView):

    popupcrud_template_name = "form_template"
    form_template = "popupcrud/form.html"

    def __init__(self, viewset_cls, *args, **kwargs):
        super(CreateView, self).__init__(viewset_cls, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['pagetitle'] = ugettext("New {0}").format(self._viewset.model._meta.verbose_name)
        kwargs['form_url'] = self._viewset.new_url
        return super(CreateView, self).get_context_data(**kwargs)

    def get_permission_required(self):
        return self._viewset.get_permission_required('create')

    # def get_form_class(self):
    #     if getattr(self._viewset, 'form_class', None):
    #         return self._viewset.form_class
    #     return super(CreateView, self).get_form_class()


class DetailView(AttributeThunk, PermissionRequiredMixin, generic.DetailView):
    def __init__(self, viewset_cls, *args, **kwargs):
        super(DetailView, self).__init__(viewset_cls, *args, **kwargs)

    def get_permission_required(self):
        return self._viewset.get_permission_required('read')


class UpdateView(AttributeThunk, TemplateNameMixin, AjaxObjectFormMixin,
                 PermissionRequiredMixin, generic.UpdateView):

    popupcrud_template_name = "form_template"
    form_template = "popupcrud/form.html"

    def __init__(self, viewset_cls, *args, **kwargs):
        super(UpdateView, self).__init__(viewset_cls, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['pagetitle'] = _("Edit {0}").format(self._viewset.model._meta.verbose_name)
        kwargs['form_url'] = self._viewset.get_edit_url(self.object)
        return super(UpdateView, self).get_context_data(**kwargs)

    def get_permission_required(self):
        return self._viewset.get_permission_required('update')

    # def get_form_class(self):
    #     if getattr(self._viewset, 'form_class', None):
    #         return self._viewset.form_class
    #     return super(UpdateView, self).get_form_class()


class DeleteView(AttributeThunk, PermissionRequiredMixin, generic.DeleteView):

    def __init__(self, viewset_cls, *args, **kwargs):
        super(DeleteView, self).__init__(viewset_cls, *args, **kwargs)

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
        super(AjaxObjectFormMixin, self).handle_no_permission()

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
        else:
            return retval

    def get_permission_required(self):
        return self._viewset.get_permission_required('delete')


class PopupCrudViewSet(object):
    """
    This is the base class from which you derive a class in your project
    for each model that you need to build CRUD views for.
    """

    """
        Optional:

            Class Properties:
                list_template: the template file to use for list view
                create_template: template to use for create new object view
                edit_template: template to use for editing an existing object view
                detail_template: template to use for detail view
                delete_template: template to use for delete view

            Methods:
                get_detail_url: staticmetod. Return the url to the object's

                    detail view. Default implementation in base class returns
                    None, which disables the object detail view.

    3. Connect the five different methods to the url resolver. For example:

        MyModelViewset(PopupCrudViewSet):
            model = MyModel
            ...

        urlpatterns = [
            url(r'mymodel/$', MyModelViewset.list(), name='mymodels-list'),
            url(r'mymodel/new/$', MyModelViewset.create(), name='new-mymodel'),
            url(r'mymodel/(?P<pk>\d+)/$', MyModelViewset.detail(), name='mymodel-detail'),
            url(r'mymodel/(?P<pk>\d+)/edit/$', MyModelViewset.update(), name='edit-mymodel'),
            url(r'mymodel/(?P<pk>\d+)/delete/$', MyModelViewset.delete(), name='delete-mymodel'),
            ]
    """

    #: The model to build CRUD views for. This is a required attribute.
    model = None

    #: URL to the create view for creating a new object. This is a required
    #: attribute.
    new_url = None

    #: Lists the fields to be displayed in the list view columns. This attribute
    #: is modelled after ModelAdmin.list_display and supports model methods as
    #: as ViewSet methods much like ModelAdmin. This is a required attribute.
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
    paginate_by = 10 # turn on pagination by default

    #: List of permission names for the list view. Permission names are of the
    #: same format as what is specified in `permission_required()` decorator.
    #: Defaults to no permissions, meaning no permission is required.
    list_permission_required = ()

    #: List of permission names for the create view.
    #: Defaults to no permissions, meaning no permission is required.
    create_permission_required = ()

    #: List of permission names for the detail view.
    #: Defaults to no permissions, meaning no permission is required.
    read_permission_required = ()

    #: List of permission names for the update view.
    #: Defaults to no permissions, meaning no permission is required.
    update_permission_required = ()

    #: List of permission names for the delete view.
    #: Defaults to no permissions, meaning no permission is required.
    delete_permission_required = ()

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
    #: `PopupCrudViewSet.create()` view url. This would result in the select box
    #: for the foreign key to display a 'New {model}' link at its bottom, which
    #: the user can click to add a new {model} object from another popup. The
    #: newly created {model} object will be added to the select's options and
    #: set as its selected option.
    #:
    #: Defaults to empty dict, meaning creation of target model objects, for the
    #: foreign keys of a model, from a popup is disabled.
    related_object_popups = {}

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
    def read(cls, **initkwargs):
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

    def get_detail_url(self, obj):
        """ Override this returning the URL where PopupCrudViewSet.detail() is
        placed in the URL namespace such that ViewSet can generate the
        appropriate href to the item detail hyperlink in list view.
        argument.
        """
        return None

    def get_edit_url(self, obj):
        """ Override this returning the URL where PopupCrudViewSet.update() is
        placed in the URL namespace such that ViewSet can generate the
        appropriate href to the item edit hyperlink in list view.
        """
        return "#"

    def get_delete_url(self, obj):
        """ Override this returning the URL where PopupCrudViewSet.delete() is
        placed in the URL namespace such that ViewSet can generate the
        appropriate href to the item delete hyperlink in list view.
        """
        return "#"

    def get_permission_required(self, op):
        """
        Return the permission required for the CRUD operation specified in op.
        Default implementation returns the value of one
        `{list|create|read|update|delete}_permission_required` class attributes.
        Overriding this allows you to return dynamically computed permissions.

        :param op: The CRUD operation code. One of
            `{'list'|'create'|'read'|'update'|'delete'}`.

        :rtype:
            The `permission_required` tuple for the specified operation.
            Determined by looking up the given `op` from the table::

                permission_table = {
                    'list': self.list_permission_required,
                    'create': self.create_permission_required,
                    'read': self.read_permission_required,
                    'update': self.update_permission_required,
                    'delete': self.delete_permission_required
                }
        """
        permission_table = {
            'list': self.list_permission_required,
            'create': self.create_permission_required,
            'read': self.read_permission_required,
            'update': self.update_permission_required,
            'delete': self.delete_permission_required
        }
        return permission_table[op]
