from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Municipio, Evento

@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre']
    ordering = ['nombre']

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 
        'fecha_evento', 
        'municipio', 
        'get_estado_display',
        'asistio_gobernador', 
        'representante',
        'estado_calculado_display'
    ]
    list_filter = [
        'estado',
        'asistio_gobernador', 
        'es_festivo', 
        'municipio', 
        'fecha_evento'
    ]
    search_fields = [
        'nombre', 
        'lugar', 
        'responsable', 
        'representante'
    ]
    date_hierarchy = 'fecha_evento'
    ordering = ['-fecha_evento']
    
    fieldsets = (
        ('Información del Evento', {
            'fields': ('nombre', 'fecha_evento', 'municipio', 'lugar')
        }),
        ('Detalles', {
            'fields': ('es_festivo', 'responsable', 'descripcion')
        }),
        ('Estado', {
            'fields': ('estado', 'fecha_finalizacion_manual')
        }),
        ('Asistencia', {
            'fields': ('asistio_gobernador', 'representante')
        }),
        ('Información Adicional', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['fecha_finalizacion_manual']
    
    def estado_calculado_display(self, obj):
        """Muestra el estado calculado automáticamente con colores"""
        estado = obj.actualizar_estado_automatico()
        
        colors = {
            'programado': '#17a2b8',  # Info
            'en_curso': '#fd7e14',    # Warning
            'finalizado': '#28a745',  # Success
            'cancelado': '#dc3545'    # Danger
        }
        
        color = colors.get(estado, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    
    estado_calculado_display.short_description = 'Estado Actual'
    estado_calculado_display.admin_order_field = 'estado'
    
    def save_model(self, request, obj, form, change):
        """Asignar automáticamente el usuario que crea el evento"""
        if not change:  # Solo en creación, no en edición
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['finalizar_eventos', 'marcar_en_curso', 'actualizar_estados']
    
    def finalizar_eventos(self, request, queryset):
        """Acción para finalizar eventos seleccionados"""
        count = 0
        for evento in queryset:
            if evento.puede_finalizar_manualmente:
                evento.finalizar_manualmente()
                count += 1
        
        self.message_user(
            request,
            f'{count} eventos fueron finalizados correctamente.'
        )
    
    finalizar_eventos.short_description = "Finalizar eventos seleccionados"
    
    def marcar_en_curso(self, request, queryset):
        """Acción para marcar eventos como en curso"""
        count = queryset.update(estado='en_curso')
        self.message_user(
            request,
            f'{count} eventos fueron marcados como "En Curso".'
        )
    
    marcar_en_curso.short_description = "Marcar como En Curso"
    
    def actualizar_estados(self, request, queryset):
        """Acción para actualizar estados automáticamente"""
        count = 0
        for evento in queryset:
            estado_anterior = evento.estado
            evento.actualizar_estado_automatico()
            if evento.estado != estado_anterior:
                count += 1
        
        self.message_user(
            request,
            f'{count} eventos actualizaron su estado automáticamente.'
        )
    
    actualizar_estados.short_description = "Actualizar estados automáticamente"