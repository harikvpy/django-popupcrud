History
-------

0.1.0 (2017-09-25)
++++++++++++++++++

* Initial release

0.1.2 (2017-09-26)
++++++++++++++++++

* Merge Quickstart section into README

0.1.3 (2017-09-26)
++++++++++++++++++

* Add missing HISTORY.rst to manifst

0.1.4 (2017-09-26)
++++++++++++++++++

* Support for ``order_field`` attribute for ``list_display`` method fields.
  This works similar to ``ModelAdmin`` method fields' ``admin_order_field``
  property.

0.1.5 (2017-09-26)
++++++++++++++++++

* Better unicode support

0.1.6 (2017-09-27)
++++++++++++++++++

* Better access control support through 'login_url' & 'raise_exception'
  PopupCrudViewSet properties

0.1.7 (2017-10-13)
++++++++++++++++++

* Object detail view support

0.1.8 (2017-10-16)
++++++++++++++++++

* Add PopupCrudViewSet.urls() -- a single method to return all the CRUD urls
  that can be added to urlpatterns[].
* When related object popup is activated on a multiselect select and it adds a
  new object, the object is added to the existing list of selections. (old code
  used to replace all the current selections with the newly added item)
* Insert all form media into ListView through ListView.media property.
* Fix broken support for django-select2 in modals by setting control's
  dropdownParent to the modal (rather than parent window)
* Use the 'create-edit-modal' modal as the template for secondary modals
  activated through related-model modal popups. This ensures consistent modal
  look and feel if the user customized the modal template by overriding
  popupcrud/modal.html template.
* Fix ALLOWED_HOSTS in settings - issue #1

0.2.0 (2017-10-18)
++++++++++++++++++
* Bumping minor version as reflection of new features legacy_crud dict, media
  & out-of-the-box django_select2 support in previous release
* Added 'crudform.ready' JavaScript event, which is triggered when
  create/update form is activated. This event provides clients an uniform way to
  apply their own optional initialization code to the CRUD forms.
* Added 6 more tests to cover new legacy_crud dict value support & form media
  injection.

0.3.0 (2017-10-26)
++++++++++++++++++
* List view content is rendered in its own block, popupcrud_list, in the
  template file. This allows the list content to be relocated to different
  parts of the base template.
* Add ViewSet.empty_list_icon and ViewSet.empty_list_message properties. These
  properties provide for prettier rendering of empty table states.

0.3.1 (2017-10-26)
++++++++++++++++++
* Use custom style for empty-list-state icon sizing. Earlier code was using font
  awesome style.

0.4.0 (2017-11-2)
+++++++++++++++++
* Breadcrumbs support
* ListView queryset custom filtering through ``PopupCrudViewSet.get_queryset()``
* Support custom form init args through ``PopupCrudViewSet.get_form_kwargs()``
* ``PopupCrudViewSet.new_url`` and ``PopupCrudViewSet.list_url`` are determined
  through ``PopupCrudViewSet.get_new_url()`` and
  ``PopupCrudViewSet.get_list_url()`` throughout the code.

0.4.1 (2017-11-6)
+++++++++++++++++
* Fix an issue where when form with errors is rendered select2 and add-related
  widgets are not bound correctly

0.5.0 (2017-11-10)
++++++++++++++++++
* Add custom item action support
* Clean up JavaScript by encapsulating all methods in its own namespace &
  reducing code duplication
* Add missing CSS styles to popupcrud.css
* Empty_list_message class variable now allows embedded html tags (value is
  wrapped in mark_safe() before placing in template context)

0.6.0 (2018-03-15)
++++++++++++++++++
* Add formset support in CRUD create/update views
* Add size option to bsmodal template tags
* Fixes to some minor bugs

0.6.1 (2018-03-16)
++++++++++++++++++
* Make formset alignment consistent with bootstrap3 settings
  horizontal_label_class & horizontal_field_class.

0.6.2 (2018-03-17)
++++++++++++++++++
* Fix bug where forms with m2m fields were not saved
* Reflect formset form field 'required' status in field column header
* Make formsets work in legacy crud mode
* django-select2 support in formset forms
* Minor formset layout formatting improvements

0.6.3 (2018-03-18)
++++++++++++++++++
* Fix incorrect formset detection logic

0.6.4 (2018-03-26)
++++++++++++++++++
* Optimize listview media when create & edit are set to legacy
* Breadcrumbs obeys custom page title
* Fix bug in ListView.media optimization
* Introduce permissions_required attribute
* PopupCrudViewSet.get_page_title now used in for all CRUD(legacy) views

0.7.0 (2018-06-20)
++++++++++++++++++
* Add support for ``pk_url_kwarg``, ``slug_field``, ``slug_url_kwarg`` &
  ``context_object_name`` ViewSet attributes.
* Improve documentation

0.7.1 (2018-06-20)
++++++++++++++++++
* Update release history

0.8.0 (2018-10-31)
++++++++++++++++++
* Allow html tags in custom column headers; hide Action column if there're
  no item actions
* Support view template context data in ViewSet

0.9.0 (2019-12-25)
++++++++++++++++++
* Django 3.0 support

0.10.0 (2019-12-26)
+++++++++++++++++++
* Fix rendering bugs owing to changes in Django 3.0

0.11.0 (2019-12-26)
+++++++++++++++++++
* Bump min Django ver to 2.2.8

0.12.0 (2019-12-26)
+++++++++++++++++++
* Fix README formatting errors