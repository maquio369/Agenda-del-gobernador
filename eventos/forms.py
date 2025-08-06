# eventos/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Evento, Municipio
import pytz
from datetime import datetime

# eventos/forms.py - Reemplaza la clase EventoForm con esta versión corregida

class EventoForm(forms.ModelForm):
    """Formulario para crear y editar eventos"""
    
    class Meta:
        model = Evento
        fields = [
            'nombre', 'fecha_evento', 'municipio', 'lugar', 
            'es_festivo', 'responsable', 'asistio_gobernador', 
            'representante', 'descripcion', 'observaciones'
        ]
        widgets = {
            'fecha_evento': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local', 
                    'class': 'form-control',
                    'step': '300'  # Pasos de 5 minutos
                }
            ),
            'nombre': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Nombre del evento'}
            ),
            'lugar': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Lugar donde se realizará el evento'}
            ),
            'responsable': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Persona que organiza o invita'}
            ),
            'representante': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Nombre del representante'}
            ),
            'descripcion': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del evento (opcional)'}
            ),
            'observaciones': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observaciones del evento (opcional)'}
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar queryset de municipios
        self.fields['municipio'].queryset = Municipio.objects.filter(activo=True).order_by('nombre')
        self.fields['municipio'].empty_label = "Seleccione un municipio"
        
        # Hacer campos requeridos
        self.fields['nombre'].required = True
        self.fields['fecha_evento'].required = True
        self.fields['municipio'].required = True
        self.fields['lugar'].required = True
        self.fields['responsable'].required = True
        
        # Labels personalizados
        self.fields['nombre'].label = "Nombre del Evento"
        self.fields['fecha_evento'].label = "Fecha y Hora"
        self.fields['municipio'].label = "Municipio"
        self.fields['lugar'].label = "Lugar del Evento"
        self.fields['es_festivo'].label = "¿Es un evento festivo?"
        self.fields['responsable'].label = "Responsable/Organizador"
        self.fields['asistio_gobernador'].label = "¿Asistió el Gobernador?"
        self.fields['representante'].label = "Representante (si no asistió el Gobernador)"
        self.fields['descripcion'].label = "Descripción del Evento"
        self.fields['observaciones'].label = "Observaciones"
        
        # Help text
        self.fields['fecha_evento'].help_text = "Seleccione la fecha y hora exacta del evento"
        self.fields['es_festivo'].help_text = "Marque si es una celebración o evento festivo"
        self.fields['representante'].help_text = "Solo complete si el Gobernador no asistió"
        
        # SOLUCIÓN PARA EL PROBLEMA: Convertir fecha a timezone de México para mostrar
        if self.instance and self.instance.pk and self.instance.fecha_evento:
            mexico_tz = pytz.timezone('America/Mexico_City')
            fecha_mexico = self.instance.fecha_evento.astimezone(mexico_tz)
            # Convertir a formato datetime-local (sin timezone)
            fecha_local_str = fecha_mexico.strftime('%Y-%m-%dT%H:%M')
            self.initial['fecha_evento'] = fecha_local_str
    
    def clean_fecha_evento(self):
        """Validar que la fecha sea válida y convertir a UTC"""
        fecha = self.cleaned_data.get('fecha_evento')
        if fecha:
            mexico_tz = pytz.timezone('America/Mexico_City')
            
            # Si la fecha no tiene zona horaria, asumimos que es en zona de México
            if timezone.is_naive(fecha):
                fecha = mexico_tz.localize(fecha)
            
            # Permitir fechas hasta 1 año atrás
            ahora = timezone.now()
            fecha_limite = ahora - timezone.timedelta(days=365)
            
            if fecha < fecha_limite:
                raise ValidationError("La fecha del evento no puede ser mayor a 1 año atrás.")
            
            # Convertir a UTC para almacenamiento
            fecha_utc = fecha.astimezone(pytz.UTC)
            return fecha_utc
        
        return fecha
    
    def clean_nombre(self):
        """Validar el nombre del evento"""
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            if len(nombre.strip()) < 5:
                raise ValidationError("El nombre del evento debe tener al menos 5 caracteres.")
        return nombre
    
    def clean(self):
        """Validación cruzada del formulario"""
        cleaned_data = super().clean()
        asistio_gobernador = cleaned_data.get('asistio_gobernador')
        representante = cleaned_data.get('representante')
        
        # Si no asistió el gobernador, debe haber un representante
        if not asistio_gobernador and not representante:
            raise ValidationError({
                'representante': 'Debe especificar quién asistió como representante si el Gobernador no asistió.'
            })
        
        # Si asistió el gobernador, limpiar el campo representante
        if asistio_gobernador and representante:
            cleaned_data['representante'] = ''
        
        return cleaned_data

class FiltroEventosForm(forms.Form):
    """Formulario para filtrar eventos - CORREGIDO"""
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label="Fecha desde"
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label="Fecha hasta"
    )
    
    municipio = forms.ModelChoiceField(
        queryset=Municipio.objects.filter(activo=True),
        required=False,
        empty_label="Todos los municipios",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Municipio"
    )
    
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + Evento.ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Estado del evento"
    )
    
    # FIX: Cambiar el nombre del campo para evitar confusión
    asistencia = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('True', 'Asistió el Gobernador'),
            ('False', 'Asistió Representante')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Tipo de asistencia"
    )
    
    # NUEVO: Campo separado para tipo de evento
    tipo_evento = forms.ChoiceField(
        choices=[
            ('', 'Todos los tipos'),
            ('festivo', 'Festivo'),
            ('regular', 'Regular')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Tipo de evento"
    )
    
    buscar = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar en nombre, lugar, responsable...'
        }),
        label="Búsqueda general"
    )