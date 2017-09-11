# -*- coding: utf-8 -*-
""" PopupCRUD list view template tags """

from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields.related import RelatedField
from django.forms.utils import pretty_name
from django.template import Library
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext

register = Library()


def label_for_field(view, queryset, field):
    """
    Returns the suitable lable for a field. Labels are determined as per the
    following rules:
        1. Model's meta class is searched for a field with matching name.
           If found, fields verbose_name is used as label

        2. A method on the model class with the same name is looked up.
           If found, the method's 'label' attribute value is used as the label.

        3. Viewset is searched for a method with the same name.
           If found, the method's 'label' attribute value is used as the label.

        4. If none of the above match, the specified field name is used as is.
    """
    options = queryset.model._meta
    try:
        field = options.get_field(field)
        if isinstance(field, RelatedField):
            label = field.related_model._meta.verbose_name
        else:
            label = field.verbose_name
    except FieldDoesNotExist:
        model = queryset.model
        # query the model for a method with matching name
        if hasattr(model, field) and callable(getattr(model, field)):
            # method exists, return its 'label' attribute value
            label = getattr(getattr(model, field), 'label', field.title())
        # query the viewset for a method with matching name
        elif hasattr(view._viewset, field) and callable(
            getattr(view._viewset, field)):
            # method exists, return its 'label' attribute value
            label = getattr(getattr(view._viewset, field), 'label', field.title())
        else:
            label = pretty_name(field)

    return label


def list_display_headers(view, queryset):
    """
    Returns the column headers for the fields specified in list_display
    """
    for field in view._viewset.list_display:
        yield label_for_field(view, queryset, field)

    yield ugettext("Action")


def list_field_value(view, obj, field, context, index):
    value = ''
    if hasattr(obj, field):
        value = getattr(obj, field)
        if callable(value):
            value = value()
    elif hasattr(view._viewset, field):
        # try if the attribute is a method on the viewset class itself
        value = getattr(view._viewset, field)
        if callable(value):
            # TODO: 2017年09月06日 (週三) 08時33分26秒
            #		We're instaintiating the viewset class for every field
            #       that is a method on the viewset class. NOT VERY GOOD!
            value = getattr(view._viewset, field)(obj)

    if index==0 and 'edit_url' in context:
        detail_url = view._viewset.get_detail_url(obj)
        if detail_url:
            return mark_safe('<a name="object_detail" data-url="{0}" href="javascript:void(0);">{1}</a>'.format(
                detail_url, value))
        else:
            return value

    return value


def render_item_actions(context, obj):
    action_template = """
    <a name="edit_object" data-url="{0}" href="javascript:void(0);"><span class="glyphicon glyphicon-pencil" title="{2}"></span></a>
    <a name="delete_object" data-url="{1}" href="javascript:void(0);"><span class="glyphicon glyphicon-trash" title="{3}"></span></a>
    """
    view = context['view']
    edit_url = view._viewset.get_edit_url(obj)
    delete_url = view._viewset.get_delete_url(obj)

    return mark_safe(action_template.format(
        edit_url, delete_url, ugettext("Edit"), ugettext("Delete")))


def render_list_display(view, obj, context):
    for i, name in enumerate(view._viewset.list_display):
        yield list_field_value(view, obj, name, context, i)

    yield render_item_actions(context, obj)


def list_display_results(view, queryset, context):
    for obj in queryset:
        yield render_list_display(view, obj, context)


@register.inclusion_tag("popupcrud/list_content.html", takes_context=True)
def list_content(context):
    view = context['view']
    queryset = context['object_list'] #view.get_queryset()
    return {
        'headers': list_display_headers(view, queryset),
        'results': list_display_results(view, queryset, context)
    }
