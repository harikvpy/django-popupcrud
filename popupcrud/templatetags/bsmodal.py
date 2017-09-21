# coding: utf-8
"""
A tag to help creation of Bootstrap modal dialogs. You may use this tag as:

    .. code:: django

        {% bsmodal dialogTitle dialogId [close_title_button={Yes|No}] %}
            <dialog content goes here>
        {% endbsmodal %}

    :dialogTitle: Required. The title of the modal window. This can be a template
        variable (created with ``{% trans 'something' as var %}``) or a
        string literal.
    :dialogId: Required. The id of the modal window specified as string literal.
    :close_title_button: Optional. A flag indicating whether to show the modal
        window close button on the titlebar. Specify one of ``Yes`` or ``No``.


This would create a hidden dialog with title ``dialogTitle`` and id ``dialogId``.
The content of the dialog body is to be written between the pair of tags
``{% bsmodal %}`` and ``{% endbsmodal %}``.

The final rendered html fragment would look like this:

    .. code:: html

        <div class="modal fade" tabindex="-1" role="dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                    <h4 class="modal-title">{{dialogTitle}}</h4>
                </div>
                <div class="modal-body">
                    <..content between bsmodal & endbsmodal tags..>
                </div>
            </div>
        </div>

The html template for the modal is stored in ``popupcrud/modal.html``. So if you
want to custom styling of the modal windows, you may define your own template
in your projects ``templates`` folder.

Refer to Boostrap `documentation <https://getbootstrap.com/docs/3.3/javascript/#modals>`_ on modals for more information on how to show
and hide the modal windows.
"""

from django import template

register = template.Library()

class ModalDialog(template.Node):
    def __init__(self, dialog_id, title, content_nodelist, close_title_button=True,
                header_bg_css=''):
        self.dialog_id = dialog_id
        self.title = template.Variable(title)
        self.content_nodelist = content_nodelist
        self.close_title_button = close_title_button
        self.header_bg_css = header_bg_css

    def render(self, context):
        try:
            title = self.title.resolve(context)
        except template.VariableDoesNotExist:
            title = self.title.var

        templ = template.loader.get_template("popupcrud/modal.html")
        return templ.render({
            'id': self.dialog_id,
            'title': title,
            'body': self.content_nodelist.render(context),
            'close_btn': self.close_title_button,
        })


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
    header_bg_css = ''
    # optional elements
    for i in range(3, len(contents)):
        option = strip_quotes(contents[i]).split('=')
        if option[0] == 'close_title_button':
           close_title_button = True if option[1] in ['True', 'Yes'] else False
        elif option[0] == 'header_bg_css':
            header_bg_css = option[1]

    nodelist = parser.parse(('endbsmodal',))
    parser.delete_first_token()
    return ModalDialog(
        dialog_id, title, nodelist, close_title_button, header_bg_css)
