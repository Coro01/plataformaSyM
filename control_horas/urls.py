# En control_horas/urls.py
from django.urls import path
from . import views

# EL NAMESPACE DE TU APLICACIÓN ES CRUCIAL
app_name = 'control_horas' 

urlpatterns = [
# Login y Logout
    path('SYM/login/', views.EmpleadoLoginView.as_view(), name='login'),
    path('SYM/logout', views.logout_confirm_view, name='logout_confirm'), # Asegúrate de tener esta vista

    # 1. DASHBOARD GLOBAL (Punto de entrada principal)
    path('SYM/inicio/', views.main_dashboard_view, name='main_dashboard'), 
    
    # 2. HUB Nivel 2: CONTROL HORAS
    path('SYM/rrhh/resumen', views.saldo_horas_view, name='saldo_horas'), # <-- Usamos esta como la página principal del módulo
    # 🌟 CALENDARIOS SEPARADOS MANTENIDOS 🌟
    path('SYM/rrhh/horas/', views.calendario_horas_view, name='calendario_horas'),
    path('SYM/rrhh/solicitudes/', views.calendario_solicitudes_view, name='calendario_solicitudes'),
    
    # 🌟 RUTA PARA LA EDICIÓN DE REGISTROS 🌟
    path('SYM/rrhh/editar/<int:registro_id>/', views.editar_registro_jornada_view, name='editar_registro'),
    
    # API ENDPOINT (Usado por el Calendario de Horas)
    path('api/jornada/', views.journal_data_api, name='journal_data_api'),
    
    # SOLICITUDES
    path('SYM/rrhh/solicitar/', views.solicitar_dia_libre_view, name='solicitar_dia_libre'),
    path('SYM/rrhh/gestion/', views.gestion_solicitudes_view, name='gestion_solicitudes'),
    path('SYM/rrhh/gestion/<int:solicitud_id>/', views.aprobar_rechazar_solicitud, name='aprobar_rechazar_solicitud'),
 
    path('SYM/rrhh/cargar/', views.upload_excel_view, name='upload_excel'),
    path('SYM/rrhh/exportar/', views.export_jornadas_csv, name='exportar_registros'),

    path('SYM/rrhh/control_dashboard/', views.control_horas_dashboard, name='control_dashboard'),
    
    
]