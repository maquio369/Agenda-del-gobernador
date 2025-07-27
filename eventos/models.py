# eventos/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import pytz

class Municipio(models.Model):
    """Modelo para los municipios de Chiapas"""
    nombre = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Municipio"
        verbose_name_plural = "Municipios"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class Evento(models.Model):
    """Modelo principal para los eventos del Gobernador"""
    
    ESTADO_CHOICES = [
        ('programado', 'Programado'),
        ('en_curso', 'En Curso'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
    ]
    
    # Información básica del evento
    nombre = models.CharField(max_length=200, verbose_name="Nombre del evento")
    fecha_evento = models.DateTimeField(verbose_name="Fecha y hora del evento")
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE, verbose_name="Municipio")
    lugar = models.CharField(max_length=300, verbose_name="Lugar del evento")
    
    # Características del evento
    es_festivo = models.BooleanField(default=False, verbose_name="¿Es festivo?")
    responsable = models.CharField(
        max_length=200, 
        verbose_name="Responsable del evento o persona que invita"
    )
    
    # Estado del evento
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='programado',
        verbose_name="Estado del evento"
    )
    fecha_finalizacion_manual = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Fecha de finalización manual"
    )
    
    # Asistencia del Gobernador
    asistio_gobernador = models.BooleanField(default=True, verbose_name="¿Asistió el Gobernador?")
    representante = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name="Nombre del representante (si no asistió el Gobernador)"
    )
    
    # Información adicional
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción del evento")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    
    # Metadatos
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Creado por")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última actualización")
    
    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ['-fecha_evento']
    
    def __str__(self):
        mexico_tz = pytz.timezone('America/Mexico_City')
        fecha_mexico = self.fecha_evento.astimezone(mexico_tz)
        return f"{self.nombre} - {self.municipio.nombre} - {fecha_mexico.strftime('%d/%m/%Y %H:%M')}"
    
    def get_fecha_mexico(self):
        """Retorna la fecha del evento en zona horaria de México"""
        mexico_tz = pytz.timezone('America/Mexico_City')
        return self.fecha_evento.astimezone(mexico_tz)
    
    def actualizar_estado_automatico(self):
        """Actualiza el estado del evento automáticamente basado en la fecha/hora"""
        # Obtener fecha/hora actual en zona de México
        mexico_tz = pytz.timezone('America/Mexico_City')
        ahora_mexico = timezone.now().astimezone(mexico_tz)
        fecha_evento_mexico = self.fecha_evento.astimezone(mexico_tz)
        
        # Si el evento fue finalizado manualmente, no cambiar
        if self.fecha_finalizacion_manual:
            return self.estado
        
        # Si el evento aún no ha empezado
        if ahora_mexico < fecha_evento_mexico:
            nuevo_estado = 'programado'
        
        # Si el evento ya empezó pero no ha pasado 1 hora
        elif (ahora_mexico >= fecha_evento_mexico and 
              ahora_mexico < (fecha_evento_mexico + timezone.timedelta(hours=1))):
            nuevo_estado = 'en_curso'
        
        # Si ya pasó más de 1 hora desde que empezó
        else:
            nuevo_estado = 'finalizado'
        
        # Solo actualizar si el estado cambió
        if self.estado != nuevo_estado:
            print(f"DEBUG MODEL - Actualizando estado de {self.nombre}: {self.estado} -> {nuevo_estado}")
            print(f"DEBUG MODEL - Ahora México: {ahora_mexico}")
            print(f"DEBUG MODEL - Evento México: {fecha_evento_mexico}")
            self.estado = nuevo_estado
            self.save(update_fields=['estado', 'fecha_actualizacion'])
        
        return self.estado
    
    def finalizar_manualmente(self, usuario=None):
        """Marca el evento como finalizado manualmente"""
        self.estado = 'finalizado'
        self.fecha_finalizacion_manual = timezone.now()
        self.save(update_fields=['estado', 'fecha_finalizacion_manual', 'fecha_actualizacion'])
        return True
    
    @property
    def estado_calculado(self):
        """Retorna el estado actual del evento (calculado automáticamente)"""
        return self.actualizar_estado_automatico()
    
    @property
    def es_evento_hoy(self):
        """Verifica si el evento es hoy (en zona de México)"""
        mexico_tz = pytz.timezone('America/Mexico_City')
        ahora_mexico = timezone.now().astimezone(mexico_tz)
        fecha_evento_mexico = self.fecha_evento.astimezone(mexico_tz)
        return fecha_evento_mexico.date() == ahora_mexico.date()
    
    @property
    def es_evento_proximo(self):
        """Verifica si el evento es en los próximos 7 días (en zona de México)"""
        mexico_tz = pytz.timezone('America/Mexico_City')
        ahora_mexico = timezone.now().astimezone(mexico_tz)
        fecha_evento_mexico = self.fecha_evento.astimezone(mexico_tz)
        fecha_limite = ahora_mexico.date() + timezone.timedelta(days=7)
        return (fecha_evento_mexico.date() >= ahora_mexico.date() and 
                fecha_evento_mexico.date() <= fecha_limite)
    
    @property
    def puede_finalizar_manualmente(self):
        """Verifica si el evento puede ser finalizado manualmente"""
        mexico_tz = pytz.timezone('America/Mexico_City')
        ahora_mexico = timezone.now().astimezone(mexico_tz)
        fecha_evento_mexico = self.fecha_evento.astimezone(mexico_tz)
        
        # Puede finalizar si ya empezó y no está finalizado manualmente
        return (ahora_mexico >= fecha_evento_mexico and 
                self.estado != 'finalizado' and 
                not self.fecha_finalizacion_manual)
    
    @property
    def tiempo_transcurrido(self):
        """Retorna el tiempo transcurrido desde que empezó el evento"""
        mexico_tz = pytz.timezone('America/Mexico_City')
        ahora_mexico = timezone.now().astimezone(mexico_tz)
        fecha_evento_mexico = self.fecha_evento.astimezone(mexico_tz)
        
        if ahora_mexico >= fecha_evento_mexico:
            return ahora_mexico - fecha_evento_mexico
        return None
    
    def clean(self):
        """Validaciones personalizadas"""
        from django.core.exceptions import ValidationError
        
        # Si no asistió el gobernador, debe haber un representante
        if not self.asistio_gobernador and not self.representante:
            raise ValidationError({
                'representante': 'Debe especificar quién asistió como representante si el Gobernador no asistió.'
            })
        
        # Si asistió el gobernador, no debe haber representante
        if self.asistio_gobernador and self.representante:
            raise ValidationError({
                'representante': 'No debe especificar un representante si el Gobernador asistió.'
            })