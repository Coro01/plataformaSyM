from django.urls import path
from . import views

app_name = 'rrhh'

urlpatterns = [
    # Nuevo Dashboard/Hub para RR.HH. - Este es el punto de entrada del módulo
    path('rrhh_dashboard', views.rrhh_dashboard_view, name='rrhh_dashboard'), # URL vacía para /rrhh/

    # Secciones internas del módulo RR.HH.
    path('salarios/', views.salarios_view, name='salarios'),
    path('vacaciones/', views.vacaciones_view, name='vacaciones'),
]