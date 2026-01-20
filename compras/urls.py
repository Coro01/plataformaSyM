# compras/urls.py

from django.urls import path
from . import views

# ¡IMPORTANTE! El namespace es 'compras'.
app_name = 'compras'

urlpatterns = [
    # 1. Dashboard Principal del Módulo de Compras
    path('dashboard/', views.compras_dashboard, name='compras_dashboard'), 
    
    # 2. Vistas de Inventario y Depósito
    path('deposito/', views.deposito_view, name='deposito'), 
    
    # 3. Detalle de Producto
    path('detalle/<str:pk>/', views.detalle_producto_view, name='detalle_producto'),

    # 4. Dashboard Específico del Depósito
    path('deposito_dashboard/', views.deposito_dashboard_view, name='deposito_dashboard'), 
    
    # 5. Vistas de Movimiento de Stock
    path('stock/ingreso/', views.ingreso_stock_view, name='ingreso_stock'),
    path('stock/egreso/', views.egreso_stock_view, name='egreso_stock'),
    
    # 6. Vistas de Adquisiciones y Facturación
    path('facturas/', views.facturas_view, name='facturas'),
    path('facturas/guardar/', views.guardar_factura, name='guardar_factura'),
    path('facturas/manual/', views.cargar_factura_manual, name='cargar_factura_manual'),  # ✅ RUTA CORREGIDA
    path('facturas/<int:factura_id>/pdf/ver/', views.ver_factura_pdf, name='ver_factura_pdf'),
    path('facturas/<int:factura_id>/pdf/descargar/', views.descargar_factura_pdf, name='descargar_factura_pdf'),
    path('facturas/listado/', views.listado_facturas, name='listado_facturas'),
    
    # 7. Vistas de Adquisiciones
    path('importaciones/', views.importaciones_view, name='importaciones'),
    path('locales/', views.locales_view, name='locales'),
    
    # 8. Vistas de Creación de Productos
    path('crear/', views.crear_producto_view, name='crear_producto'),
    
    # 9. Vistas de Gestión de Proveedores
    path('proveedores/', views.gestionar_proveedores, name='gestionar_proveedores'),
    path('proveedores/<str:ruc>/eliminar/', views.eliminar_proveedor, name='eliminar_proveedor'),
    
    # 10. APIs AJAX
    path('api/buscar/', views.search_products_ajax, name='search_products_ajax'),
    path('api/detalle-ajax/', views.get_product_details_ajax, name='get_product_details_ajax'),
    path('editar-producto/<str:pk>/', views.editar_producto_view, name='editar_producto'),
]