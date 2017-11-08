# -*- coding: utf-8 -*-
""" PopupCRUD list view template tags """

from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields.related import RelatedField
from django.forms.utils import pretty_name
from django.template import Library
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.utils.html import format_html
from django.utils import six
from django.contrib.admin.utils import lookup_field,label_for_field as lff

register = Library()

from popupcrud.views import ORDER_VAR, ORDER_TYPE_VAR

def label_for_field(view, queryset, field_name):
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
        field = options.get_field(field_name)
        if isinstance(field, RelatedField):
            label = field.related_model._meta.verbose_name
        else:
            label = field.verbose_name
    except FieldDoesNotExist:
        model = queryset.model
        # query the model for a method with matching name
        if hasattr(model, field_name) and callable(getattr(model, field_name)):
            # method exists, return its 'label' attribute value
            label = getattr(getattr(model, field_name), 'label', field_name.title())
        # query the viewset for a method with matching name
        elif hasattr(view._viewset, field_name) and callable(
            getattr(view._viewset, field_name)):
            # method exists, return its 'label' attribute value
            label = getattr(getattr(view._viewset, field_name), 'label', field_name.title())
        else:
            label = pretty_name(field_name)

    return {
        'text': label,
        'sortable': False,
        'class_attrib': 'class=col-{}'.format(field_name)
    }


def _coerce_field_name(field_name, field_index):
    """
    Coerce a field_name (which may be a callable) to a string.
    """
    if callable(field_name):
        if field_name.__name__ == '<lambda>':
            return 'lambda' + str(field_index)
        else:
            return field_name.__name__
    return field_name


def list_display_headers(view, queryset):
    """
    Returns the column headers for the fields specified in list_display
    """
    ordering_field_columns = view.get_ordering_field_columns()

    for i, field_name in enumerate(view._viewset.list_display):
        text, attr = lff(field_name, view.model, view._viewset, return_attr=True)

        if attr:
            field_name = _coerce_field_name(field_name, i)
            # Potentially not sortable

            order_field = getattr(attr, "order_field", None)
            if not order_field:
                # Not sortable
                yield {
                    "text": text,
                    "class_attrib": format_html(' class="text-uppercase column-{}"', field_name),
                    "sortable": False,
                }
                continue

        # OK, it is sortable if we got this far
        th_classes = ['sortable', 'column-{}'.format(field_name)]
        order_type = ''
        new_order_type = 'asc'
        sort_priority = 0
        sorted = False
        # Is it currently being sorted on?
        if i in ordering_field_columns:
            sorted = True
            order_type = ordering_field_columns.get(i).lower()
            sort_priority = list(ordering_field_columns).index(i) + 1
            th_classes.append('sorted %sending' % order_type)
            new_order_type = {'asc': 'desc', 'desc': 'asc'}[order_type]

        # build new ordering param
        o_list_primary = []  # URL for making this field the primary sort
        o_list_remove = []  # URL for removing this field from sort
        o_list_toggle = []  # URL for toggling order type for this field

        def make_qs_param(t, n):
            return ('-' if t == 'desc' else '') + str(n)

        for j, ot in ordering_field_columns.items():
            if j == i:  # Same column
                param = make_qs_param(new_order_type, j)
                # We want clicking on this header to bring the ordering to the
                # front
                o_list_primary.insert(0, param)
                o_list_toggle.append(param)
                # o_list_remove - omit
            else:
                param = make_qs_param(ot, j)
                o_list_primary.append(param)
                o_list_toggle.append(param)
                o_list_remove.append(param)

        if i not in ordering_field_columns:
            o_list_primary.insert(0, make_qs_param(new_order_type, i))

        yield {
            "text": text,
            "sortable": True,
            "sorted": sorted,
            "ascending": order_type == "asc",
            "sort_priority": sort_priority,
            "url_primary": view.get_query_string({ORDER_VAR: '.'.join(o_list_primary)}),
            "url_remove": view.get_query_string({ORDER_VAR: '.'.join(o_list_remove)}),
            "url_toggle": view.get_query_string({ORDER_VAR: '.'.join(o_list_toggle)}),
            "class_attrib": format_html(' class="text-uppercase {}"', ' '.join(th_classes)) if th_classes else '',
        }

        # yield {
        #     'text': text,
        #     'sortable': False,
        #     'class_attrib': 'class=col-{}'.format(field_name)
        # }
        #yield label_for_field(view, queryset, field_name)

    # Action column
    yield {
        'text': ugettext("Action"),
        'sortable': False,
        'class_attrib': 'class=text-uppercase col-action'
    }


def list_field_value(view, obj, field, context, index):
    value = ''
    try:
        # Use django.admin's function to render the list_display column value
        # lookup_field expects a ModelAdmin instance as the third argument,
        # but all it does is dyanamic lookup of the field as a method of this
        # object and if found, evaluates it to return the value. So it's safe
        # to pass it a ViewSet instance. Of course, if the lookup_field
        # implementation changes, we'll to change this code accordingly.
        f, attr, value = lookup_field(field, obj, view._viewset)

        # for fields that have 'choices=' set conver the value into its
        # more descriptive string.
        if getattr(f, 'choices', None):
            choices = dict(f.choices)
            if value in choices:
                value = dict(choices)[value]

    except AttributeError:
        f, attr, value = (None, None, '')

    if index == 0:
        detail_url = view._viewset.get_detail_url(obj)
        if detail_url:
            title = ugettext("{0} Detail").format(
                view._viewset.model._meta.verbose_name)
            if view._viewset.popups['detail']:
                value = six.text_type('<a name="object_detail" data-url="{0}" data-title="{2}" href="javascript:void(0);">{1}</a>').format(
                    detail_url, value, title)
            else:
                value = six.text_type('<a href="{0}" title="{2}">{1}</a>').format(
                    detail_url, value, title)

        return mark_safe(six.text_type("{0}<div data-name='{1}'></div>").format(
                value, view._viewset.get_obj_name(obj)))

    return value


def render_item_actions(context, obj):
    popup_edit_template = six.text_type('<a name="create_edit_object" data-url="{0}" data-title="{1}" href="javascript:void(0);"><span class="glyphicon glyphicon-pencil" title="{1}"></span></a>')
    popup_delete_template = six.text_type('<a name="delete_object" data-url="{0}" data-title="{1}" href="javascript:void(0);"><span class="glyphicon glyphicon-trash" title="{1}"></span></a>')

    legacy_edit_template = six.text_type('<a href="{0}"><span class="glyphicon glyphicon-pencil" title="{1}"></span></a>')
    legacy_delete_template = six.text_type('<a href="{0}"><span class="glyphicon glyphicon-trash" title="{1}"></span></a>')

    view = context['view']
    edit_url = view._viewset.get_edit_url(obj)
    delete_url = view._viewset.get_delete_url(obj)
    edit_title = ugettext("Edit {0}").format(
        view._viewset.model._meta.verbose_name)
    delete_title = ugettext("Delete {0}").format(
        view._viewset.model._meta.verbose_name)

    # choose the right template based on legacy_crud setting
    edit_template = popup_edit_template if view._viewset.popups['update'] \
            else legacy_edit_template
    delete_template = popup_delete_template if view._viewset.popups['delete'] \
            else legacy_delete_template

    edit_action = edit_template.format(edit_url, edit_title) if edit_url else ''
    delete_action = delete_template.format(delete_url, delete_title) if delete_url else ''
    custom_actions = []
    for index, action in enumerate(view._viewset.get_item_actions(obj)):
        custom_actions.append(
            "<a name='custom_action' href='javascript:void(0);' title='{0}' data-action='{1}' data-obj='{2}'><span class='{3}'></span></a>".format(
                action[0], index, obj.pk, action[1]))

    item_actions = ("%s %s" % (edit_action, delete_action))
    if custom_actions:
        item_actions = "%s %s" % (item_actions, " ".join(custom_actions))
    return mark_safe(item_actions)


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
    headers = list(list_display_headers(view, queryset))

    num_sorted_fields = 0
    for h in headers:
        if h['sortable'] and h['sorted']:
            num_sorted_fields += 1

    return {
        'headers': headers,
        'results': list_display_results(view, queryset, context),
        'num_sorted_fields': num_sorted_fields,
    }


@register.inclusion_tag("popupcrud/empty_list.html", takes_context=True)
def empty_list(context):
    viewset = context['view']._viewset
    return {
        'viewset': viewset,
        'icon': viewset.get_empty_list_icon(),
        'message': viewset.get_empty_list_message(),
        'new_button_text': ugettext("New {0}").format(
            viewset.model._meta.verbose_name),
    }
