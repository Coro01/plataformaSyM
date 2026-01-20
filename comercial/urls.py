# En comercial/urls.py
from django.urls import path
from . import views

app_name = 'comercial'

urlpatterns = [
    path('', views.comercial_view, name='dashboard'), 
    path('clientes/', views.clientes_view, name='clientes'), 
    path('reportes/', views.reportes_view, name='reportes'), 
    path('pedidos/', views.pedidos_view, name='pedidos'), 
]
