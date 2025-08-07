# eventos/utils.py
from django.utils import timezone
import pytz
from datetime import datetime, date

def get_mexico_timezone():
    """Obtiene la zona horaria de México"""
    return pytz.timezone('America/Mexico_City')

def get_current_mexico_time():
    """Obtiene la fecha y hora actual en zona horaria de México"""
    mexico_tz = get_mexico_timezone()
    return timezone.now().astimezone(mexico_tz)

def convert_to_mexico_time(dt):
    """Convierte un datetime a zona horaria de México"""
    if dt is None:
        return None
    
    mexico_tz = get_mexico_timezone()
    if dt.tzinfo is None:
        # Si no tiene timezone, asumimos que es UTC
        dt = pytz.UTC.localize(dt)
    
    return dt.astimezone(mexico_tz)

def format_event_date(evento):
    """Formatea la fecha de un evento para mostrar en el calendario"""
    mexico_time = convert_to_mexico_time(evento.fecha_evento)
    return {
        'date': mexico_time.strftime('%Y-%m-%d'),
        'time': mexico_time.strftime('%H:%M'),
        'datetime_display': mexico_time.strftime('%d/%m/%Y %H:%M'),
        'iso': mexico_time.isoformat()
    }

def parse_calendar_date(date_string):
    """Convierte una fecha en formato YYYY-MM-DD a datetime con timezone de México"""
    try:
        date_obj = datetime.strptime(date_string, '%Y-%m-%d').date()
        mexico_tz = get_mexico_timezone()
        # Crear datetime al inicio del día en México
        dt = datetime.combine(date_obj, datetime.min.time())
        return mexico_tz.localize(dt)
    except (ValueError, TypeError):
        return None