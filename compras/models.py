# tu_app/models.py - CÓDIGO COMPLETO

from django.db import models
from django.db.models import F
from django.utils import timezone 
from django.db import transaction
from django.contrib.auth.models import User
from decimal import Decimal

# ==========================================================
# 1. MODELO PRINCIPAL: INVENTARIO (MAESTRO DE STOCK)
# ==========================================================
class Inventario(models.Model):
    """
    Representa el inventario de materiales y productos en el depósito.
    """

    # --- CAMPOS DE IDENTIFICACIÓN ---
    CodigoProducto = models.CharField(
        max_length=50, 
        primary_key=True,
        db_column='CodigoProducto',
        verbose_name='SKU'
    )
    Producto = models.CharField(max_length=255, db_column='Producto', verbose_name='Nombre del Producto')
    Marca = models.CharField(max_length=100, db_column='Marca', verbose_name='Marca', null=True, blank=True)
    Modelo = models.CharField(max_length=100, db_column='Modelo', verbose_name='Modelo/Especificación', null=True, blank=True)
    Descripcion = models.TextField(db_column='Descripcion', verbose_name='Descripción Detallada', null=True, blank=True)
    
    # --- CAMPOS DE STOCK Y CONTROL ---
    Cantidad = models.FloatField(default=0.0, db_column='Cantidad', verbose_name='Stock Actual')
    Ubicacion = models.CharField(max_length=100, db_column='Ubicacion', verbose_name='Ubicación', null=True, blank=True)
    MinimoAdmisible = models.FloatField(default=0.0, db_column='MinimoAdmisible', verbose_name='Stock Mínimo')
    MaximoAdmisible = models.FloatField(default=0.0, db_column='MaximoAdmisible', verbose_name='Stock Máximo')
    
    # --- CAMPOS DE PRECIO ---
    PrecioGS = models.FloatField(default=0.0, db_column='PrecioGS', verbose_name='Precio Unitario (G$)')
    PrecioUSD = models.FloatField(default=0.0, db_column='PrecioUSD', verbose_name='Precio Unitario (USD)')
    
    PrecioTotalGS = models.FloatField(default=0.0, db_column='PrecioTotalGS', verbose_name='Valor Total de Stock (G$)')
    
    # --- CAMPO DE SEGUIMIENTO ---
    FechaUltimoMovimiento = models.DateTimeField(
        db_column='FechaUltimoMovimiento',
        verbose_name='Último Movimiento',
        default=timezone.now
    )

    class Meta:
        db_table = 'Inventario'
        verbose_name = 'Producto de Inventario'
        verbose_name_plural = 'Productos de Inventario'
    
    def __str__(self):
        return f"{self.CodigoProducto} - {self.Producto}"

    def save(self, *args, **kwargs):
        """Asegura que la cantidad no sea negativa y recalcula PrecioTotalGS."""
        if self.Cantidad < 0:
            self.Cantidad = 0.0
        
        self.PrecioTotalGS = self.Cantidad * self.PrecioGS 
        
        super().save(*args, **kwargs)

# ==========================================================
# 2. MODELO DE MOVIMIENTO DE STOCK (HISTÓRICO)
# ==========================================================
class StockMovement(models.Model):
    """
    Registra cada movimiento de entrada, salida o ajuste de inventario.
    """
    MOVEMENT_CHOICES = [
        ('ENTRADA', 'Entrada (Compra/Recepción)'),
        ('SALIDA', 'Salida (Venta/Uso)'),
        ('AJUSTE', 'Ajuste de Inventario'),
    ]

    producto = models.ForeignKey(
        Inventario, 
        on_delete=models.PROTECT, 
        db_column='CodigoProducto',
        to_field='CodigoProducto', 
        related_name='movimientos'
    )
    
    tipo_movimiento = models.CharField(
        max_length=10, 
        choices=MOVEMENT_CHOICES, 
        default='AJUSTE',
        verbose_name='Tipo de Movimiento'
    )

    cantidad_movida = models.FloatField(
        verbose_name='Cantidad'
    )
    
    fecha_movimiento = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha y Hora'
    )

    motivo = models.TextField(
        blank=True,
        null=True,
        verbose_name='Motivo/Referencia'
    )
    
    costo_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        verbose_name='Costo Unitario Registrado'
    )
    
    costo_total = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Costo Total del Movimiento (GS)"
    )
    
    tasa_cambio = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Tasa de Cambio (GS/USD)"
    )
    
    referencia = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Referencia/Factura"
    )

    class Meta:
        db_table = 'StockMovement'
        verbose_name = 'Movimiento de Stock'
        verbose_name_plural = 'Movimientos de Stock'
        ordering = ['-fecha_movimiento']

    def __str__(self):
        return f"{self.tipo_movimiento} de {self.cantidad_movida} de {self.producto.CodigoProducto}"

    def save(self, *args, **kwargs):
        """Solo guarda el registro histórico del movimiento."""
        super().save(*args, **kwargs)


class Proveedor(models.Model):
    """
    Tabla maestro de proveedores para correlacionar datos.
    """
    
    ruc = models.CharField(
        max_length=20,
        unique=True,
        primary_key=True,
        verbose_name='RUC'
    )
    
    nombre = models.CharField(
        max_length=255,
        verbose_name='Nombre de Empresa'
    )
    
    email = models.EmailField(
        verbose_name='Email',
        blank=True,
        null=True
    )
    
    telefono = models.CharField(
        max_length=20,
        verbose_name='Teléfono',
        blank=True,
        null=True
    )
    
    direccion = models.TextField(
        verbose_name='Dirección',
        blank=True,
        null=True
    )
    
    contacto = models.CharField(
        max_length=100,
        verbose_name='Persona de Contacto',
        blank=True,
        null=True
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    class Meta:
        db_table = 'Proveedor'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.ruc} - {self.nombre}"
# ==========================================================
# 3. MODELO NUEVO: FACTURA
# ==========================================================
class Factura(models.Model):
    """
    Modelo para registrar facturas de proveedores.
    Se integra con el modelo Inventario existente.
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Procesamiento'),
        ('procesada', 'Procesada'),
        ('cancelada', 'Cancelada'),
    ]

    # --- DATOS BÁSICOS ---
    numero_factura = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Número de Factura'
    )
    
    proveedor = models.ForeignKey(
            Proveedor, 
            on_delete=models.PROTECT, 
            related_name='facturas',
            verbose_name='Proveedor'
    )
    
    ruc_proveedor = models.CharField(
        max_length=20,
        verbose_name='RUC del Proveedor',
        blank=True,
        null=True
    )
    
    fecha_emision = models.DateField(
        verbose_name='Fecha de Emisión'
    )
    
    monto_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Monto Total'
    )
    
    # --- ARCHIVOS ---
    pdf_original = models.FileField(
        upload_to='facturas/originales/',
        verbose_name='PDF Original Cargado'
    )
    
  
    pdf_registro = models.FileField(
        upload_to='facturas/registros/%Y/%m/', 
        null=True, 
        blank=True,
        verbose_name='Archivo PDF'
    )
    
    # --- ESTADO Y CONTROL ---
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado'
    )
    
    fecha_carga = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Carga'
    )
    
    fecha_procesamiento = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de Procesamiento'
    )
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='Usuario que Cargó'
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observaciones'
    )

    class Meta:
        db_table = 'Factura'
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-fecha_emision']

    def __str__(self):
        return f"Factura {self.numero_factura} - {self.proveedor}"

# ==========================================================
# 4. MODELO NUEVO: DETALLE DE FACTURA (RELACIÓN)
# ==========================================================
class FacturaProducto(models.Model):
    """
    Relaciona los productos del inventario existente con los items de una factura.
    Punto de integración entre Factura e Inventario.
    """
    
    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name='productos',
        verbose_name='Factura'
    )
    
    # IMPORTANTE: Referencia a Inventario usando CodigoProducto
    producto = models.ForeignKey(
        Inventario,
        on_delete=models.PROTECT,
        to_field='CodigoProducto',
        related_name='facturas_recibidas',
        verbose_name='Producto del Inventario'
    )
    
    cantidad = models.FloatField(
        verbose_name='Cantidad Recibida'
    )
    
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Precio Unitario'
    )
    
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Subtotal'
    )

    class Meta:
        db_table = 'FacturaProducto'
        verbose_name = 'Producto en Factura'
        verbose_name_plural = 'Productos en Factura'
        indexes = [
            models.Index(fields=['factura']),
            models.Index(fields=['producto']),
        ]

    def __str__(self):
        return f"{self.factura.numero_factura} - {self.producto.Producto}"

    def save(self, *args, **kwargs):
        """Calcula el subtotal automáticamente."""
        self.subtotal = Decimal(self.cantidad) * self.precio_unitario
        super().save(*args, **kwargs)
# tu_app/models.py - AGREGAR ESTE MODELO AL FINAL

