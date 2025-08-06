# eventos/templatetags/fecha_filters.py
from django import template
from django.utils import timezone
import datetime
import pytz

register = template.Library()

@register.filter
def fecha_espanol(fecha):
    """Convierte una fecha a formato español legible"""
    if not fecha:
        return ""
    
    # Diccionario de días en español
    dias = {
        'Monday': 'Lunes',
        'Tuesday': 'Martes', 
        'Wednesday': 'Miércoles',
        'Thursday': 'Jueves',
        'Friday': 'Viernes',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    
    # Diccionario de meses en español
    meses = {
        'January': 'Enero',
        'February': 'Febrero',
        'March': 'Marzo',
        'April': 'Abril',
        'May': 'Mayo',
        'June': 'Junio',
        'July': 'Julio',
        'August': 'Agosto',
        'September': 'Septiembre',
        'October': 'Octubre',
        'November': 'Noviembre',
        'December': 'Diciembre'
    }
    
    try:
        # MEJORA: Mejor manejo de timezone de México
        if hasattr(fecha, 'astimezone'):
            mexico_tz = pytz.timezone('America/Mexico_City')
            fecha_mexico = fecha.astimezone(mexico_tz)
        else:
            fecha_mexico = fecha
        
        dia_ingles = fecha_mexico.strftime('%A')
        mes_ingles = fecha_mexico.strftime('%B')
        
        dia_espanol = dias.get(dia_ingles, dia_ingles)
        mes_espanol = meses.get(mes_ingles, mes_ingles)
        
        return f"{dia_espanol}, {fecha_mexico.day} de {mes_espanol} de {fecha_mexico.year}"
    except Exception:
        # MEJORA: Mejor manejo de errores
        try:
            return fecha.strftime('%d/%m/%Y')
        except:
            return "Fecha no disponible"

@register.filter
def minutos_transcurridos(timedelta_obj):
    """Convierte un timedelta a minutos"""
    if not timedelta_obj:
        return 0
    try:
        return int(timedelta_obj.total_seconds() / 60)
    except Exception:
        return 0

# ========== NUEVOS FILTROS (NO AFECTAN LOS EXISTENTES) ==========

@register.filter
def fecha_corta_espanol(fecha):
    """Formato corto de fecha en español"""
    if not fecha:
        return "No especificada"
    
    try:
        # Convertir a timezone de México si es aware
        if hasattr(fecha, 'astimezone'):
            mexico_tz = pytz.timezone('America/Mexico_City')
            fecha_mexico = fecha.astimezone(mexico_tz)
        else:
            fecha_mexico = fecha
            
        return fecha_mexico.strftime('%d/%m/%Y')
    except Exception:
        return "Fecha inválida"

@register.filter
def hora_mexico(fecha):
    """Convierte una fecha a hora de México"""
    if not fecha:
        return "No especificada"
    
    try:
        # Convertir a timezone de México si es aware
        if hasattr(fecha, 'astimezone'):
            mexico_tz = pytz.timezone('America/Mexico_City')
            fecha_mexico = fecha.astimezone(mexico_tz)
        else:
            fecha_mexico = fecha
            
        return fecha_mexico.strftime('%H:%M')
    except Exception:
        return "Hora inválida"

@register.filter
def estado_evento_display(estado):
    """Muestra el estado del evento en español"""
    estados = {
        'programado': 'Programado',
        'en_curso': 'En Curso',
        'finalizado': 'Finalizado',
        'cancelado': 'Cancelado'
    }
    return estados.get(estado, estado.title())

@register.filter
def tiempo_hasta_evento(fecha_evento):
    """Calcula el tiempo hasta el evento"""
    if not fecha_evento:
        return "Fecha no especificada"
    
    try:
        ahora = timezone.now()
        if hasattr(fecha_evento, 'astimezone'):
            fecha_evento = fecha_evento.astimezone(timezone.get_current_timezone())
        
        diferencia = fecha_evento - ahora
        
        if diferencia.total_seconds() < 0:
            return "Evento pasado"
        elif diferencia.days > 0:
            return f"En {diferencia.days} día{'s' if diferencia.days != 1 else ''}"
        elif diferencia.seconds > 3600:
            horas = int(diferencia.seconds / 3600)
            return f"En {horas} hora{'s' if horas != 1 else ''}"
        elif diferencia.seconds > 60:
            minutos = int(diferencia.seconds / 60)
            return f"En {minutos} minuto{'s' if minutos != 1 else ''}"
        else:
            return "Ahora"
    except Exception:
        return "Error calculando tiempo"