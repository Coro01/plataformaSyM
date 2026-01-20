from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError 
from django.forms import TimeInput 
from datetime import timedelta, datetime, date, time
import re

from django.contrib.auth import get_user_model
try:
    from .models import SolicitudLibre, RegistroJornada
except ImportError:
    pass

User = get_user_model() 

# --- REGLAS DE NEGOCIO (Necesarias para la validación clean()) ---
HORA_INICIO_OFICIAL = time(7, 0)
DURACION_ALMUERZO = timedelta(minutes=30)
JORNADA_ESTANDAR = timedelta(hours=9, minutes=30)
UMBRAL_ALMUERZO = timedelta(hours=6)

def calcular_horas_jornada(fecha: date, entrada: time, salida: time):
    """
    Calcula las horas netas y horas extra basándose en las reglas de negocio.
    """
    
    # Combinar fecha y hora para obtener objetos datetime para cálculo
    entrada_dt = datetime.combine(fecha, entrada)
    salida_dt = datetime.combine(fecha, salida)
    hora_inicio_dt = datetime.combine(fecha, HORA_INICIO_OFICIAL)

    # Regla: No se cuentan horas antes de la HORA_INICIO_OFICIAL
    if entrada_dt < hora_inicio_dt:
        entrada_dt = hora_inicio_dt

    # Regla: Permitir cruce de medianoche
    if salida_dt <= entrada_dt:
        if (salida_dt - entrada_dt).total_seconds() < 0:
            salida_dt += timedelta(days=1)
        elif entrada_dt == salida_dt:
            # Duración neta 0, resta la jornada estándar
            return timedelta(0), JORNADA_ESTANDAR * -1 
        else:
            # Duración neta 0, resta la jornada estándar (caso de error no específico)
            return timedelta(0), JORNADA_ESTANDAR * -1 

    duracion_bruta = salida_dt - entrada_dt
    
    # Regla: Descuento de almuerzo (30 minutos si la duración bruta >= 6 horas)
    if duracion_bruta >= UMBRAL_ALMUERZO:
        duracion_neta = duracion_bruta - DURACION_ALMUERZO
    else:
        duracion_neta = duracion_bruta

    if duracion_neta < timedelta(0):
        duracion_neta = timedelta(0) 

    # Cálculo de horas extras (puede ser positivo o negativo)
    horas_extras = duracion_neta - JORNADA_ESTANDAR
    
    return duracion_neta, horas_extras
# -------------------------------------------------------------

# =================================================================
# 1. Formulario para Carga de Archivos
# =================================================================
class UploadFileForm(forms.Form):
    # ¡CRÍTICO! Cambiamos 'file' a 'archivo' para que coincida con views.py
    archivo = forms.FileField(label='Selecciona el archivo Excel de Jornadas:')

# =================================================================
# 2. Formulario para Solicitud de Días Libres
# =================================================================
class SolicitudLibreForm(forms.ModelForm):
    # Campo temporal para la entrada de horas (string HH:MM)
    horas_solicitadas_input = forms.CharField(
        label='Horas de Compensación Solicitadas (HH:MM)',
        max_length=5,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: 01:00 (1 hora)', 'class': 'form-control'})
    )

    class Meta:
        model = SolicitudLibre
        # Excluimos 'horas_solicitadas' (DurationField) para asignarlo manualmente en save()
        fields = ['fecha_libre', 'motivo']
        widgets = {
            'fecha_libre': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'motivo': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean_horas_solicitadas_input(self):
        """Convierte la cadena HH:MM a un objeto timedelta y valida el formato."""
        horas_str = self.cleaned_data['horas_solicitadas_input']

        if not re.match(r'^\d{1,2}:\d{2}$', horas_str):
            raise forms.ValidationError("El formato debe ser HH:MM (ej. 01:30).")

        try:
            h, m = map(int, horas_str.split(':'))

            if h < 0 or m < 0 or m >= 60:
                raise forms.ValidationError("Valores de horas/minutos inválidos (Mín 00:01, Minutos máx 59).")

            if h == 0 and m == 0:
                raise forms.ValidationError("La duración debe ser mayor a cero.")

            # Devolvemos el timedelta para clean()
            return timedelta(hours=h, minutes=m) 
        except ValueError:
            raise forms.ValidationError("Formato incorrecto. Por favor, use HH:MM.")

    def save(self, commit=True):
        """Asigna el timedelta limpiado al campo 'horas_solicitadas' del modelo."""
        instance = super().save(commit=False)
        # Aquí usamos el valor limpio (timedelta) devuelto por clean_horas_solicitadas_input
        instance.horas_solicitadas = self.cleaned_data['horas_solicitadas_input']
        if commit:
            instance.save()
        return instance


# =================================================================
# 3. Formulario para Edición de Registro de Jornada (CONSOLIDADO)
# =================================================================
class RegistroJornadaForm(forms.ModelForm):
    
    # 💡 NUEVO CAMPO: Solo para visualizar la fecha (Solución al problema de fecha)
    fecha_display = forms.DateField(
        label='Fecha del Registro',
        widget=forms.DateInput(attrs={'type': 'text', 'readonly': 'readonly', 'class': 'form-control'}),
        required=False 
    )
    
    class Meta:
        model = RegistroJornada 
        fields = ('empleado', 'fecha', 'entrada', 'salida')
        
        widgets = {
            # Se usa TimeInput para asegurar que se muestren los valores de hora
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'entrada': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'salida': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        # 1. ESENCIAL: EXTRAER Y REMOVER EL ARGUMENTO PERSONALIZADO 'user'
        self.user = kwargs.pop('user', None) 

        # 2. CRUCIAL: Llamar al constructor base ANTES de usar self.fields
        super().__init__(*args, **kwargs)

        # 3. 💡 FIX para el ERROR DE VALIDACIÓN: Hacer los campos de hora opcionales
        # Aunque entrada es requerida en el modelo, la hacemos opcional en el formulario
        # para manejar el envío sin cambios.
        self.fields['entrada'].required = False 
        self.fields['salida'].required = False
        
        # 4. 💡 FIX para la FECHA: Habilitar la visualización
        if self.instance and self.instance.fecha:
            # Ocultamos el campo 'fecha' original del modelo
            self.fields['fecha'].widget = forms.HiddenInput() 
            
            # Inicializamos 'fecha_display' con el valor de la instancia formateado
            self.fields['fecha_display'].initial = self.instance.fecha.strftime('%d/%m/%Y') 

        # 5. Lógica de 'empleado'
        self.fields['empleado'].widget.attrs.update({'class': 'form-control'})
        
        if self.user and not self.user.is_staff:
            self.fields['empleado'].widget = forms.HiddenInput()
            # Aseguramos que el valor inicial sea el del registro actual o el usuario logueado
            if self.instance and self.instance.pk:
                self.fields['empleado'].initial = self.instance.empleado 
            else:
                self.fields['empleado'].initial = self.user
                
        elif self.user and self.user.is_staff:
             self.fields['empleado'].queryset = User.objects.all().order_by('username')
# =================================================================
# 4. Formulario para Login de Empleados
# =================================================================
class EmpleadoLoginForm(AuthenticationForm):
    """Formulario de Login que utiliza Bootstrap classes para el diseño."""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'class': 'form-control',
            'placeholder': 'Usuario o Nombre de Empleado'
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )
