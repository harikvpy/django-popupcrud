/* 
 * Event raised after a create/update form is displayed and ready for further
 * manipulation by client code. This event can be trapped by client code to
 * add their own custom JavaScript initialization to the form. Using this event
 * instead of the ubiqitous $(document).ready ensures that the same init code
 * works well on both legacy and popup modes.
 *
 * This allows you write code such as this:
 *
 *   $(document).on("crudform.ready", function(event) {
 *     // create/edit form initialization code goes here
 *   });
 */
const CRUDFORM_READY = "crudform.ready";

(function($) {
  $.fn.popupCrud = function (opts) { // wrap all popupcrud functions in a closure
    /* 
     * Bind a submit function to a form embedded in a Bootstrap modal, which in 
     * turn uses AJAX POST request to submit the form data. When the form has been
     * successully submitted, the modal is hidden. If the submitted form has errors
     * the form is re-rendered with field errors highlighted as per Bootstrap
     * rendering guidelines.
     *
       Parameters:
        form: jQuery selector to the form that is to be submited via AJAX
        modal: jQuery selector to the modal dialog to be dismissed post successful
               form submission
        complete: A function to be called upon successful form submission.
     */
    var submitModalForm = function(form, modal, complete) {
        $(form).submit(function(e) {
            e.preventDefault();
            $.ajax({
                type: $(this).attr('method'),
                url: $(this).attr('action'),
                data: $(this).serialize(),
                success: function (xhr, ajaxOptions, thrownError) {
                    if ( $(xhr).find('.has-error').length > 0 ||
                         $(xhr).find('.alert').length > 0) {
                        $(modal).find('.block-content').html(xhr);
                        bindAddAnother(modal);
                        bindSelect2(modal);
                        submitModalForm(form, modal, complete);
                    } else {
                        $(modal).modal('hide');
                        if (typeof complete == "function") {
                            complete(xhr); // notify caller
                        }
                    }
                },
                error: function (xhr, ajaxOptions, thrownError) {
                  // todo
                }
            });
        });
    },
    /* Helper function to retrieve cookie value */
    getCookie = function(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },
    /*
     * Triggers crudform.ready event on an activated form if it's
     * not the delete-form
     */
    triggerCrudFormReady = function(elem) {
      var form = $(elem).find("form");
      if (form) {
        var ev = $.Event(CRUDFORM_READY);
        if (form.attr('id') != 'delete-form') { // exclude delete-form
          form.trigger(ev);
        }
      }
    },
    /*
     * Bind select2 widget to any form controls with css style .django-select2
     */
    bindSelect2 = function(modal) {
      var sels = $(modal).find('.django-select2');
      if (sels.length > 0) {
        $(sels).djangoSelect2({
          dropdownParent: $(modal)
        });
      }

      // trigger the crudform.ready event
      triggerCrudFormReady(modal);
    },
    /*
     * Binds all '.add-another' hyperlinks under the given 'elem' with their own
     * modals, each of which will hold the form for the .add-another's data-url
     * value. Each such modal is given an id composed as the value of the 'a' 
     * tag's 'id' value + '-modal'. The modal will be added only if a modal with
     * the same id does not exist so as to avoid duplicate modals.

     * The 'a' tag is assigned the newly added modal's id, so that the associated
     * modal dialog can be loaded with the respective url form content and 
     * activated in a generic manner from a Javascript function.
     */
    bindAddAnother = function(elem) {
      // Modal dialog template derived from #create-edit-modal that'll be added at 
      // the end of the <body> tag.
      if ($("#add-related-modal").length == 0)
        return;

      var modalTemplate = $('<div/>').html($("#add-related-modal")[0].outerHTML);
      $(modalTemplate)
        .find('.modal').attr('id', 'create-related-modal')
        .find('.modal-title').html('')
        .find('.modal-body').html('')
      var createRelatedModal = modalTemplate.html();
      elem.find(".add-another").each(function(index, elem) {
        var modalId = $(elem).attr('id') + '-modal';
        if ($("#"+modalId).length == 0) {
          $("body").append(createRelatedModal.replace('create-related-modal', modalId))
        }
        $(elem).data('modal', modalId);
      });
      /*
       * Generic function that loads the form associated with a hyperlink into
       * the related modal.
       *
       * Constraints & Behavior:
       *  1. <a> element is preceded immediately by a <select> element
       *  2. <a> element has the following data attributes:
       *      a. data-url: the URL to load the form from
       *      b. data-modal: id of the associated modal that is loaded with the 
       *         form and activated.
       *  3. The activated modal's title is set to <a> element's text content.
       *  4. If the activated form submission was successful, the sibling 'select'
       *     element is popuplated with an <option> for the just added element.
       */
      $(elem).find(".add-another").click(function(evtObj) {
        var url = $(this).data('url');
        var title = $(this).text();
        var select = $(this).prevAll('select');
        var modalId = $(this).data('modal');
        var modal = $('#' + modalId);
        modal.find('.modal-body').load(url, function () {
          modal.find('.modal-title').text(title);
          bindAddAnother(modal);
          modal.modal('show');
          submitModalForm(modal.find('#create-edit-form'), '#'+modalId, 
            function(xhr) {
              $(select).append($("<option></option>").
                attr("value", xhr.pk).text(xhr.name));
              var newVal = $(select).val();
              if ($(select).attr('multiple')) {
                newVal.push(xhr.pk);
              } else {
                newVal = xhr.pk;
              }
              $(select).val(newVal).trigger('change');
            })
        });
      });
    },
    handleCreateEdit = function(evtObj) {
      evtObj.preventDefault();
      var url = $(this).data('url');
      var title = $(this).data('title');
      $('#create-edit-modal .modal-body').load(url, function () {
        $('#create-edit-modal .modal-title').text(title);
        bindAddAnother($("#create-edit-modal"));
        $('#create-edit-modal').modal('show');
        submitModalForm('#create-edit-form', 
          '#create-edit-modal', function(xhr) {
            location.reload();
          });
      });
    }, 
    // handler for object detail view
    handleObjectDetail = function(evtObj) {
      evtObj.preventDefault();
      var url = $(this).data('url');
      var title = $(this).data('title');
      $('#detail-modal .modal-body').load(url, function () {
        $('#detail-modal .modal-title').text(title);
        $('#detail-modal').modal('show');
      });
    },
    // delete an object action handler
    handleDeleteObject = function(evtObj) {
      evtObj.preventDefault();
      $('#delete-modal #id_object_name').text(
        $(evtObj.target).parents('tr').children(':nth-child(1)').children('div').data('name'));
      $('#delete-modal .modal-body form').attr(
        'action', $(evtObj.target).parent('a').data('url'));
      $('#delete-modal').modal('show');
      var title = $(this).children('span').attr('title');
      submitModalForm('#delete-form', '#delete-modal', 
        function(xhr) {
          showActionResult(xhr.result, title, xhr.message);
        }
      );
    },
    // custom action handler
    handleCustomAction = function(evtObj) {
      evtObj.preventDefault();
      var action = $(this).data('action');
      var title = $(this).attr('title');
      $.ajax({
        type: 'POST',
        data: {
          csrfmiddlewaretoken: getCookie('csrftoken'),
          action: action, 
          item: $(this).data('obj')
        },
        success: function (xhr, ajaxOptions, thrownError) {
          showActionResult(xhr.result, title, xhr.message);
        }
      });
    },
    // Show the action result message in a modal
    //
    // Parameters:
    //      result: bool, action success indicator
    //      title: title for the dialog
    //      message: message to be displayed in the modal
    // Returns:
    //      None
    showActionResult = function(result, title, message) {
      $("#action-result-modal .modal-title").text(title);
      $("#action-result-modal #id_action_result").html(message);
      $('#action-result-modal').on('hidden.bs.modal', result ? 
        function(evtObj) { 
          $('#action-result-modal').off('hidden.bs.modal');
          location.reload();
        } : 
        function(evtObj) { 
          $('#action-result-modal').off('hidden.bs.modal');
        });
      $('#action-result-modal').modal('show');
    };

    $("[name=create_edit_object]").click(handleCreateEdit);
    $("[name=object_detail]").click(handleObjectDetail);
    $("a[name='delete_object']").click(handleDeleteObject);
    $("a[name='custom_action']").click(handleCustomAction);

    // Bind any embedded .add-another links in the document to its own modal. 
    bindAddAnother($('body')); 

    /* 
     * Adjusts the just activated modal window's z-index to a value higher 
     * than the previously activated modal window's z-index. This will 
     * ensure that each newly activated modal is layered on top of all 
     * previously activated modals achieving the layered dialog effect.

     * Code borrowed from: http://jsfiddle.net/CxdUQ/
     */
    $(document).on('show.bs.modal', '.modal', function (event) {
      // calculate z-index as a function of number of visible modal windows.
      var zIndex = 1040 + (10 * $('.modal:visible').length);
      $(this).css('z-index', zIndex);
      setTimeout(function() {
        $('.modal-backdrop').not('.modal-stack').css('z-index', zIndex - 1).addClass('modal-stack');
      }, 0);
    });
    $(document).on('shown.bs.modal', '.modal', function (event) {
      /* 
       * Initialize any django-select2 fields in the dialog. If the dialog does
       * not have any select2 fields, this code does nothing.
       *
       * Also this is a template for any custom initialization to be done
       * by user javascript codes. Typically if the user code has to do UI level
       * processing, it does it from $(document).ready(). But for UI processing
       * on modal dialogs, it has to be done from $(document).on('shown.bs.modal').
       */
      bindSelect2(this);
    });

    /*
     * Trigger CRUDFORM_READY event, if we're in legacy_crud mode. Since
     * '<form>' element would only be present in legacy_crud mode, this code
     * is safe in that it will not have any effect on popup crud mode.
     * Delete item form is preloaded with list template, but we dont trigger
     * the event for this form (checked by triggerCrudFormReady).
     */
    triggerCrudFormReady(document);
  }
  $(document).ready(function() {
    $.fn.popupCrud({});
  });
})(jQuery);
