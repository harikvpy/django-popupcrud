from django.conf.urls import url, include
from django.contrib import admin

from library.models import Author
from library.admin import AuthorAdmin
from library import views

author_admin = AuthorAdmin(Author, admin.site)

urlpatterns = [
    url(r'^authors/$', views.AuthorCrudViewset.list(), name='authors'),
    url(r'^authors/new/$', views.AuthorCrudViewset.create(), name='new-author'),
    url(r'^authors/(?P<pk>\d+)/edit/$', views.AuthorCrudViewset.update(), name='edit-author'),
    url(r'^authors/(?P<pk>\d+)/delete/$', views.AuthorCrudViewset.delete(), name='delete-author'),

    url(r'^books/$', views.BookCrudViewset.list(), name='books'),
    url(r'^books/new/$', views.BookCrudViewset.create(), name='new-book'),
    url(r'^books/(?P<pk>\d+)/edit/$', views.BookCrudViewset.update(), name='edit-book'),
    url(r'^books/(?P<pk>\d+)/delete/$', views.BookCrudViewset.delete(), name='delete-book'),

    url(r'^rating/author/$', views.AuthorRatingView.as_view(), name='author-rating'),
    url(r'^rating/book/$', views.BookRatingView.as_view(), name='book-rating'),
    url(r'^mro/$', views.MultipleRelatedObjectDemoView.as_view(), name='multi-related-object-demo'),
]

urlpatterns += [
    url(r'^writers/', include((author_admin.get_urls(), 'library'), namespace='writers')),
]
