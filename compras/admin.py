# tu_app/admin.py - CÓDIGO COMPLETO

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Inventario,
    StockMovement,
    Factura,
    FacturaProducto,
)

# ==========================================================
# 1. ADMIN: INVENTARIO (EXISTENTE)
# ==========================================================
@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('Producto', 'CodigoProducto', 'Cantidad', 'MinimoAdmisible', 'Ubicacion')
    
    list_filter = ('Ubicacion',) 
    
    search_fields = ('Producto', 'CodigoProducto', 'Marca', 'Modelo') 
    
    readonly_fields = ('Cantidad',) 
    
    fieldsets = (
        (None, {
            'fields': ('CodigoProducto', 'Producto', 'Descripcion', 'Cantidad')
        }),
        ('Detalles', {
            'fields': ('Marca', 'Modelo', 'Ubicacion')
        }),
        ('Stock Mínimos y Máximos', {
            'fields': ('MinimoAdmisible', 'MaximoAdmisible')
        }),
        ('Precios', {
            'fields': ('PrecioGS', 'PrecioUSD', 'PrecioTotalGS')
        }),
    )

# ==========================================================
# 2. ADMIN: MOVIMIENTO DE STOCK (EXISTENTE)
# ==========================================================
@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo_movimiento', 'cantidad_movida', 'fecha_movimiento', 'motivo') 
    
    list_filter = ('tipo_movimiento', 'producto') 
    
    search_fields = ('producto__Producto', 'motivo') 
    
    list_per_page = 25
    
    readonly_fields = ('producto', 'tipo_movimiento', 'cantidad_movida', 'fecha_movimiento', 'motivo', 'costo_unitario')

    def has_add_permission(self, request):
        return False
       
    def has_delete_permission(self, request, obj=None):
        return False

# ==========================================================
# 3. ADMIN INLINE: Productos dentro de Factura (NUEVO)
# ==========================================================
class FacturaProductoInline(admin.TabularInline):
    """Muestra productos asociados directamente en la factura."""
    model = FacturaProducto
    extra = 1
    fields = ('producto', 'cantidad', 'precio_unitario', 'subtotal')
    readonly_fields = ('subtotal',)

# ==========================================================
# 4. ADMIN PRINCIPAL: Factura (NUEVO)
# ==========================================================
@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    """
    Administración de facturas procesadas.
    Integración con Inventario existente.
    """
    list_display = ('numero_factura', 'proveedor', 'fecha_emision', 'monto_total', 'estado_badge', 'usuario')
    list_filter = ('estado', 'fecha_emision', 'fecha_carga')
    search_fields = ('numero_factura', 'proveedor', 'ruc_proveedor')
    readonly_fields = ('fecha_carga', 'fecha_procesamiento', 'usuario', 'preview_pdf')
    date_hierarchy = 'fecha_emision'
    inlines = [FacturaProductoInline]
    
    fieldsets = (
        ('Información de Factura', {
            'fields': ('numero_factura', 'proveedor', 'ruc_proveedor')
        }),
        ('Fechas', {
            'fields': ('fecha_emision', 'fecha_carga', 'fecha_procesamiento')
        }),
        ('Montos', {
            'fields': ('monto_total',)
        }),
        ('Archivos', {
            'fields': ('pdf_original', 'pdf_registro', 'preview_pdf')
        }),
        ('Control', {
            'fields': ('estado', 'usuario', 'observaciones')
        }),
    )
    
    def estado_badge(self, obj):
        """Muestra estado con colores."""
        colores = {
            'pendiente': '#FEF3C7',
            'procesada': '#DCFCE7',
            'cancelada': '#FEE2E2'
        }
        return format_html(
            '<span style="background-color: {}; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            colores.get(obj.estado, '#E5E7EB'),
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def preview_pdf(self, obj):
        """Permite descargar el PDF original."""
        if obj.pdf_original:
            return format_html(
                '<a href="{}" target="_blank" class="button">📥 Ver PDF Original</a>',
                obj.pdf_original.url
            )
        return "Sin archivo"
    preview_pdf.short_description = "Archivo"
    
    def get_readonly_fields(self, request, obj=None):
        # En edición, algunos campos son de solo lectura
        if obj:
            return self.readonly_fields + ('numero_factura', 'proveedor', 'ruc_proveedor')
        return self.readonly_fields

# ==========================================================
# 5. ADMIN: FacturaProducto (NUEVO)
# ==========================================================
@admin.register(FacturaProducto)
class FacturaProductoAdmin(admin.ModelAdmin):
    """
    Administración de la relación Factura-Producto.
    Integración con Inventario existente.
    """
    list_display = ('numero_factura_display', 'producto_display', 'cantidad', 'precio_unitario', 'subtotal')
    list_filter = ('factura__fecha_emision',)
    search_fields = ('factura__numero_factura', 'producto__Producto')
    readonly_fields = ('subtotal',)
    
    def numero_factura_display(self, obj):
        """Muestra el número de factura de forma legible."""
        return obj.factura.numero_factura
    numero_factura_display.short_description = 'Factura'
    
    def producto_display(self, obj):
        """Muestra el nombre del producto de forma legible."""
        return obj.producto.Producto
    producto_display.short_description = 'Producto'
# tu_app/admin.py - AGREGAR AL FINAL

from .models import Proveedor

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    """Administración de proveedores."""
    
    list_display = ('ruc', 'nombre', 'email', 'telefono', 'activo')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('ruc', 'nombre', 'email')
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('ruc', 'nombre', 'activo')
        }),
        ('Contacto', {
            'fields': ('email', 'telefono', 'contacto')
        }),
        ('Dirección', {
            'fields': ('direccion',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """Evitar borrado accidental - solo desactivar."""
        return False