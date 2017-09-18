# -*- coding: utf-8 -*-
""" popupcrud widgets """

from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.utils.text import camel_case_to_spaces


class RelatedFieldPopupFormWidget(RelatedFieldWidgetWrapper):
    """
    A modified version of RelatedFieldWidgetWrapper, which simply adds a
    'Create New' hyperlink to the bottom of the select box for a related
    object. This hyperlink has the id set to 'add_id_<field_name>' with its
    href set to 'javascript:void(0);'. Therefore the client has to provide
    the necessary javascript code to bind to the click on this element to
    activate the relevant popup.
    """
    def __init__(self, widget, new_url, *args, **kwargs):
        # pylint: disable=super-init-not-called
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
