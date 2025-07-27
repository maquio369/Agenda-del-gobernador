from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Evento, Municipio
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML
from crispy_forms.bootstrap import Field

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
                attrs={'type': 'datetime-local', 'class': 'form-control'}
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
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observaciones adicionales (opcional)'}
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar Crispy Forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        self.helper.attrs = {'novalidate': ''}
        
        # Layout del formulario
        self.helper.layout = Layout(
            Fieldset(
                'Información Básica del Evento',
                Row(
                    Column('nombre', css_class='form-group col-md-8 mb-3'),
                    Column('es_festivo', css_class='form-group col-md-4 mb-3'),
                    css_class='form-row'
                ),
                Row(
                    Column('fecha_evento', css_class='form-group col-md-6 mb-3'),
                    Column('municipio', css_class='form-group col-md-6 mb-3'),
                    css_class='form-row'
                ),
                Row(
                    Column('lugar', css_class='form-group col-md-8 mb-3'),
                    Column('responsable', css_class='form-group col-md-4 mb-3'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Asistencia del Gobernador',
                Row(
                    Column('asistio_gobernador', css_class='form-group col-md-6 mb-3'),
                    Column('representante', css_class='form-group col-md-6 mb-3'),
                    css_class='form-row'
                ),
                HTML('<small class="text-muted">Si el Gobernador no asiste, especifique quién lo representa</small>'),
            ),
            Fieldset(
                'Información Adicional (Opcional)',
                'descripcion',
                'observaciones',
                css_class='mt-3'
            ),
            HTML('<hr class="my-4">'),
            Row(
                Column(
                    Submit('submit', 'Guardar Evento', css_class='btn btn-success btn-lg'),
                    css_class='col-md-6'
                ),
                Column(
                    HTML('<a href="{% url \'dashboard\' %}" class="btn btn-secondary btn-lg">Cancelar</a>'),
                    css_class='col-md-6 text-end'
                ),
                css_class='form-row'
            )
        )
        
        # Personalizar campos
        self.fields['municipio'].queryset = Municipio.objects.filter(activo=True).order_by('nombre')
        self.fields['municipio'].empty_label = "Seleccione un municipio"
        
        # Hacer campos requeridos más claros
        self.fields['nombre'].required = True
        self.fields['fecha_evento'].required = True
        self.fields['municipio'].required = True
        self.fields['lugar'].required = True
        self.fields['responsable'].required = True
        
        # Labels personalizados
        self.fields['nombre'].label = "Nombre del Evento *"
        self.fields['fecha_evento'].label = "Fecha y Hora *"
        self.fields['municipio'].label = "Municipio *"
        self.fields['lugar'].label = "Lugar del Evento *"
        self.fields['es_festivo'].label = "¿Es un evento festivo?"
        self.fields['responsable'].label = "Responsable/Organizador *"
        self.fields['asistio_gobernador'].label = "¿Asistió el Gobernador?"
        self.fields['representante'].label = "Representante (si no asistió el Gobernador)"
        self.fields['descripcion'].label = "Descripción del Evento"
        self.fields['observaciones'].label = "Observaciones"
        
        # Help text
        self.fields['fecha_evento'].help_text = "Seleccione la fecha y hora exacta del evento"
        self.fields['es_festivo'].help_text = "Marque si es una celebración o evento festivo"
        self.fields['representante'].help_text = "Solo complete si el Gobernador no asistió"
    
    def clean_fecha_evento(self):
        """Validar que la fecha no sea muy antigua"""
        fecha = self.cleaned_data.get('fecha_evento')
        if fecha:
            # Permitir fechas hasta 1 año atrás
            fecha_limite = timezone.now() - timezone.timedelta(days=365)
            if fecha < fecha_limite:
                raise ValidationError("La fecha del evento no puede ser mayor a 1 año atrás.")
        return fecha
    
    def clean_representante(self):
        """Validar representante según asistencia del gobernador"""
        asistio = self.cleaned_data.get('asistio_gobernador')
        representante = self.cleaned_data.get('representante')
        
        if not asistio and not representante:
            raise ValidationError("Debe especificar quién asistió como representante.")
        
        if asistio and representante:
            # Limpiar el campo si el gobernador asistió
            return None
            
        return representante
    
    def clean_nombre(self):
        """Validar que el nombre no esté duplicado para la misma fecha"""
        nombre = self.cleaned_data.get('nombre')
        fecha_evento = self.cleaned_data.get('fecha_evento')
        
        if nombre and fecha_evento:
            # Excluir el evento actual si estamos editando
            queryset = Evento.objects.filter(
                nombre__iexact=nombre,
                fecha_evento__date=fecha_evento.date()
            )
            
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError(
                    f"Ya existe un evento con el nombre '{nombre}' para la fecha {fecha_evento.date()}."
                )
        
        return nombre


class FiltroEventosForm(forms.Form):
    """Formulario para filtrar eventos en las listas"""
    
    OPCIONES_ASISTENCIA = [
        ('', 'Todos'),
        ('True', 'Asistió el Gobernador'),
        ('False', 'Asistió Representante'),
    ]
    
    OPCIONES_TIPO = [
        ('', 'Todos'),
        ('True', 'Festivos'),
        ('False', 'Regulares'),
    ]
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Desde"
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Hasta"
    )
    municipio = forms.ModelChoiceField(
        queryset=Municipio.objects.filter(activo=True).order_by('nombre'),
        required=False,
        empty_label="Todos los municipios",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Municipio"
    )
    asistencia = forms.ChoiceField(
        choices=OPCIONES_ASISTENCIA,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Asistencia"
    )
    tipo_evento = forms.ChoiceField(
        choices=OPCIONES_TIPO,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Tipo de Evento"
    )
    buscar = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, lugar o responsable...'
        }),
        label="Buscar"
    )