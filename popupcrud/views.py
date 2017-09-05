# -*- coding: utf-8 -*-
""" Popupcrud views """

from functools import update_wrapper

from django.core.exceptions import ImproperlyConfigured
from django.utils.decorators import classonlymethod
from django.views import generic


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
        if request.is_ajax() and getattr(self, 'template_name', None):
            if not hasattr(self, 'ajax_template_name'):
                split = self.template_name.split('.html')
                split[-1] = '_inner'
                split.append('.html')
                self.ajax_template_name = ''.join(split)
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


class AttributeThunk(object):
    """
    Class thunks the various attributes expected by Django generic
    CRUD views as properties of the parent viewset class instance, which is
    passed as constructur argument.
    """
    def __init__(self, viewset, *args, **kwargs):
        self._viewset = viewset
        super(AttributeThunk, self).__init__(*args, **kwargs)

    @property
    def model(self):
        return self._viewset.model

    @property
    def fields(self):
        return self._viewset.fields

    @property
    def success_url(self):
        return self._viewset.success_url


# Individual CRUD views are based on Django CBVs with custom constructor
# to supply the viewset class as argument. This viewset class argument is
# used to retrieve the class.model, class.fields, class.success_url, etc.
# properties from it so that the user needs to define this only once
# for each viewset.

class ListView(AttributeThunk, generic.ListView):
    def __init__(self, viewset_cls, *args, **kwargs):
        super(ListView, self).__init__(viewset_cls, *args, **kwargs)


class CreateView(AttributeThunk, AjaxObjectFormMixin, generic.CreateView):
    def __init__(self, viewset_cls, *args, **kwargs):
        super(CreateView, self).__init__(viewset_cls, *args, **kwargs)


class DetailView(AttributeThunk, generic.DetailView):
    def __init__(self, viewset_cls, *args, **kwargs):
        super(DetailView, self).__init__(viewset_cls, *args, **kwargs)


class UpdateView(AttributeThunk, AjaxObjectFormMixin, generic.UpdateView):
    def __init__(self, viewset_cls, *args, **kwargs):
        super(UpdateView, self).__init__(viewset_cls, *args, **kwargs)


class DeleteView(AttributeThunk, AjaxObjectFormMixin, generic.DeleteView):
    def __init__(self, viewset_cls, *args, **kwargs):
        super(DeleteView, self).__init__(viewset_cls, *args, **kwargs)


class PopupCrudViewSet(object):
    fields = ()

    # @classonlymethod
    # def list(cls, **initkwargs):
    #     pass

    # @classonlymethod
    # def create(cls, **initkwargs):
    #     pass

    # @classonlymethod
    # def read(cls, **initkwargs):
    #     pass

    # @classonlymethod
    # def update(cls, **initkwargs):
    #     pass

    # @classonlymethod
    # def delete(cls, **initkwargs):
    #     pass

    # class AttributeThunk(object):
    #     """
    #     This class thunks the various attributes expected by Django generic
    #     CRUD views as properties of the parent viewset class instance.
    #     """
    #     def __init__(self, viewset, *args, **kwargs):
    #         self._viewset = viewset
    #         super(PopupCrudViewSet.AttributeThunk, self).__init__(*args, **kwargs)

    #     @property
    #     def model(self):
    #         return self._viewset.model

    #     @property
    #     def fields(self):
    #         return self._viewset.fields

    #     @property
    #     def success_url(self):
    #         return self._viewset.success_url

    # # Individual CRUD views are based on Django CBVs with custom constructor
    # # to supply the viewset class as argument. This viewset class argument is
    # # used to retrieve the class.model, class.fields, class.success_url, etc.
    # # properties from it so that the user needs to define this only once
    # # for each viewset.
    # class ListView(AttributeThunk, generic.ListView):
    #     def __init__(self, viewset_cls, *args, **kwargs):
    #         super(PopupCrudViewSet.ListView, self).__init__(
    #             viewset_cls, *args, **kwargs)

    # class CreateView(AttributeThunk, AjaxObjectFormMixin, generic.CreateView):
    #     def __init__(self, viewset_cls, *args, **kwargs):
    #         super(PopupCrudViewSet.CreateView, self).__init__(
    #             viewset_cls, *args, **kwargs)

    # class DetailView(AttributeThunk, generic.DetailView):
    #     def __init__(self, viewset_cls, *args, **kwargs):
    #         super(PopupCrudViewSet.DetailView, self).__init__(
    #             viewset_cls, *args, **kwargs)

    # class UpdateView(AttributeThunk, AjaxObjectFormMixin, generic.UpdateView):
    #     def __init__(self, viewset_cls, *args, **kwargs):
    #         super(PopupCrudViewSet.UpdateView, self).__init__(
    #             viewset_cls, *args, **kwargs)

    # class DeleteView(AttributeThunk, AjaxObjectFormMixin, generic.DeleteView):
    #     def __init__(self, viewset_cls, *args, **kwargs):
    #         super(PopupCrudViewSet.DeleteView, self).__init__(
    #             viewset_cls, *args, **kwargs)

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
