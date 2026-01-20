# forms.py

from django import forms
from .models import Inventario, StockMovement 
from django.core.exceptions import ValidationError
from decimal import Decimal
from django import forms
from .models import Factura, FacturaProducto, Inventario
from django.core.exceptions import ValidationError
from decimal import Decimal

# Estilo de clases para los widgets basados en TailwindCSS (form-input-focus)
WIDGET_ATTRS = {'class': 'form-input-focus w-full p-2 border rounded-lg focus:ring-1'}


# =================================================================
# 1. Formulario para Ingreso de Stock (Compra)
# =================================================================
class IngresoStockForm(forms.ModelForm): 
    """Formulario para registrar un ingreso de stock usando Autocomplete."""
    
    # Campo auxiliar (NO mapeado al modelo StockMovement) para el Autocomplete
    codigo_producto = forms.CharField(
        label='Buscar Producto (Código o Nombre)',
        required=True,
        widget=forms.TextInput(attrs={
            **WIDGET_ATTRS, 
            'placeholder': 'Empieza a escribir el código o nombre...',
            # CRÍTICO: Este ID es usado por jQuery para el Autocomplete
            'id': 'codigo_producto', 
            'class': WIDGET_ATTRS['class'] + ' text-uppercase'
        })
    )
    
    # Campo del modelo: 'producto' (Se convierte en OCULTO, rellenado por JS con el PK)
    producto = forms.ModelChoiceField(
        queryset=Inventario.objects.all(),
        widget=forms.HiddenInput(), 
        required=True,
        label='Producto seleccionado' 
    )
    
    # Campo auxiliar que no está en el modelo, para registrar el costo
    costo_unitario_registro = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Costo Unitario de la Compra', 'step': '0.01'}),
        label='Costo Unitario de Compra'
    )
    
    class Meta:
        model = StockMovement
        fields = ['producto', 'cantidad_movida', 'motivo']
        widgets = {
            'cantidad_movida': forms.NumberInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Cantidad recibida', 'step': '0.01'}),
            'motivo': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 3, 'placeholder': 'Nro. Factura, Nro. Lote, Nro. OC, o Proveedor'}),
        }
        labels = {
            'cantidad_movida': 'Cantidad Ingresada',
            'motivo': 'Referencia de Ingreso',
        }
        
    def clean(self):
        cleaned_data = super().clean()
        
        # Validación CRÍTICA: Asegurar que el campo oculto 'producto' fue llenado
        if not cleaned_data.get('producto'):
            self.add_error('codigo_producto', 
                           "Debe seleccionar un producto válido de la lista de autocompletado.")
            
        costo = cleaned_data.get('costo_unitario_registro')
        if costo is not None and costo <= Decimal('0.00'):
             self.add_error('costo_unitario_registro', "El costo unitario debe ser mayor a cero.")

        cantidad = cleaned_data.get('cantidad_movida')
        if cantidad is not None and cantidad <= 0:
            self.add_error('cantidad_movida', "La cantidad ingresada debe ser un valor positivo.")
            
        return cleaned_data

# =================================================================
# 2. Formulario para Egreso de Stock (Venta/Uso)
# =================================================================
class EgresoStockForm(forms.ModelForm): 
    """Formulario para registrar un egreso de stock."""
    
    producto = forms.ModelChoiceField(
        # Usamos 'Cantidad' y 'Producto' según la convención de tu modelo
        queryset=Inventario.objects.filter(Cantidad__gt=0).order_by('Producto'),
        widget=forms.Select(attrs=WIDGET_ATTRS),
        label='Producto/Artículo a Egresar'
    )
    
    cantidad_movida = forms.FloatField(
        min_value=0.01,
        widget=forms.NumberInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Cantidad a retirar', 'step': '0.01'}),
        label='Cantidad Egresada'
    )
    
    class Meta:
        model = StockMovement
        fields = ['producto', 'cantidad_movida', 'motivo']
        widgets = {
            'motivo': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 3, 'placeholder': 'Nro. Venta, Orden de Uso, o Descarte y Observaciones'}),
        }
        labels = {
            'motivo': 'Referencia y Observaciones',
        }
        
    def clean_cantidad_movida(self):
        """Validar que la cantidad no exceda el stock disponible."""
        cantidad = self.cleaned_data['cantidad_movida']
        producto = self.cleaned_data.get('producto')
        
        if producto:
            # CRÍTICO: Usamos 'Cantidad' (con mayúscula) para acceder al campo de stock de Inventario
            if cantidad > producto.Cantidad: 
                raise ValidationError(
                    f"La cantidad a egresar ({cantidad:.2f}) excede el stock disponible ({producto.Cantidad:.2f})."
                )
        return cantidad
class FacturaProductoForm(forms.ModelForm):
    """
    Formulario para asociar productos del Inventario existente a una factura.
    """
    
    # Usar el Inventario existente con el campo CodigoProducto
    producto = forms.ModelChoiceField(
        queryset=Inventario.objects.all().order_by('Producto'),
        widget=forms.Select(attrs=WIDGET_ATTRS),
        label='Producto del Inventario'
    )
    
    cantidad = forms.FloatField(
        min_value=0.01,
        widget=forms.NumberInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Cantidad', 'step': '0.01'}),
        label='Cantidad Recibida'
    )
    
    precio_unitario = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        # CORREGIDO: Usar NumberInput en lugar de DecimalInput
        widget=forms.NumberInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Precio unitario', 'step': '0.01'}),
        label='Precio Unitario'
    )
    
    class Meta:
        model = FacturaProducto
        fields = ['producto', 'cantidad', 'precio_unitario']
    
    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad and cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor a 0')
        return cantidad
    
    def clean_precio_unitario(self):
        precio = self.cleaned_data.get('precio_unitario')
        if precio and precio <= 0:
            raise ValidationError('El precio debe ser mayor a 0')
        return precio


# ==========================================================
# 4. FORMULARIO PRINCIPAL PARA FACTURA (Lectura/Edición básica)
# ==========================================================
class FacturaForm(forms.ModelForm):
    """
    Formulario para ver/editar datos básicos de una factura.
    Los datos principales se extraen del PDF.
    """
    
    class Meta:
        model = Factura
        fields = [
            'numero_factura',
            'proveedor',
            'ruc_proveedor',
            'fecha_emision',
            'monto_total',
            'pdf_original',
            'observaciones'
        ]
        widgets = {
            'numero_factura': forms.TextInput(attrs={
                'class': 'form-input-focus w-full p-2 border rounded-lg',
                'placeholder': 'Ej: FAC-001-2024',
                'readonly': True  # Se genera automáticamente
            }),
            'proveedor': forms.TextInput(attrs={
                'class': 'form-input-focus w-full p-2 border rounded-lg',
                'placeholder': 'Nombre de la empresa',
                'readonly': True  # Se extrae del PDF
            }),
            'ruc_proveedor': forms.TextInput(attrs={
                'class': 'form-input-focus w-full p-2 border rounded-lg',
                'placeholder': 'RUC (opcional)',
                'readonly': True
            }),
            'fecha_emision': forms.DateInput(attrs={
                'class': 'form-input-focus w-full p-2 border rounded-lg',
                'type': 'date',
                'readonly': True
            }),
            'monto_total': forms.NumberInput(attrs={
                'class': 'form-input-focus w-full p-2 border rounded-lg',
                'placeholder': '0.00',
                'step': '0.01',
                'readonly': True
            }),
            'pdf_original': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 p-2',
                'accept': 'application/pdf'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-input-focus w-full p-2 border rounded-lg',
                'rows': 3,
                'placeholder': 'Observaciones adicionales (opcional)'
            })
        }
    
    def clean_numero_factura(self):
        numero = self.cleaned_data.get('numero_factura', '').strip()
        if not numero:
            raise ValidationError('El número de factura es requerido')
        
        # Validar unicidad (excepto en edición)
        if self.instance.pk is None:
            if Factura.objects.filter(numero_factura=numero).exists():
                raise ValidationError('Ya existe una factura con este número')
        
        return numero
    
    def clean_monto_total(self):
        monto = self.cleaned_data.get('monto_total')
        if monto and monto <= 0:
            raise ValidationError('El monto debe ser mayor a 0')
        return monto


# ==========================================================
# 5. FORMSET PARA MÚLTIPLES PRODUCTOS EN UNA FACTURA
# ==========================================================
from django.forms import inlineformset_factory

FacturaProductoFormSet = inlineformset_factory(
    Factura,
    FacturaProducto,
    form=FacturaProductoForm,
    extra=1,
    can_delete=True
)