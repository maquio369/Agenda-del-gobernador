from django import template
from django.utils import timezone
import datetime

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
        dia_ingles = fecha.strftime('%A')
        mes_ingles = fecha.strftime('%B')
        
        dia_espanol = dias.get(dia_ingles, dia_ingles)
        mes_espanol = meses.get(mes_ingles, mes_ingles)
        
        return f"{dia_espanol}, {fecha.day} de {mes_espanol} de {fecha.year}"
    except Exception:
        return fecha.strftime('%d/%m/%Y')

@register.filter
def minutos_transcurridos(timedelta_obj):
    """Convierte un timedelta a minutos"""
    if not timedelta_obj:
        return 0
    try:
        return int(timedelta_obj.total_seconds() / 60)
    except Exception:
        return 0