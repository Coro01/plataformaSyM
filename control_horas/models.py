# ============================================================
# control_horas/models.py - CON CAMPOS DE AUDITORÍA
# ============================================================

from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone

# ============================================================
# PERFIL DE EMPLEADO - CON NIVELES DE ACCESO
# ============================================================

class PerfilEmpleado(models.Model):
    NIVEL_CHOICES = (
        (1, 'Empleado (Solo registro propio)'),
        (2, 'Supervisor de Turno'),
        (3, 'Jefe de Departamento'),
        (4, 'Administrador RH'),
        (5, 'Superadmin'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    nro_afiliacion = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        unique=True, 
        verbose_name='Número de Afiliación/Cédula'
    )
    
    saldo_horas_comp = models.DurationField(
        default=timedelta(hours=0), 
        verbose_name='Saldo Horas Compensatorias'
    )
    
    # ✅ NUEVOS CAMPOS AGREGADOS
    nivel = models.IntegerField(
        choices=NIVEL_CHOICES,
        default=1,
        verbose_name='Nivel de Acceso'
    )
    
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Perfil Empleado'
        verbose_name_plural = 'Perfiles Empleados'

    def __str__(self):
        return f"{self.user.username} (Nivel {self.nivel})"
    
    def tiene_acceso(self, nivel_requerido):
        """Verifica si el usuario tiene el nivel de acceso requerido"""
        return self.activo and self.nivel >= nivel_requerido


# ============================================================
# REGISTRO DE JORNADA
# ============================================================

class RegistroJornada(models.Model):
    empleado = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateField()
    entrada = models.TimeField(null=True, blank=True)
    salida = models.TimeField(null=True, blank=True)
    horas_netas = models.DurationField(null=True, blank=True)
    horas_extras = models.DurationField(default=timedelta(hours=0), null=True, blank=True)
    salida_forzada = models.BooleanField(default=False)

    class Meta:
        unique_together = ('empleado', 'fecha')

    def __str__(self):
        return f'Jornada de {self.empleado.username} el {self.fecha}'


# ============================================================
# SOLICITUD DE DÍA LIBRE
# ============================================================

class SolicitudLibre(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
        ('CANCELADO', 'Cancelado'),
    )
    
    empleado = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_libre = models.DateField()
    horas_solicitadas = models.DurationField(default=timedelta(hours=8)) 
    estado = models.CharField(max_length=10, choices=ESTADOS, default='PENDIENTE')
    motivo = models.CharField(max_length=255, blank=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Solicitud de Día Libre"
        verbose_name_plural = "Solicitudes de Días Libres"
        unique_together = ('empleado', 'fecha_libre')

    def __str__(self):
        return f'{self.empleado.username} solicita libre el {self.fecha_libre} ({self.estado})'