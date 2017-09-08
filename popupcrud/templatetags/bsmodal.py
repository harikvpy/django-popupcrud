# coding: utf-8
'''
A template tag to ease creation of Bootstrap modal dialogs. Use this tag like:

    {% bsmodal dialogTitle dialogId [close_title_button={Yes|No}] %}
        <dialog content goes here>
    {% endbsmodal %}

This would create a hidden dialog with title dialogTitle and id dialogId.
dialogTitle can be a template variable (for eg created with
{% trans 'something' as var %}) or a string literal. dialogId is expected to be
a string literal. This cane be enclosed in a pair of quotes as is the norm
for string literals or can be written as it is.

The content of the dialog body is to be written between the pair of tags
bsmodal and endbsmodal.

This would result in the html fragment
    <div class="modal fade"...>
        <div class="modal-content">
            <div class="modal-header">
            </div>
            <div class="modal-body">
            </div>
        </div>
    </div>
'''

from django import template

register = template.Library()

DIALOG_TEMPLATE = u"""
    <div class="modal fade" id="{0}" tabindex="-1" role="dialog" aria-hidden="true">
        <div class="modal-dialog modal-dialog-top" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    {3}
                    <h4 class="modal-title">{1}</h4>
                </div>
                <div class="modal-body">
                    {2}
                </div>
            </div>
        </div>
    </div>
    """

DIALOG_CLOSE_TITLE_BUTTON = u"""
    <button type="button" class="close" data-dismiss="modal" aria-label=""><span aria-hidden="true">&times;</span></button>
    """

class ModalDialog(template.Node):
    def __init__(self, dialog_id, title, content_nodelist, close_title_button=True):
        self.dialog_id = dialog_id
        self.title = template.Variable(title)
        self.content_nodelist = content_nodelist
        self.close_title_button = close_title_button

    def render(self, context):
        try:
            title = self.title.resolve(context)
        except template.VariableDoesNotExist:
            title = self.title.var
        return DIALOG_TEMPLATE.format(
                self.dialog_id,
                title,
                self.content_nodelist.render(context),
                DIALOG_CLOSE_TITLE_BUTTON if self.close_title_button else ''
                )


def strip_quotes(string):
    '''
    Strips embedded starting and ending quotes, if any.
    Starting and ending quote characters have to be the same.
    '''
    if string[0] == string[-1] and string[0] in ('"', "'"):
        return string[1:-1]
    return string


@register.tag
def bsmodal(parser, token):
    try:
        contents = token.split_contents()
    except ValueError:
        pass

    if len(contents) < 2:
        raise template.TemplateSyntaxError(
                "%r requires dialog title as argument" % \
                        token.contents.split()[0]
                )

    title = strip_quotes(contents[1])
    dialog_id = strip_quotes(contents[2]) if len(contents) > 2 else "modal"
    close_title_button = True
    # optional elements
    for i in range(3, len(contents)):
        option = strip_quotes(contents[i]).split('=')
        if option[0] == 'close_title_button':
           close_title_button = True if option[1] in ['True', 'Yes'] else False

    nodelist = parser.parse(('endbsmodal',))
    parser.delete_first_token()
    return ModalDialog(
            dialog_id,
            title,
            nodelist,
            close_title_button
            )
