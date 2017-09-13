from django.conf.urls import url
from library import views

urlpatterns = [
    url(r'^authors/$', views.AuthorCrudViewset.list(), name='authors'),
    url(r'^authors/new/$', views.AuthorCrudViewset.create(), name='new-author'),
    url(r'^authors/(?P<pk>\d+)/edit/$', views.AuthorCrudViewset.update(), name='edit-author'),
    url(r'^authors/(?P<pk>\d+)/delete/$', views.AuthorCrudViewset.delete(), name='delete-author'),

    url(r'^books/$', views.BookCrudViewset.list(), name='books'),
    url(r'^books/new/$', views.BookCrudViewset.create(), name='new-book'),
    url(r'^books/(?P<pk>\d+)/edit/$', views.BookCrudViewset.update(), name='edit-book'),
    url(r'^books/(?P<pk>\d+)/delete/$', views.BookCrudViewset.delete(), name='delete-book'),
]
