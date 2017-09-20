# -*- coding: utf-8 -*-
""" popupcrud widgets """

from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.utils.text import camel_case_to_spaces


class RelatedFieldPopupFormWidget(RelatedFieldWidgetWrapper):
    """
    A modified version of django.admin's `RelatedFieldWidgetWrapper`,
    adds a **Create New** hyperlink to the bottom of the select box of a related
    object field. This hyperlink will have CSS class `add-another` and its id
    set to `add_id_<field_name>` with its href set to `javascript:void(0);`.

    The associated JavaScript `popupcrud/js/popupcrud.js`, binds a click handler
    to `.add-another`, which then activates the Bootstrap modal associated with
    the hyperlink. The modal body will be filled with the HTML response from
    an AJAX request to the hyperlink's `data-url` attribute value.

    The JavaScript file is added to the form's media list automatically.

    """
    def __init__(self, widget, new_url, *args, **kwargs):
        """
        Constructor takes the following required parameters:

        :param widget: The underlying `Select` widget that this widget replaces.
        :param url: The url to load the HTML content to fill the assocaited modal
            body.
        """
        _unused = args, kwargs
        self.widget = widget
        self.new_url = str(new_url)
        self.choices = widget.choices
        self.needs_multipart_form = getattr(widget, "needs_multipart_form", False)
        self.attrs = getattr(widget, 'attrs', None)

    def render(self, name, value, *args, **kwargs):
        widget = self.widget
        widget.choices = self.choices
        output = [self.widget.render(name, value, *args, **kwargs)]
        output.append(u'<a href="javascript:void(0);" class="add-another" id="add_id_{0}" data-url="{1}">'\
                      .format(name, self.new_url))
        output.append(u'<small>%s</small></a>' % ugettext('New {0}').\
                      format(camel_case_to_spaces(name).title()))
        return mark_safe(u''.join(output))

    class Media:
        js = ('popupcrud/js/popupcrud.js',)
