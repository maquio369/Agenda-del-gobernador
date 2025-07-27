# eventos/management/commands/actualizar_estados.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from eventos.models import Evento
import pytz

class Command(BaseCommand):
    help = 'Actualiza los estados de todos los eventos automáticamente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué cambios se harían sin aplicarlos',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra información detallada',
        )
        parser.add_argument(
            '--solo-hoy',
            action='store_true',
            help='Solo procesa eventos de hoy',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        solo_hoy = options['solo_hoy']
        
        # Configurar zona horaria de México
        mexico_tz = pytz.timezone('America/Mexico_City')
        ahora_mexico = timezone.now().astimezone(mexico_tz)
        hoy = ahora_mexico.date()
        
        self.stdout.write('=' * 60)
        self.stdout.write('ACTUALIZADOR DE ESTADOS DE EVENTOS')
        self.stdout.write('=' * 60)
        self.stdout.write(f'Fecha/hora actual (México): {ahora_mexico}')
        self.stdout.write(f'Fecha de hoy: {hoy}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se guardarán cambios'))
        
        # Obtener eventos
        if solo_hoy:
            eventos = Evento.objects.filter(fecha_evento__date=hoy).order_by('fecha_evento')
            self.stdout.write(f'Procesando solo eventos de hoy...')
        else:
            eventos = Evento.objects.all().order_by('fecha_evento')
            self.stdout.write(f'Procesando todos los eventos...')
        
        total_eventos = eventos.count()
        cambios = 0
        
        self.stdout.write(f'Total de eventos a revisar: {total_eventos}')
        self.stdout.write('-' * 60)
        
        for evento in eventos:
            estado_anterior = evento.estado
            fecha_evento_mexico = evento.fecha_evento.astimezone(mexico_tz)
            
            if not dry_run:
                nuevo_estado = evento.actualizar_estado_automatico()
            else:
                # Simular el cálculo sin guardar
                if evento.fecha_finalizacion_manual:
                    nuevo_estado = evento.estado
                elif ahora_mexico < fecha_evento_mexico:
                    nuevo_estado = 'programado'
                elif ahora_mexico >= fecha_evento_mexico and ahora_mexico < (fecha_evento_mexico + timezone.timedelta(hours=1)):
                    nuevo_estado = 'en_curso'
                else:
                    nuevo_estado = 'finalizado'
            
            # Verificar si es evento de hoy
            es_hoy = fecha_evento_mexico.date() == hoy
            marca_hoy = "📅 HOY" if es_hoy else ""
            
            if estado_anterior != nuevo_estado:
                cambios += 1
                if verbose or dry_run:
                    self.stdout.write(
                        f'{marca_hoy} {evento.nombre} | '
                        f'{fecha_evento_mexico.strftime("%d/%m/%Y %H:%M")} | '
                        f'{estado_anterior} → {nuevo_estado}'
                    )
            elif verbose:
                self.stdout.write(
                    f'{marca_hoy} {evento.nombre} | '
                    f'{fecha_evento_mexico.strftime("%d/%m/%Y %H:%M")} | '
                    f'{nuevo_estado} (sin cambios)'
                )
        
        self.stdout.write('-' * 60)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Se cambiarían {cambios} eventos de {total_eventos}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Actualizados {cambios} eventos de {total_eventos}')
            )
        
        # Mostrar estadísticas actuales
        self.stdout.write('\n📊 ESTADÍSTICAS ACTUALES')
        self.stdout.write('=' * 30)
        for estado_key, estado_nombre in Evento.ESTADO_CHOICES:
            count = eventos.filter(estado=estado_key).count()
            self.stdout.write(f'{estado_nombre}: {count} eventos')
        
        # Mostrar eventos de hoy
        eventos_hoy = eventos.filter(fecha_evento__date=hoy)
        
        self.stdout.write(f'\n📅 EVENTOS DE HOY ({hoy.strftime("%d/%m/%Y")})')
        self.stdout.write('=' * 40)
        
        if eventos_hoy.exists():
            for evento in eventos_hoy:
                fecha_evento_mexico = evento.fecha_evento.astimezone(mexico_tz)
                estado_emoji = {
                    'programado': '⏰',
                    'en_curso': '▶️',
                    'finalizado': '✅',
                    'cancelado': '❌'
                }.get(evento.estado, '❓')
                
                self.stdout.write(
                    f'{estado_emoji} {evento.nombre} | '
                    f'{fecha_evento_mexico.time().strftime("%H:%M")} | '
                    f'{evento.get_estado_display()}'
                )
                
                # Mostrar detalles adicionales si es evento de hoy
                if evento.es_evento_hoy:
                    tiempo_transcurrido = evento.tiempo_transcurrido
                    if tiempo_transcurrido:
                        horas = int(tiempo_transcurrido.total_seconds() / 3600)
                        minutos = int((tiempo_transcurrido.total_seconds() % 3600) / 60)
                        self.stdout.write(f'    └─ Tiempo transcurrido: {horas}h {minutos}m')
        else:
            self.stdout.write('No hay eventos programados para hoy')
        
        # Mostrar próximos eventos
        manana = hoy + timezone.timedelta(days=1)
        eventos_manana = Evento.objects.filter(fecha_evento__date=manana)
        
        if eventos_manana.exists():
            self.stdout.write(f'\n📅 EVENTOS DE MAÑANA ({manana.strftime("%d/%m/%Y")})')
            self.stdout.write('=' * 42)
            for evento in eventos_manana:
                fecha_evento_mexico = evento.fecha_evento.astimezone(mexico_tz)
                self.stdout.write(
                    f'⏰ {evento.nombre} | {fecha_evento_mexico.time().strftime("%H:%M")}'
                )
        
        self.stdout.write('\n✅ ¡Actualización completada!')
        
        if solo_hoy and not eventos_hoy.exists():
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  No se encontraron eventos para hoy. '
                    'Ejecuta el comando sin --solo-hoy para ver todos los eventos.'
                )
            )