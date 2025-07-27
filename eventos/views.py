from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q, Count
from django.db.models.functions import TruncMonth
from django.template.loader import render_to_string
from datetime import timedelta
import json

# Importaciones para reportes
# from weasyprint import HTML, CSS  # Comentado temporalmente
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
import io

from .models import Evento, Municipio
from .forms import EventoForm, FiltroEventosForm

# Vista principal - Dashboard
@login_required
def dashboard(request):
    """Dashboard principal con eventos del día y próximos"""
    hoy = timezone.now().date()
    
    # Obtener todos los eventos de hoy
    eventos_hoy_todos = Evento.objects.filter(
        fecha_evento__date=hoy
    ).select_related('municipio', 'creado_por')
    
    # Actualizar estados automáticamente antes de mostrar
    for evento in eventos_hoy_todos:
        evento.actualizar_estado_automatico()
    
    # Separar por estados calculados
    eventos_en_curso = eventos_hoy_todos.filter(estado='en_curso')
    eventos_hoy_proximos = eventos_hoy_todos.filter(estado='programado')
    eventos_hoy_finalizados = eventos_hoy_todos.filter(estado='finalizado')
    
    # Eventos próximos (siguientes 7 días, excluyendo hoy)
    fecha_limite = hoy + timedelta(days=7)
    eventos_proximos = Evento.objects.filter(
        fecha_evento__date__gt=hoy,
        fecha_evento__date__lte=fecha_limite
    ).select_related('municipio', 'creado_por')[:10]  # Limitamos a 10
    
    # También actualizar estados de eventos próximos
    for evento in eventos_proximos:
        evento.actualizar_estado_automatico()
    
    context = {
        'eventos_hoy_todos': eventos_hoy_todos,
        'eventos_en_curso': eventos_en_curso,
        'eventos_hoy_proximos': eventos_hoy_proximos,
        'eventos_hoy_finalizados': eventos_hoy_finalizados,
        'eventos_proximos': eventos_proximos,
        'fecha_actual': hoy,
    }
    
    return render(request, 'eventos/dashboard.html', context)

# Vista para finalizar evento manualmente
@login_required
def finalizar_evento(request, pk):
    """Finaliza un evento manualmente"""
    evento = get_object_or_404(Evento, pk=pk)
    
    if request.method == 'POST':
        if evento.puede_finalizar_manualmente:
            evento.finalizar_manualmente()
            messages.success(request, f'Evento "{evento.nombre}" marcado como finalizado.')
        else:
            messages.error(request, 'Este evento no puede ser finalizado manualmente en este momento.')
    
    return redirect('dashboard')

# Vista para cambiar estado de evento
@login_required
def cambiar_estado_evento(request, pk):
    """Cambia el estado de un evento manualmente"""
    evento = get_object_or_404(Evento, pk=pk)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in ['programado', 'en_curso', 'finalizado', 'cancelado']:
            evento.estado = nuevo_estado
            if nuevo_estado == 'finalizado':
                evento.fecha_finalizacion_manual = timezone.now()
            evento.save()
            messages.success(request, f'Estado del evento cambiado a "{evento.get_estado_display()}".')
        else:
            messages.error(request, 'Estado no válido.')
    
    return redirect('dashboard')

# Vista para editar eventos
@login_required
def editar_evento(request, pk):
    """Formulario para editar eventos existentes"""
    evento = get_object_or_404(Evento, pk=pk)
    
    if request.method == 'POST':
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            messages.success(request, f'Evento "{evento.nombre}" actualizado exitosamente.')
            return redirect('detalle_evento', pk=evento.pk)
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = EventoForm(instance=evento)
    
    return render(request, 'eventos/editar_evento.html', {
        'form': form,
        'evento': evento
    })

# Vista para crear eventos
@login_required
def crear_evento(request):
    """Formulario para crear nuevos eventos"""
    if request.method == 'POST':
        form = EventoForm(request.POST)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.creado_por = request.user
            evento.save()
            messages.success(request, f'Evento "{evento.nombre}" creado exitosamente.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = EventoForm()
    
    return render(request, 'eventos/crear_evento.html', {'form': form})

# Vista para listar eventos
@login_required
def lista_eventos(request):
    """Lista completa de eventos con filtros"""
    form = FiltroEventosForm(request.GET)
    eventos = Evento.objects.select_related('municipio', 'creado_por').order_by('-fecha_evento')
    
    # Aplicar filtros
    if form.is_valid():
        if form.cleaned_data['fecha_desde']:
            eventos = eventos.filter(fecha_evento__date__gte=form.cleaned_data['fecha_desde'])
        
        if form.cleaned_data['fecha_hasta']:
            eventos = eventos.filter(fecha_evento__date__lte=form.cleaned_data['fecha_hasta'])
        
        if form.cleaned_data['municipio']:
            eventos = eventos.filter(municipio=form.cleaned_data['municipio'])
        
        if form.cleaned_data['asistencia']:
            asistio = form.cleaned_data['asistencia'] == 'True'
            eventos = eventos.filter(asistio_gobernador=asistio)
        
        if form.cleaned_data['tipo_evento']:
            es_festivo = form.cleaned_data['tipo_evento'] == 'True'
            eventos = eventos.filter(es_festivo=es_festivo)
        
        if form.cleaned_data['buscar']:
            busqueda = form.cleaned_data['buscar']
            eventos = eventos.filter(
                Q(nombre__icontains=busqueda) |
                Q(lugar__icontains=busqueda) |
                Q(responsable__icontains=busqueda) |
                Q(representante__icontains=busqueda)
            )
    
    context = {
        'eventos': eventos,
        'form': form,
        'total_eventos': eventos.count()
    }
    
    return render(request, 'eventos/lista_eventos.html', context)

# Vista para ver detalle de evento
@login_required
def detalle_evento(request, pk):
    """Detalle completo de un evento específico"""
    evento = get_object_or_404(Evento, pk=pk)
    
    # Si es una petición AJAX, devolver solo el contenido del modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'fetch' in request.META.get('HTTP_USER_AGENT', '').lower():
        return render(request, 'eventos/detalle_evento_modal.html', {'evento': evento})
    
    # Si no es AJAX, devolver página completa
    return render(request, 'eventos/detalle_evento.html', {'evento': evento})

# Vista de reportes
@login_required
def reportes(request):
    """Página de generación de reportes"""
    form = FiltroEventosForm(request.GET)
    eventos = Evento.objects.select_related('municipio', 'creado_por').order_by('-fecha_evento')
    
    # Aplicar filtros si existen
    if form.is_valid():
        if form.cleaned_data['fecha_desde']:
            eventos = eventos.filter(fecha_evento__date__gte=form.cleaned_data['fecha_desde'])
        if form.cleaned_data['fecha_hasta']:
            eventos = eventos.filter(fecha_evento__date__lte=form.cleaned_data['fecha_hasta'])
        if form.cleaned_data['municipio']:
            eventos = eventos.filter(municipio=form.cleaned_data['municipio'])
        if form.cleaned_data['asistencia']:
            asistio = form.cleaned_data['asistencia'] == 'True'
            eventos = eventos.filter(asistio_gobernador=asistio)
        if form.cleaned_data['tipo_evento']:
            es_festivo = form.cleaned_data['tipo_evento'] == 'True'
            eventos = eventos.filter(es_festivo=es_festivo)
        if form.cleaned_data['buscar']:
            busqueda = form.cleaned_data['buscar']
            eventos = eventos.filter(
                Q(nombre__icontains=busqueda) |
                Q(lugar__icontains=busqueda) |
                Q(responsable__icontains=busqueda)
            )
    
    # Estadísticas básicas
    total_eventos = eventos.count()
    eventos_gobernador = eventos.filter(asistio_gobernador=True).count()
    eventos_representante = eventos.filter(asistio_gobernador=False).count()
    eventos_festivos = eventos.filter(es_festivo=True).count()
    
    context = {
        'form': form,
        'eventos': eventos,
        'total_eventos': total_eventos,
        'eventos_gobernador': eventos_gobernador,
        'eventos_representante': eventos_representante,
        'eventos_festivos': eventos_festivos,
    }
    
    return render(request, 'reportes/reportes.html', context)

# Vista de estadísticas
@login_required
def estadisticas(request):
    """Página de estadísticas y gráficas"""
    from django.db.models import Count
    from collections import defaultdict
    import json
    
    # Estadísticas generales
    total_eventos = Evento.objects.count()
    eventos_gobernador = Evento.objects.filter(asistio_gobernador=True).count()
    eventos_representante = Evento.objects.filter(asistio_gobernador=False).count()
    eventos_festivos = Evento.objects.filter(es_festivo=True).count()
    
    # Eventos por municipio
    eventos_por_municipio = Evento.objects.values('municipio__nombre').annotate(
        total=Count('id')
    ).order_by('-total')[:10]  # Top 10
    
    # Eventos por mes (último año) - Corregido para PostgreSQL
    from django.utils import timezone
    from django.db.models import DateTimeField
    from django.db.models.functions import Extract, TruncMonth
    
    hace_un_ano = timezone.now() - timezone.timedelta(days=365)
    
    # Usar TruncMonth en lugar de DATE_FORMAT para PostgreSQL
    eventos_por_mes = Evento.objects.filter(
        fecha_evento__gte=hace_un_ano
    ).annotate(
        mes=TruncMonth('fecha_evento')
    ).values('mes').annotate(
        total=Count('id')
    ).order_by('mes')
    
    # Asistencia por municipio
    asistencia_por_municipio = Evento.objects.values(
        'municipio__nombre'
    ).annotate(
        total=Count('id'),
        gobernador=Count('id', filter=Q(asistio_gobernador=True)),
        representante=Count('id', filter=Q(asistio_gobernador=False))
    ).order_by('-total')[:15]
    
    # Preparar datos para gráficas (JSON)
    municipios_data = json.dumps({
        'labels': [item['municipio__nombre'] for item in eventos_por_municipio],
        'data': [item['total'] for item in eventos_por_municipio]
    })
    
    # Convertir las fechas de mes a formato legible
    meses_formateados = []
    for item in eventos_por_mes:
        fecha_mes = item['mes']
        mes_texto = fecha_mes.strftime('%Y-%m')
        meses_formateados.append({
            'mes': mes_texto,
            'total': item['total']
        })
    
    meses_data = json.dumps({
        'labels': [item['mes'] for item in meses_formateados],
        'data': [item['total'] for item in meses_formateados]
    })
    
    asistencia_data = json.dumps({
        'labels': [item['municipio__nombre'] for item in asistencia_por_municipio],
        'gobernador': [item['gobernador'] for item in asistencia_por_municipio],
        'representante': [item['representante'] for item in asistencia_por_municipio]
    })
    
    # Calcular porcentajes para el template
    porcentaje_gobernador = (eventos_gobernador * 100 / total_eventos) if total_eventos > 0 else 0
    porcentaje_representante = (eventos_representante * 100 / total_eventos) if total_eventos > 0 else 0
    porcentaje_festivos = (eventos_festivos * 100 / total_eventos) if total_eventos > 0 else 0
    
    context = {
        'total_eventos': total_eventos,
        'eventos_gobernador': eventos_gobernador,
        'eventos_representante': eventos_representante,
        'eventos_festivos': eventos_festivos,
        'porcentaje_gobernador': round(porcentaje_gobernador, 1),
        'porcentaje_representante': round(porcentaje_representante, 1),
        'porcentaje_festivos': round(porcentaje_festivos, 1),
        'municipios_data': municipios_data,
        'meses_data': meses_data,
        'asistencia_data': asistencia_data,
        'top_municipios': eventos_por_municipio,
    }
    
    return render(request, 'estadisticas/estadisticas.html', context)

# Vistas para generar reportes
@login_required
def generar_pdf(request):
    """Generar reporte en PDF"""
    # Temporalmente deshabilitado por problemas de WeasyPrint en Windows
    messages.warning(request, 'La generación de PDF está temporalmente deshabilitada. Use Excel por ahora.')
    return redirect('reportes')
    
    # Código original comentado:
    """
    form = FiltroEventosForm(request.GET)
    eventos = Evento.objects.select_related('municipio', 'creado_por').order_by('-fecha_evento')
    
    # Aplicar filtros
    if form.is_valid():
        if form.cleaned_data['fecha_desde']:
            eventos = eventos.filter(fecha_evento__date__gte=form.cleaned_data['fecha_desde'])
        if form.cleaned_data['fecha_hasta']:
            eventos = eventos.filter(fecha_evento__date__lte=form.cleaned_data['fecha_hasta'])
        if form.cleaned_data['municipio']:
            eventos = eventos.filter(municipio=form.cleaned_data['municipio'])
        if form.cleaned_data['asistencia']:
            asistio = form.cleaned_data['asistencia'] == 'True'
            eventos = eventos.filter(asistio_gobernador=asistio)
        if form.cleaned_data['tipo_evento']:
            es_festivo = form.cleaned_data['tipo_evento'] == 'True'
            eventos = eventos.filter(es_festivo=es_festivo)
    
    # Estadísticas
    total_eventos = eventos.count()
    eventos_gobernador = eventos.filter(asistio_gobernador=True).count()
    eventos_representante = eventos.filter(asistio_gobernador=False).count()
    
    context = {
        'eventos': eventos,
        'total_eventos': total_eventos,
        'eventos_gobernador': eventos_gobernador,
        'eventos_representante': eventos_representante,
        'fecha_generacion': timezone.now(),
        'filtros': form.cleaned_data if form.is_valid() else {}
    }
    
    # Renderizar template HTML
    html_string = render_to_string('reportes/reporte_pdf.html', context)
    
    # Generar PDF
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    
    # Respuesta HTTP
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_eventos_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf"'
    
    return response
    """

@login_required
def generar_excel(request):
    """Generar reporte en Excel"""
    form = FiltroEventosForm(request.GET)
    eventos = Evento.objects.select_related('municipio', 'creado_por').order_by('-fecha_evento')
    
    # Aplicar filtros
    if form.is_valid():
        if form.cleaned_data['fecha_desde']:
            eventos = eventos.filter(fecha_evento__date__gte=form.cleaned_data['fecha_desde'])
        if form.cleaned_data['fecha_hasta']:
            eventos = eventos.filter(fecha_evento__date__lte=form.cleaned_data['fecha_hasta'])
        if form.cleaned_data['municipio']:
            eventos = eventos.filter(municipio=form.cleaned_data['municipio'])
        if form.cleaned_data['asistencia']:
            asistio = form.cleaned_data['asistencia'] == 'True'
            eventos = eventos.filter(asistio_gobernador=asistio)
        if form.cleaned_data['tipo_evento']:
            es_festivo = form.cleaned_data['tipo_evento'] == 'True'
            eventos = eventos.filter(es_festivo=es_festivo)
    
    # Crear libro de Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte de Eventos"
    
    # Estilos
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    center_alignment = Alignment(horizontal="center", vertical="center")
    
    # Headers
    headers = [
        'Nombre del Evento', 'Fecha', 'Hora', 'Municipio', 'Lugar',
        'Responsable', 'Asistió Gobernador', 'Representante', 'Es Festivo',
        'Creado por', 'Fecha Creación'
    ]
    
    # Escribir headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
    
    # Escribir datos
    for row, evento in enumerate(eventos, 2):
        ws.cell(row=row, column=1, value=evento.nombre)
        ws.cell(row=row, column=2, value=evento.fecha_evento.strftime('%d/%m/%Y'))
        ws.cell(row=row, column=3, value=evento.fecha_evento.strftime('%H:%M'))
        ws.cell(row=row, column=4, value=evento.municipio.nombre)
        ws.cell(row=row, column=5, value=evento.lugar)
        ws.cell(row=row, column=6, value=evento.responsable)
        ws.cell(row=row, column=7, value='Sí' if evento.asistio_gobernador else 'No')
        ws.cell(row=row, column=8, value=evento.representante or 'N/A')
        ws.cell(row=row, column=9, value='Sí' if evento.es_festivo else 'No')
        ws.cell(row=row, column=10, value=evento.creado_por.get_full_name() or evento.creado_por.username)
        ws.cell(row=row, column=11, value=evento.fecha_creacion.strftime('%d/%m/%Y %H:%M'))
    
    # Ajustar ancho de columnas
    for column in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(column)].width = 15
    
    # Guardar en memoria
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    # Respuesta HTTP
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="reporte_eventos_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx"'
    
    return response