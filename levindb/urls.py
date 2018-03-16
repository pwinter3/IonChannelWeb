from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^ajax/load-proteins/', views.load_proteins, name='ajax_load_proteins'),
]

