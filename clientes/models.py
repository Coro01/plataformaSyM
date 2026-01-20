from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import os
from django.db.models.signals import post_delete
from django.dispatch import receiver


def reporte_file_path(instance, filename):
    """Genera la ruta para archivos adjuntos del reporte"""
    # Corregido: Acceder a través de la relación 'reporte'
    return f'reportes/{instance.reporte.numero_reporte}/{filename}'

class Empresa(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    ruc = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class ReporteAsistencia(models.Model):
    numero_reporte = models.CharField(max_length=20, unique=True, editable=False)
    fecha_generacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de generación')
    fecha_asistencia = models.DateField(verbose_name='Fecha de asistencia')
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='reportes')
    maquina = models.CharField(max_length=200)
    persona_solicita = models.CharField(max_length=200)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reportes_creados')
    
    problema = models.TextField()
    problema_encontrado = models.TextField()
    solucion = models.TextField()
    
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Reporte de Asistencia'
        verbose_name_plural = 'Reportes de Asistencia'
        # Corregido: Se cambió '-fecha' por '-fecha_asistencia'
        ordering = ['-fecha_asistencia']
    
    def __str__(self):
        return f"{self.numero_reporte} - {self.empresa.nombre}"
    
    def save(self, *args, **kwargs):
            if not self.numero_reporte:
                # Usamos la fecha de asistencia para el número o la actual
                # para mantener consistencia con el día del servicio
                fecha_str = self.fecha_asistencia.strftime('%Y%m%d') if self.fecha_asistencia else timezone.now().strftime('%Y%m%d')
                
                # Usamos select_for_update si estuvieras en una transacción, 
                # pero para nivel básico esto funciona bien:
                ultimo_reporte = ReporteAsistencia.objects.filter(
                    numero_reporte__startswith=f'AST-{fecha_str}'
                ).order_by('-numero_reporte').first()
                
                if ultimo_reporte:
                    try:
                        # Obtenemos el último número de los últimos 4 dígitos
                        ultimo_num = int(ultimo_reporte.numero_reporte.split('-')[-1])
                        nuevo_num = ultimo_num + 1
                    except (ValueError, IndexError):
                        nuevo_num = 1
                else:
                    nuevo_num = 1
                
                self.numero_reporte = f'AST-{fecha_str}-{nuevo_num:04d}'
            
            super().save(*args, **kwargs)

class ArchivoReporte(models.Model):
    TIPO_CHOICES = [
        ('foto', 'Fotografía'),
        ('pdf', 'Documento PDF'),
    ]
    
    reporte = models.ForeignKey(ReporteAsistencia, on_delete=models.CASCADE, related_name='archivos')
    archivo = models.FileField(
        upload_to=reporte_file_path,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf'])]
    )
    # Corregido: blank=True para que no falle en validación de formularios
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, blank=True)
    descripcion = models.CharField(max_length=200, blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Archivo Adjunto'
        verbose_name_plural = 'Archivos Adjuntos'
        ordering = ['-fecha_subida']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.reporte.numero_reporte}"
    
    def save(self, *args, **kwargs):
        if not self.tipo:
            ext = os.path.splitext(self.archivo.name)[1].lower()
            self.tipo = 'pdf' if ext == '.pdf' else 'foto'
        super().save(*args, **kwargs)
    
    def auto_delete_file_on_delete(sender, instance, **kwargs):
        """Borra el archivo físico cuando se elimina el registro de la BD"""
        if instance.archivo:
            if os.path.isfile(instance.archivo.path):
                os.remove(instance.archivo.path)