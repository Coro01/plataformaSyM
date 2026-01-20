from django.contrib import admin
from django.utils.html import format_html
from .models import Empresa, ReporteAsistencia, ArchivoReporte

class ArchivoReporteInline(admin.TabularInline):
    model = ArchivoReporte
    extra = 1
    fields = ['archivo', 'ver_archivo', 'tipo', 'descripcion']
    readonly_fields = ['tipo', 'ver_archivo', 'fecha_subida']

    def ver_archivo(self, obj):
        if obj.archivo:
            # Si es imagen, muestra miniatura; si es PDF, muestra icono
            if obj.archivo.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                return format_html('<img src="{}" style="width: 50px; height: auto; border-radius: 5px;" />', obj.archivo.url)
            return format_html('<i class="bi bi-file-pdf text-danger" style="font-size: 20px;"></i> PDF')
        return "-"
    ver_archivo.short_description = 'Previsualización'

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'ruc', 'telefono', 'activo', 'fecha_creacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['nombre', 'ruc']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información Básica', {'fields': ('nombre', 'ruc', 'activo')}),
        ('Contacto', {'fields': ('direccion', 'telefono', 'email')}),
    )

@admin.register(ReporteAsistencia)
class ReporteAsistenciaAdmin(admin.ModelAdmin):
    # Mostramos el número de reporte y el cliente de forma destacada
    list_display = ['numero_reporte', 'fecha_asistencia', 'empresa', 'maquina', 'usuario']
    list_filter = ['fecha_asistencia', 'empresa', 'usuario']
    search_fields = ['numero_reporte', 'empresa__nombre', 'maquina', 'persona_solicita']
    readonly_fields = ['numero_reporte', 'fecha_generacion', 'fecha_actualizacion']
    date_hierarchy = 'fecha_asistencia'
    inlines = [ArchivoReporteInline]
    
    # Organización lógica de campos
    fieldsets = (
        ('Encabezado y Control', {
            'fields': (('numero_reporte', 'fecha_asistencia'), 'usuario'),
            'description': 'Información básica del registro y técnico responsable.'
        }),
        ('Datos del Cliente', {
            'fields': (('empresa', 'persona_solicita'),),
        }),
        ('Diagnóstico Técnico', {
            'fields': ('maquina', 'problema', 'problema_encontrado'),
            'classes': ('wide',),
        }),
        ('Resolución del Servicio', {
            'fields': ('solucion',),
        }),
        ('Metadata', {
            'fields': (('fecha_generacion', 'fecha_actualizacion'),),
            'classes': ('collapse',) # Oculto por defecto
        }),
    )

    def save_model(self, request, obj, form, change):
        # Asigna el usuario actual automáticamente si es un reporte nuevo
        if not change:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)

@admin.register(ArchivoReporte)
class ArchivoReporteAdmin(admin.ModelAdmin):
    list_display = ['reporte', 'tipo_icon', 'descripcion', 'fecha_subida']
    list_filter = ['tipo', 'fecha_subida']
    search_fields = ['reporte__numero_reporte', 'descripcion']
    readonly_fields = ['tipo', 'fecha_subida']

    def tipo_icon(self, obj):
        if obj.tipo == 'PDF':
            return format_html('<b style="color: #d9534f;">📄 PDF</b>')
        return format_html('<b style="color: #5bc0de;">🖼️ Imagen</b>')
    tipo_icon.short_description = 'Tipo de Archivo'