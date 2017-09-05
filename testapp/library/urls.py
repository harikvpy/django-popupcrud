from django.conf.urls import url
from library import views

urlpatterns = [
    url(r'^authors/$', views.AuthorList.as_view(), name='authors-list'),
    url(r'^authors/new/$', views.CreateAuthor.as_view(), name='new-author'),
    url(r'^authors/(?P<pk>\d+)/edit/$', views.EditAuthor.as_view(), name='edit-author'),
    url(r'^books/$', views.BookList.as_view(), name='books-list'),
    url(r'^books/new/$', views.CreateBook.as_view(), name='new-book'),
    #url(r'^books/(?P<pk>\d+)/$', views.BookDetail.as_view(), name='book-detail'),
    url(r'^books/(?P<pk>\d+)/edit/$', views.EditBook.as_view(), name='edit-book'),
    url(r'^books/(?P<pk>\d+)/delete/$', views.DeleteBook.as_view(), name='delete-book'),

    url(r'^writers/$', views.AuthorCrudViewset.list(), name='writers-list'),
    url(r'^writers/new/$', views.AuthorCrudViewset.create(), name='new-writer'),
    url(r'^writers/(?P<pk>\d+)/edit/$', views.AuthorCrudViewset.update(), name='edit-writer'),

    url(r'^titles/$', views.BookCrudViewset.list(), name='titles-list'),
    url(r'^titles/new/$', views.BookCrudViewset.create(), name='new-title'),
    url(r'^titles/(?P<pk>\d+)/edit/$', views.BookCrudViewset.update(), name='edit-title'),
    url(r'^titles/(?P<pk>\d+)/delete/$', views.BookCrudViewset.delete(), name='delete-title'),
]
