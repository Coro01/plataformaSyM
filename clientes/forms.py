from django import forms
from .models import Empresa, ReporteAsistencia, ArchivoReporte

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'ruc', 'direccion', 'telefono', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la empresa'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUC (opcional)'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Dirección (opcional)'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono (opcional)'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@empresa.com'}),
        }

class ReporteAsistenciaForm(forms.ModelForm):
    # Campo extra para crear empresa al vuelo
    nueva_empresa = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control border-primary', 
            'placeholder': 'Escriba aquí si la empresa no está en la lista'
        }),
        label='O registrar nueva empresa'
    )
    
    class Meta:
        model = ReporteAsistencia
        # Campos actualizados incluyendo las dos descripciones de problemas
        fields = [
            'empresa', 'fecha_asistencia', 'maquina', 
            'persona_solicita', 'problema', 'problema_encontrado', 'solucion'
        ]
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select', 'id': 'id_empresa'}),
            'fecha_asistencia': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'  # Genera el selector de fecha nativo del navegador
            }),
            'maquina': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Torno CNC Haas ST-20'}),
            'persona_solicita': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de contacto'}),
            'problema': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3, 
                'placeholder': 'Lo que el cliente reporta (Síntomas)'
            }),
            'problema_encontrado': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3, 
                'placeholder': 'Diagnóstico técnico real tras la inspección'
            }),
            'solucion': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3, 
                'placeholder': 'Acciones realizadas para resolver el fallo'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['empresa'].queryset = Empresa.objects.filter(activo=True)
        self.fields['empresa'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        empresa = cleaned_data.get('empresa')
        nueva_empresa = cleaned_data.get('nueva_empresa')
        
        if not empresa and not nueva_empresa:
            raise forms.ValidationError('Seleccione una empresa o ingrese el nombre de una nueva.')
        
        # Lógica para crear la empresa si se usó el campo de texto
        if nueva_empresa and not empresa:
            empresa_obj, created = Empresa.objects.get_or_create(
                nombre=nueva_empresa.strip()
            )
            cleaned_data['empresa'] = empresa_obj
        
        return cleaned_data

class ArchivoReporteForm(forms.ModelForm):
    class Meta:
        model = ArchivoReporte
        fields = ['archivo', 'descripcion']
        widgets = {
            'archivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,image/*'  # Filtra archivos en la selección
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: Foto de placa, Manual PDF...'
            }),
        }

ArchivoReporteFormSet = forms.inlineformset_factory(
    ReporteAsistencia,
    ArchivoReporte,
    form=ArchivoReporteForm,
    extra=1,
    can_delete=True
)