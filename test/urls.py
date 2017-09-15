from django.conf.urls import url
import views

urlpatterns = [
    url(r'^authors/$', views.AuthorCrudViewset.list(), name='authors'),
    url(r'^authors/new/$', views.AuthorCrudViewset.create(), name='new-author'),
    url(r'^authors/(?P<pk>\d+)/edit/$', views.AuthorCrudViewset.update(), name='edit-author'),
    url(r'^authors/(?P<pk>\d+)/delete/$', views.AuthorCrudViewset.delete(), name='delete-author'),
]

