# eventos/chatbot.py
from django.db.models import Q, Count
from datetime import datetime, timedelta, date
import re
from .models import Evento, Municipio

class ChatbotAgenda:
    """Chatbot básico para consultas de la agenda del gobernador"""
    
    def __init__(self):
        # Patrones de fechas comunes
        self.patrones_fecha = {
            'hoy': ['hoy', 'hoy día', 'el día de hoy'],
            'mañana': ['mañana', 'el día de mañana'],
            'ayer': ['ayer', 'el día de ayer'],
            'esta_semana': ['esta semana', 'semana actual'],
            'proxima_semana': ['próxima semana', 'siguiente semana', 'la próxima semana'],
            'este_mes': ['este mes', 'mes actual'],
            'proximo_mes': ['próximo mes', 'siguiente mes', 'el próximo mes']
        }
        
        # Patrones de consultas estadísticas
        self.patrones_estadisticas = {
            'total': ['cuántos eventos', 'total de eventos', 'número de eventos'],
            'gobernador': ['eventos del gobernador', 'donde asistió el gobernador'],
            'representante': ['eventos del representante', 'donde fue el representante'],
            'festivos': ['eventos festivos', 'festividades', 'eventos especiales']
        }
        
        # Municipios de Chiapas (principales)
        self.municipios_principales = [
            'tuxtla gutiérrez', 'tuxtla', 'san cristóbal de las casas', 'san cristóbal',
            'tapachula', 'comitán', 'palenque', 'arriaga', 'tonalá', 'ocosingo',
            'villaflores', 'las margaritas', 'chiapa de corzo', 'berriozábal'
        ]
    
    def procesar_consulta(self, mensaje):
        """Punto de entrada principal para procesar consultas"""
        mensaje = mensaje.lower().strip()
        
        # 1. Consultas por fecha (incluyendo fechas exactas)
        if self._detectar_consulta_fecha(mensaje):
            return self._consultar_por_fecha(mensaje)
        
        # 2. Consultas por municipio
        elif self._detectar_consulta_municipio(mensaje):
            return self._consultar_por_municipio(mensaje)
        
        # 3. Consultas estadísticas
        elif self._detectar_consulta_estadistica(mensaje):
            return self._consultar_estadisticas(mensaje)
        
        # 4. Consultas de búsqueda general
        elif self._detectar_busqueda_general(mensaje):
            return self._busqueda_general(mensaje)
        
        # 5. Comandos de ayuda
        elif self._detectar_ayuda(mensaje):
            return self._mostrar_ayuda()
        
        # 6. Respuesta por defecto
        else:
            return self._respuesta_no_entendida()
    
    def _detectar_fecha_exacta(self, mensaje):
        """Detecta fechas exactas en diferentes formatos"""
        # Patrones para diferentes formatos de fecha
        patrones_fecha = [
            # dd/mm/yyyy o dd-mm-yyyy
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            # dd/mm o dd-mm (año actual)
            r'(\d{1,2})[/-](\d{1,2})(?![/-]\d)',
            # yyyy-mm-dd (formato ISO)
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            # dd de mes de año
            r'(\d{1,2})\s+de\s+(\w+)(?:\s+de\s+(\d{4}))?',
            # mes dd, yyyy
            r'(\w+)\s+(\d{1,2}),?\s*(\d{4})?'
        ]
        
        for patron in patrones_fecha:
            if re.search(patron, mensaje):
                return True
        return False
    
    def _extraer_fecha_exacta(self, mensaje):
        """Extrae y convierte fechas exactas a objeto date"""
        # Mapeo de meses en español
        meses_es = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
        }
        
        año_actual = date.today().year
        
        # Patrón 1: dd/mm/yyyy o dd-mm-yyyy
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', mensaje)
        if match:
            try:
                dia, mes, año = map(int, match.groups())
                return date(año, mes, dia)
            except ValueError:
                pass
        
        # Patrón 2: dd/mm o dd-mm (año actual)
        match = re.search(r'(\d{1,2})[/-](\d{1,2})(?![/-]\d)', mensaje)
        if match:
            try:
                dia, mes = map(int, match.groups())
                return date(año_actual, mes, dia)
            except ValueError:
                pass
        
        # Patrón 3: yyyy-mm-dd (formato ISO)
        match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', mensaje)
        if match:
            try:
                año, mes, dia = map(int, match.groups())
                return date(año, mes, dia)
            except ValueError:
                pass
        
        # Patrón 4: dd de mes de año
        match = re.search(r'(\d{1,2})\s+de\s+(\w+)(?:\s+de\s+(\d{4}))?', mensaje)
        if match:
            try:
                dia = int(match.group(1))
                mes_nombre = match.group(2).lower()
                año = int(match.group(3)) if match.group(3) else año_actual
                
                if mes_nombre in meses_es:
                    mes = meses_es[mes_nombre]
                    return date(año, mes, dia)
            except (ValueError, TypeError):
                pass
        
        # Patrón 5: mes dd, yyyy
        match = re.search(r'(\w+)\s+(\d{1,2}),?\s*(\d{4})?', mensaje)
        if match:
            try:
                mes_nombre = match.group(1).lower()
                dia = int(match.group(2))
                año = int(match.group(3)) if match.group(3) else año_actual
                
                if mes_nombre in meses_es:
                    mes = meses_es[mes_nombre]
                    return date(año, mes, dia)
            except (ValueError, TypeError):
                pass
        
        return None
    
    def _consultar_fecha_exacta(self, mensaje):
        """Consulta eventos para una fecha exacta"""
        fecha_objetivo = self._extraer_fecha_exacta(mensaje)
        
        if not fecha_objetivo:
            return "No pude entender la fecha. Puedes usar formatos como:\n• 15/01/2024\n• 15 de enero\n• 2024-01-15"
        
        # Buscar eventos en esa fecha
        eventos = Evento.objects.filter(fecha_evento__date=fecha_objetivo)
        
        # Formatear la fecha para mostrar
        fecha_str = fecha_objetivo.strftime('%d de %B de %Y')
        meses_es = {
            'January': 'enero', 'February': 'febrero', 'March': 'marzo', 'April': 'abril',
            'May': 'mayo', 'June': 'junio', 'July': 'julio', 'August': 'agosto',
            'September': 'septiembre', 'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
        }
        
        for en, es in meses_es.items():
            fecha_str = fecha_str.replace(en, es)
        
        if not eventos.exists():
            # Verificar si es una fecha futura o pasada para dar mejor contexto
            hoy = date.today()
            if fecha_objetivo > hoy:
                return f"📅 No hay eventos programados para el **{fecha_str}**.\n\n¿Te gustaría que revise fechas cercanas?"
            else:
                return f"📅 No hubo eventos registrados el **{fecha_str}**."
        
        # Formatear eventos encontrados
        respuesta = f"📅 **Eventos para el {fecha_str}** ({eventos.count()} evento{'s' if eventos.count() > 1 else ''}):\n\n"
        
        for evento in eventos.order_by('fecha_evento'):
            fecha_hora = evento.get_fecha_mexico().strftime('%H:%M')
            icono_asistencia = "👤" if evento.asistio_gobernador else "🤝"
            tipo_asistencia = "Gobernador" if evento.asistio_gobernador else "Representante"
            
            respuesta += f"🕐 **{fecha_hora}** - {evento.nombre}\n"
            respuesta += f"   📍 {evento.lugar}, {evento.municipio.nombre}\n"
            respuesta += f"   👤 {evento.responsable}\n"
            respuesta += f"   {icono_asistencia} {tipo_asistencia}\n"
            
            if evento.es_festivo:
                respuesta += f"   🎉 Evento festivo\n"
            
            respuesta += "\n"
        
        return respuesta
    
    def _detectar_consulta_fecha(self, mensaje):
        """Detecta si es una consulta relacionada con fechas"""
        # Primero verificar fechas exactas
        if self._detectar_fecha_exacta(mensaje):
            return True
        
        # Luego verificar patrones relativos existentes
        for patron_lista in self.patrones_fecha.values():
            if any(patron in mensaje for patron in patron_lista):
                return True
        
        return False
    
    def _consultar_por_fecha(self, mensaje):
        """Maneja consultas relacionadas con fechas"""
        # Primero verificar si es una fecha exacta
        if self._detectar_fecha_exacta(mensaje):
            return self._consultar_fecha_exacta(mensaje)
        
        # Si no es fecha exacta, usar la lógica existente para fechas relativas
        hoy = date.today()
        
        # Eventos de hoy
        if any(patron in mensaje for patron in self.patrones_fecha['hoy']):
            eventos = Evento.objects.filter(fecha_evento__date=hoy)
            return self._formatear_eventos_fecha(eventos, "hoy")
        
        # Eventos de mañana
        elif any(patron in mensaje for patron in self.patrones_fecha['mañana']):
            manana = hoy + timedelta(days=1)
            eventos = Evento.objects.filter(fecha_evento__date=manana)
            return self._formatear_eventos_fecha(eventos, "mañana")
        
        # Eventos de ayer
        elif any(patron in mensaje for patron in self.patrones_fecha['ayer']):
            ayer = hoy - timedelta(days=1)
            eventos = Evento.objects.filter(fecha_evento__date=ayer)
            return self._formatear_eventos_fecha(eventos, "ayer")
        
        # Eventos de esta semana
        elif any(patron in mensaje for patron in self.patrones_fecha['esta_semana']):
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fin_semana = inicio_semana + timedelta(days=6)
            eventos = Evento.objects.filter(
                fecha_evento__date__gte=inicio_semana,
                fecha_evento__date__lte=fin_semana
            )
            return self._formatear_eventos_fecha(eventos, "esta semana")
        
        # Eventos de próxima semana
        elif any(patron in mensaje for patron in self.patrones_fecha['proxima_semana']):
            inicio_proxima = hoy + timedelta(days=7-hoy.weekday())
            fin_proxima = inicio_proxima + timedelta(days=6)
            eventos = Evento.objects.filter(
                fecha_evento__date__gte=inicio_proxima,
                fecha_evento__date__lte=fin_proxima
            )
            return self._formatear_eventos_fecha(eventos, "la próxima semana")
        
        # Eventos de este mes
        elif any(patron in mensaje for patron in self.patrones_fecha['este_mes']):
            eventos = Evento.objects.filter(
                fecha_evento__year=hoy.year,
                fecha_evento__month=hoy.month
            )
            return self._formatear_eventos_fecha(eventos, "este mes")
        
        return "No pude entender qué fecha específica buscas. Puedes usar:\n• Fechas relativas: 'hoy', 'mañana', 'esta semana'\n• Fechas exactas: '15/01/2024', '15 de enero', '2024-01-15'"
    
    def _detectar_consulta_municipio(self, mensaje):
        """Detecta si menciona algún municipio"""
        return any(municipio in mensaje for municipio in self.municipios_principales)
    
    def _consultar_por_municipio(self, mensaje):
        """Consulta eventos por municipio"""
        municipio_encontrado = None
        
        # Buscar qué municipio mencionó
        for municipio in self.municipios_principales:
            if municipio in mensaje:
                municipio_encontrado = municipio
                break
        
        if municipio_encontrado:
            # Normalizar nombre del municipio
            nombre_municipio = self._normalizar_municipio(municipio_encontrado)
            
            try:
                municipio_obj = Municipio.objects.get(nombre__icontains=nombre_municipio)
                eventos = Evento.objects.filter(municipio=municipio_obj).order_by('-fecha_evento')[:10]
                
                if eventos.exists():
                    respuesta = f"📍 **Eventos en {municipio_obj.nombre}** (últimos 10):\n\n"
                    for evento in eventos:
                        fecha_str = evento.get_fecha_mexico().strftime('%d/%m/%Y %H:%M')
                        respuesta += f"📅 **{fecha_str}** - {evento.nombre}\n"
                        respuesta += f"   📍 {evento.lugar}\n"
                        respuesta += f"   👤 {evento.responsable}\n"
                        respuesta += f"   🎯 {'Gobernador' if evento.asistio_gobernador else 'Representante'}\n\n"
                    return respuesta
                else:
                    return f"No encontré eventos programados en {municipio_obj.nombre}."
                    
            except Municipio.DoesNotExist:
                return f"No encontré el municipio '{municipio_encontrado}' en el sistema."
        
        return "No pude identificar el municipio. ¿Puedes especificar cuál municipio te interesa?"
    
    def _detectar_consulta_estadistica(self, mensaje):
        """Detecta consultas de estadísticas"""
        for patron_lista in self.patrones_estadisticas.values():
            if any(patron in mensaje for patron in patron_lista):
                return True
        return False
    
    def _consultar_estadisticas(self, mensaje):
        """Maneja consultas estadísticas"""
        # Total de eventos
        if any(patron in mensaje for patron in self.patrones_estadisticas['total']):
            total = Evento.objects.count()
            return f"📊 **Total de eventos registrados**: {total} eventos"
        
        # Eventos del gobernador
        elif any(patron in mensaje for patron in self.patrones_estadisticas['gobernador']):
            total_gobernador = Evento.objects.filter(asistio_gobernador=True).count()
            total_eventos = Evento.objects.count()
            porcentaje = round((total_gobernador/total_eventos*100), 1) if total_eventos > 0 else 0
            return f"👤 **Eventos con asistencia del Gobernador**: {total_gobernador} eventos ({porcentaje}%)"
        
        # Eventos de representante
        elif any(patron in mensaje for patron in self.patrones_estadisticas['representante']):
            total_representante = Evento.objects.filter(asistio_gobernador=False).count()
            total_eventos = Evento.objects.count()
            porcentaje = round((total_representante/total_eventos*100), 1) if total_eventos > 0 else 0
            return f"🤝 **Eventos con representante**: {total_representante} eventos ({porcentaje}%)"
        
        # Eventos festivos
        elif any(patron in mensaje for patron in self.patrones_estadisticas['festivos']):
            total_festivos = Evento.objects.filter(es_festivo=True).count()
            return f"🎉 **Eventos festivos**: {total_festivos} eventos"
        
        return "¿Qué estadística específica te interesa?"
    
    def _detectar_busqueda_general(self, mensaje):
        """Detecta búsquedas generales por palabras clave"""
        palabras_busqueda = ['buscar', 'encontrar', 'ver', 'mostrar', 'eventos de', 'eventos con']
        return any(palabra in mensaje for palabra in palabras_busqueda)
    
    def _busqueda_general(self, mensaje):
        """Realiza búsqueda general por palabras clave"""
        # Extraer palabras clave (quitar palabras comunes)
        palabras_comunes = ['buscar', 'encontrar', 'ver', 'mostrar', 'eventos', 'de', 'con', 'el', 'la', 'los', 'las']
        palabras = [palabra for palabra in mensaje.split() if palabra not in palabras_comunes and len(palabra) > 2]
        
        if not palabras:
            return "¿Qué eventos específicos buscas? Puedes mencionar nombres, lugares o responsables."
        
        # Buscar en nombre, lugar y responsable
        query = Q()
        for palabra in palabras:
            query |= Q(nombre__icontains=palabra)
            query |= Q(lugar__icontains=palabra)
            query |= Q(responsable__icontains=palabra)
        
        eventos = Evento.objects.filter(query).order_by('-fecha_evento')[:5]
        
        if eventos.exists():
            respuesta = f"🔍 **Eventos encontrados** (relacionados con: {', '.join(palabras)}):\n\n"
            for evento in eventos:
                fecha_str = evento.get_fecha_mexico().strftime('%d/%m/%Y %H:%M')
                respuesta += f"📅 **{fecha_str}** - {evento.nombre}\n"
                respuesta += f"   📍 {evento.lugar}, {evento.municipio.nombre}\n"
                respuesta += f"   👤 {evento.responsable}\n\n"
            return respuesta
        else:
            return f"No encontré eventos relacionados con: {', '.join(palabras)}"
    
    def _detectar_ayuda(self, mensaje):
        """Detecta solicitudes de ayuda"""
        palabras_ayuda = ['ayuda', 'help', '?', 'qué puedes hacer', 'comandos', 'opciones']
        return any(palabra in mensaje for palabra in palabras_ayuda)
    
    def _mostrar_ayuda(self):
        """Muestra la ayuda del chatbot"""
        return """
🤖 **¡Hola! Soy tu asistente de agenda**

**📅 Consultas por fecha:**
• "¿Qué eventos hay hoy?"
• "¿Qué tiene el gobernador mañana?"
• "Eventos de esta semana"
• "Agenda del próximo mes"
• **NUEVO:** "¿Qué eventos hay el 15/01/2024?"
• **NUEVO:** "Eventos del 25 de enero"

**📍 Consultas por municipio:**
• "Eventos en Tuxtla Gutiérrez"
• "¿Cuándo visitó San Cristóbal?"
• "Agenda en Tapachula"

**📊 Estadísticas:**
• "¿Cuántos eventos hay?"
• "Eventos del gobernador"
• "Eventos festivos"

**🔍 Búsqueda:**
• "Buscar eventos de educación"
• "Mostrar eventos en parque"

**📅 Formatos de fecha soportados:**
• dd/mm/yyyy → "15/01/2024"
• dd/mm → "15/01" (año actual)
• dd de mes → "15 de enero"
• yyyy-mm-dd → "2024-01-15"

¡Pregúntame cualquier cosa sobre la agenda!
        """
    
    def _respuesta_no_entendida(self):
        """Respuesta cuando no entiende la consulta"""
        return """
🤔 No entendí tu consulta. Puedes preguntarme:

• **Fechas**: "eventos de hoy", "agenda de mañana", "eventos del 15/01"
• **Lugares**: "eventos en Tuxtla", "visitas a San Cristóbal" 
• **Estadísticas**: "cuántos eventos", "eventos del gobernador"
• **Búsqueda**: "buscar eventos de salud"

Escribe "ayuda" para ver todas las opciones disponibles.
        """
    
    def _formatear_eventos_fecha(self, eventos, contexto):
        """Formatea eventos para consultas por fecha"""
        if not eventos.exists():
            return f"📅 No hay eventos programados para {contexto}."
        
        respuesta = f"📅 **Eventos para {contexto}** ({eventos.count()} eventos):\n\n"
        
        for evento in eventos.order_by('fecha_evento'):
            fecha_str = evento.get_fecha_mexico().strftime('%H:%M')
            icono_asistencia = "👤" if evento.asistio_gobernador else "🤝"
            tipo_asistencia = "Gobernador" if evento.asistio_gobernador else "Representante"
            
            respuesta += f"🕐 **{fecha_str}** - {evento.nombre}\n"
            respuesta += f"   📍 {evento.lugar}, {evento.municipio.nombre}\n"
            respuesta += f"   👤 {evento.responsable}\n"
            respuesta += f"   {icono_asistencia} {tipo_asistencia}\n"
            
            if evento.es_festivo:
                respuesta += f"   🎉 Evento festivo\n"
            
            respuesta += "\n"
        
        return respuesta
    
    def _normalizar_municipio(self, municipio):
        """Normaliza nombres de municipios para búsqueda"""
        normalizaciones = {
            'tuxtla': 'Tuxtla Gutiérrez',
            'san cristóbal': 'San Cristóbal de las Casas',
            'tapachula': 'Tapachula',
            'comitán': 'Comitán de Domínguez',
            'chiapa': 'Chiapa de Corzo',
            'acala': 'Acala'
            
        }
        
        return normalizaciones.get(municipio, municipio.title())