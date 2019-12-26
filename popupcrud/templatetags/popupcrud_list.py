# -*- coding: utf-8 -*-
# pylint: disable=W0212, R0914
""" PopupCRUD list view template tags """

from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields.related import RelatedField
from django.forms.utils import pretty_name
from django.template import Library
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.utils.html import format_html
from django.utils.text import capfirst
from django.contrib.admin.utils import lookup_field, label_for_field as lff

import six

from bootstrap3.renderers import FormRenderer, FormsetRenderer
from bootstrap3.bootstrap import get_bootstrap_setting
from bootstrap3.forms import render_field

from popupcrud.views import ORDER_VAR

register = Library()

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
        elif hasattr(view._viewset, field_name) and \
            callable(getattr(view._viewset, field_name)):
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
        return field_name.__name__
    return field_name


def list_display_headers(view, queryset):
    """
    Returns the column headers for the fields specified in list_display
    """
    ordering_field_columns = view.get_ordering_field_columns()

    for i, field_name in enumerate(view._viewset.list_display):
        text, attr = lff(field_name, view.model, view._viewset, return_attr=True)
        text = mark_safe(text)  # takes care of embedded tags in header labels
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
        sorted_field = False
        # Is it currently being sorted on?
        if i in ordering_field_columns:
            sorted_field = True
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
            "sorted": sorted_field,
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
    dummy_obj = queryset.model()
    dummy_obj.pk = 1
    if view._viewset.get_edit_url(dummy_obj) or \
        view._viewset.get_delete_url(dummy_obj) or \
        view._viewset.item_actions:
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
        f, _, value = lookup_field(field, obj, view._viewset)

        # for fields that have 'choices=' set conver the value into its
        # more descriptive string.
        if getattr(f, 'choices', None):
            choices = dict(f.choices)
            if value in choices:
                value = dict(choices)[value]

    except AttributeError:
        f, _, value = (None, None, '')

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

class PopupCrudFormsetFormRenderer(FormRenderer):
    '''A special class to render formset forms fields as table
    row columns'''

    def render_fields(self):
        rendered_fields = []
        visible_fields = []
        hidden_fields = []
        for field in self.form:
            if not field.is_hidden:
                visible_fields.append(field)
            else:
                hidden_fields.append(field)
        first = True

        for field in visible_fields:
            field_html = self.__render_field(field)
            if first:
                hidden_html = ''
                for hidden_field in hidden_fields:
                    hidden_html += self.__render_field(hidden_field)
                    field_html = hidden_html + field_html
                first = False
            field_html = "<td>" + field_html + "</td>"
            rendered_fields.append(field_html)
        return '\n'.join(rendered_fields)

    def __render_field(self, field):
        return render_field(
            field,
            layout=self.layout,
            form_group_class=self.form_group_class,
            field_class=self.field_class,
            label_class=self.label_class,
            show_label=False,
            show_help=self.show_help,
            exclude=self.exclude,
            set_required=field.field.required,
            set_disabled=field.field.disabled,
            size=self.size,
            horizontal_label_class=self.horizontal_label_class,
            horizontal_field_class=self.horizontal_field_class,
            error_css_class=self.error_css_class,
            required_css_class=self.required_css_class,
            bound_css_class=self.bound_css_class)


class PopupCrudFormsetRenderer(FormsetRenderer):

    def render_form(self, form, **kwargs):
        renderer = PopupCrudFormsetFormRenderer(form, **kwargs)
        return renderer._render() # render_form(form, **kwargs)

    def render_forms(self):
        render_header = True
        html = "<table class='table table-condensed'>"
        if render_header:
            html += self.render_header()
        html += "<tbody>"
        for form in self.formset.forms:
            html += "<tr>"+self.render_form(
                form,
                layout=self.layout,
                form_group_class=self.form_group_class,
                field_class=self.field_class,
                label_class=self.label_class,
                show_label=False,
                show_help=self.show_help,
                exclude=self.exclude,
                # set_required=self.set_required,
                # set_disabled=self.set_disabled,
                size=self.size,
                horizontal_label_class=self.horizontal_label_class,
                horizontal_field_class=self.horizontal_field_class,
            )+"</tr>"
        html += "</tbody></table>"
        return html

    def render_header(self):
        headers = []
        form = self.formset.forms[0]
        for name, field in form.fields.items():
            required_style = " class='%s'" % 'required' if field.required else ''
            bf = form[name]
            if not bf.is_hidden:
                headers.append("<th%s>%s</th>" % (
                    required_style,
                    bf.label if name != 'DELETE' else '&nbsp;'))
        return "<thead><tr>{0}</tr></thead>".format("".join(headers))


@register.simple_tag
def render_formset(formset):
    '''
    Renders the formset within a bootstrap horizontal form layout. This requires
    special handling as standard bootstrap formset rendering does not work well
    within a <form class='form-horizontal'></form> element.

    After many attempts and using some suggestions from SO, the following layout
    seems work:

    <form class='form-horizontal'>
        {% bootstrap_form form layout='horizontal'%}

        <div id="id_formset">
            <label class="col-md-3 control-label">Members</label>
            <div class='col-md-9' style="max-height: 250px; overflow-y: scroll;">
                <table class='table table-condensed'>
                    <tbody>
                        {% for form in formset.forms %}
                        <tr>
                            <td>
                                <div class='form-group' style="margin-bottom: 0px;">
                                    <div class='form-inline'>
                                        {% for field in form %}
                                            <input class="form-control input-sm" id="field.name" placeholder="field.label">
                                        {% endfor %}
                                    </div>
                                </div>
                            </td>
                            <td style='vertical-align: middle;'>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        <submit/reset buttons>
    </form>

    For rendering the innermost <input../>, we use django-bootstrap3's render_field() function
    so that it can use the appropriate classes depending on the field type.

    This template tag builds the above fragment for the given formset.
    '''

    model = formset.model
    label = capfirst(model.__name__)
    if hasattr(model._meta, 'verbose_name_plural'):
        label = model._meta.verbose_name_plural

    renderer = PopupCrudFormsetRenderer(formset, form_group_class='modal-formset-field')
    label_class = get_bootstrap_setting('horizontal_label_class')
    field_class = get_bootstrap_setting('horizontal_field_class')
    output2 = r"""
    <div id="id_formset" class="form-group modal-formset">
        <label class="{2} control-label">{0}</label>
        <div class='{3} table-wrapper'>
            {1}
        </div>
    </div>
    """.format(label, renderer._render(), label_class, field_class) # pylint: disable=W0212

    return mark_safe(output2)

def _render_formset_form(form):
    '''Renders a formset form within the style setting headers above.'''

    output = r'''
    <tr>
        <td>
            <div class='form-group' style="margin-bottom: 0px;">
                <div class='form-inline'>
    '''

    for field in form:
        # Delegate the hard bits to django-bootstrap3 field renderer
        field_str = render_field(
            field,
            form_group_class='modal-formset-field',
            field_class='hide' if field.name == 'DELETE' else '',
            show_label=False,
            show_help=False,
            size='small')
        output += field_str

    output += r'''
                </div>
            </div>
        </td>
        <td style='vertical-align: middle;'>
        </td>
    </tr>
    '''
    return output
