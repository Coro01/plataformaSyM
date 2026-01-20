from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    # Dashboard
    path('', views.clientes_dashboard, name='dashboard'),
    
    # Reportes de Asistencia
    path('asistencias/', views.asistencias_lista, name='asistencias'),
    path('asistencias/nuevo/', views.crear_reporte, name='crear_reporte'),
    path('asistencias/<int:pk>/', views.detalle_reporte, name='detalle_reporte'),
    path('asistencias/<int:pk>/editar/', views.editar_reporte, name='editar_reporte'),
    path('asistencias/<int:pk>/eliminar/', views.eliminar_reporte, name='eliminar_reporte'),
    path('asistencias/<int:pk>/pdf/', views.reporte_pdf, name='reporte_pdf'),
    
    # Empresas
    path('empresas/', views.empresas_lista, name='empresas'),
    path('empresas/nueva/', views.crear_empresa, name='crear_empresa'),
 # Explorador de Red (Unidad Y:)
    path('documentos-red/', views.listar_documentos_red, name='listar_documentos_red'),
    # El uso de <path:...> permite recibir 'carpeta/archivo.pdf'
    path('documentos-red/ver/<path:nombre_archivo>', views.ver_documento_red, name='ver_documento_red'),
]