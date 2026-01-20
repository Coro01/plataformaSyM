# control_horas/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import PerfilEmpleado, RegistroJornada, SolicitudLibre

# ============================================================
# ADMIN PARA PERFILES DE EMPLEADOS
# ============================================================

@admin.register(PerfilEmpleado)
class PerfilEmpleadoAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'nro_afiliacion', 'nivel', 'activo', 'saldo_horas_comp')
    list_filter = ('nivel', 'activo')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'nro_afiliacion')
    
    fieldsets = (
        ('👤 Información Básica', {
            'fields': ('user', 'nro_afiliacion')
        }),
        ('🔐 Acceso y Permisos', {
            'fields': ('nivel', 'activo')
        }),
        ('⏱️  Horas Compensatorias', {
            'fields': ('saldo_horas_comp',)
        }),
    )
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Usuario'


# ============================================================
# ADMIN PARA REGISTROS DE JORNADA
# ============================================================

@admin.register(RegistroJornada)
class RegistroJornadaAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'fecha', 'entrada', 'salida', 'get_duracion', 'get_salida_forzada_badge')
    list_filter = ('fecha', 'salida_forzada', 'empleado')
    search_fields = ('empleado__username', 'empleado__first_name', 'empleado__last_name')
    date_hierarchy = 'fecha'
    
    fieldsets = (
        ('👤 Empleado', {
            'fields': ('empleado', 'fecha')
        }),
        ('⏰ Horario', {
            'fields': ('entrada', 'salida')
        }),
        ('📊 Cálculos', {
            'fields': ('horas_netas', 'horas_extras'),
            'classes': ('collapse',)
        }),
        ('⚠️  Indicadores', {
            'fields': ('salida_forzada',)
        }),
    )
    
    def get_duracion(self, obj):
        if obj.horas_netas:
            horas = obj.horas_netas.total_seconds() / 3600
            return f"{horas:.1f}h"
        return "—"
    get_duracion.short_description = 'Duración'
    
    def get_salida_forzada_badge(self, obj):
        if obj.salida_forzada:
            return format_html('<span style="background-color: #FF6347; color: white; padding: 3px 8px; border-radius: 3px;">⚠️ Salida Forzada</span>')
        return "✓ Normal"
    get_salida_forzada_badge.short_description = 'Estado'
    
    actions = ['marcar_como_salida_forzada', 'limpiar_salida_forzada']
    
    def marcar_como_salida_forzada(self, request, queryset):
        updated = queryset.update(salida_forzada=True)
        self.message_user(request, f'✅ {updated} registro(s) marcado(s).')
    marcar_como_salida_forzada.short_description = '🚨 Marcar como salida forzada'
    
    def limpiar_salida_forzada(self, request, queryset):
        updated = queryset.update(salida_forzada=False)
        self.message_user(request, f'✅ Marca eliminada de {updated} registro(s).')
    limpiar_salida_forzada.short_description = '✔️  Limpiar salida forzada'


# ============================================================
# ADMIN PARA SOLICITUDES DE DÍAS LIBRES
# ============================================================

@admin.register(SolicitudLibre)
class SolicitudLibreAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'fecha_libre', 'get_estado_badge', 'horas_solicitadas', 'fecha_solicitud')
    list_filter = ('estado', 'fecha_libre', 'fecha_solicitud')
    search_fields = ('empleado__username', 'empleado__first_name', 'empleado__last_name', 'motivo')
    date_hierarchy = 'fecha_libre'
    
    fieldsets = (
        ('👤 Solicitante', {
            'fields': ('empleado', 'fecha_libre')
        }),
        ('📝 Detalles', {
            'fields': ('horas_solicitadas', 'motivo', 'estado')
        }),
    )
    
    def get_estado_badge(self, obj):
        colores = {
            'PENDIENTE': '#FFD700',
            'APROBADO': '#90EE90',
            'RECHAZADO': '#FF6347',
            'CANCELADO': '#CCCCCC',
        }
        color = colores.get(obj.estado, '#CCCCCC')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    get_estado_badge.short_description = 'Estado'
    
    actions = ['aprobar_solicitudes', 'rechazar_solicitudes']
    
    def aprobar_solicitudes(self, request, queryset):
        updated = queryset.filter(estado='PENDIENTE').update(estado='APROBADO')
        self.message_user(request, f'✅ {updated} solicitud(es) aprobada(s).')
    aprobar_solicitudes.short_description = '✅ Aprobar'
    
    def rechazar_solicitudes(self, request, queryset):
        updated = queryset.filter(estado='PENDIENTE').update(estado='RECHAZADO')
        self.message_user(request, f'❌ {updated} solicitud(es) rechazada(s).')
    rechazar_solicitudes.short_description = '❌ Rechazar'


# Customización
admin.site.site_header = "Control de Horas"
admin.site.site_title = "Sistema de Control"
admin.site.index_title = "Administración"