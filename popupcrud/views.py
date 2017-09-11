# -*- coding: utf-8 -*-
""" Popupcrud views """

from functools import update_wrapper

from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render_to_response
from django.utils.decorators import classonlymethod
from django.utils.translation import ugettext_lazy as _, ugettext
from django.views import generic
from django.http import JsonResponse
from django.template import loader
from django.contrib.auth.mixins import PermissionRequiredMixin

from pure_pagination import PaginationMixin

class AjaxObjectFormMixin(object):
    """
    Mixin facilitates single object create/edit/delete functions to be
    performed through an AJAX request.

    Views that provide the feature of creating/editing the model objects (that
    they represent) via AJAX requests should derive from this class.

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
            'name': unicode(self.object), # object representation
            'pk': self.object.pk          # object id
        })

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
    Class thunks the various attributes expected by Django generic
    CRUD views as properties of the parent viewset class instance, which is
    passed as constructur argument.
    """
    def __init__(self, viewset, *args, **kwargs):
        self._viewset = viewset()   # Sat 9/9, changed to store Viewset object
                                    # instead of viewset class
        super(AttributeThunk, self).__init__(*args, **kwargs)

    @property
    def model(self):
        return self._viewset.model

    @property
    def fields(self):
        return self._viewset.fields

    @property
    def success_url(self):
        return self._viewset.list_url


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
        if hasattr(self._viewset, 'list_template'):
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
        context['edit_url'] = getattr(self._viewset, 'edit_url', None)
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

    def get_form_class(self):
        if hasattr(self._viewset, 'form_class'):
            return self._viewset.form_class
        return super(CreateView, self).get_form_class()


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

    def get_form_class(self):
        if hasattr(self._viewset, 'form_class'):
            return self._viewset.form_class
        return super(CreateView, self).get_form_class()


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
                    unicode(self.object))
            })
        else:
            return retval

    def get_permission_required(self):
        return self._viewset.get_permission_required('delete')


class PopupCrudViewSet(object):
    """
    Base class to create CRUD views for a model.

    To use:

    1. Instantiate a child class of this for your model for which you wish
    to build crud views.

    2. Provide the following in the derived class:

        Required:

            Properties:
                model: model name to provide crud views for
                list_display: fields to be included in the list view columns (a la
                    ModelAdmin.list_display, though not supporting all its flavors)
                fields: fields to be included in the form
                list_url: the list view url to redirect to after a successful
                    add/edit/delete operation.
                new_url: URL to the CRUD create view for creating a new object.

            Methods:
                get_edit_url(obj): staticmethod. Return the url to the edit
                    object view.
                get_delete_url: staticmethod. Return the url to the CRUD delete
                    object view. Object is deleted using AJAX after user
                    confirmation which is displayed as a popup.

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
    # model = None
    # fields = ()
    # form_class = None
    # list_url = None
    paginate_by = 10 # turn on pagination by default
    list_permission_required = ()
    create_permission_required = ()
    read_permission_required = ()
    update_permission_required = ()
    delete_permission_required = ()

    @classonlymethod
    def generate_view(cls, crud_view_class, **initkwargs):
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

    @classonlymethod
    def list(cls, **initkwargs):
        return cls.generate_view(ListView, **initkwargs)

    @classonlymethod
    def create(cls, **initkwargs):
        return cls.generate_view(CreateView, **initkwargs)

    @classonlymethod
    def read(cls, **initkwargs):
        return cls.generate_view(DetailView, **initkwargs)

    @classonlymethod
    def update(cls, **initkwargs):
        return cls.generate_view(UpdateView, **initkwargs)

    @classonlymethod
    def delete(cls, **initkwargs):
        return cls.generate_view(DeleteView, **initkwargs)

    def get_detail_url(self, obj):
        return None

    def get_edit_url(self, obj):
        return "#"

    def get_delete_url(self, obj):
        return "#"

    def get_permission_required(self, op):
        """
        Return the permission required for the CRUD operation specified in op.

        Parameters:
            op: {'list'|'create'|'read'|'update'|'delete'}, where

                'list':= PopupCrudViewSet.list()
                'create':= PopupCrudViewSet.create()
                'read':= PopupCrudViewSet.detail()
                'update':= PopupCrudViewSet.update()
                'delete':= PopupCrudViewSet.delete()

        Return:
            The permission_required tuple for the specified operation

        Remarks:
            Default implementation returns an empty tuple, meaning that
            none of the views require any permissions.
        """
        permission_table = {
            'list': self.list_permission_required,
            'create': self.create_permission_required,
            'read': self.read_permission_required,
            'update': self.update_permission_required,
            'delete': self.delete_permission_required
        }
        return permission_table[op]
