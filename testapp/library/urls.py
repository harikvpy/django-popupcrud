from django.conf.urls import url
from library import views

urlpatterns = [
    url(r'^books/$', views.BookList.as_view(), name='books-list'),
    url(r'^books/new/$', views.CreateBook.as_view(), name='new-book'),
    #url(r'^books/(?P<pk>\d+)/$', views.BookDetail.as_view(), name='book-detail'),
    url(r'^books/(?P<pk>\d+)/edit/$', views.EditBook.as_view(), name='edit-book'),
    url(r'^books/(?P<pk>\d+)/delete/$', views.DeleteBook.as_view(), name='delete-book'),
    url(r'^authors/$', views.AuthorList.as_view(), name='authors-list'),
    url(r'^authors/new/$', views.CreateAuthor.as_view(), name='new-author'),
    url(r'^authors/(?P<pk>\d+)/edit/$', views.EditAuthor.as_view(), name='edit-author'),
]
