from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^ajax/load-proteins/', views.load_proteins, name='ajax_load_proteins'),
    url(r'^ajax/load-protein-desc/', views.load_protein_desc, name='ajax_load_protein_desc'),
    url(r'^ajax/show-results/', views.make_results_table, name='ajax_show_results'),
]
