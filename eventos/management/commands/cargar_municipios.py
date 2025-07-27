from django.core.management.base import BaseCommand
from eventos.models import Municipio

class Command(BaseCommand):
    help = 'Carga todos los municipios de Chiapas en la base de datos'

    def handle(self, *args, **options):
        # Lista completa de municipios de Chiapas
        municipios_chiapas = [
            "Acacoyagua", "Acala", "Acapetahua", "Altamirano", "Amatán", "Amatenango de la Frontera",
            "Amatenango del Valle", "Angel Albino Corzo", "Arriaga", "Bejucal de Ocampo",
            "Bella Vista", "Berriozábal", "Bochil", "Cacahoatán", "Catazajá", "Chalchihuitán",
            "Chamula", "Chanal", "Chapultenango", "Chenalhó", "Chiapa de Corzo", "Chiapilla",
            "Chicoasén", "Chicomuselo", "Chilón", "Escuintla", "Francisco León", "Frontera Comalapa",
            "Frontera Hidalgo", "Huehuetán", "Huixtán", "Huixtla", "Huitiupán", "Hunucmá",
            "Ixhuatán", "Ixtacomitán", "Ixtapa", "Ixtapangajoya", "Jiquipilas", "Jitotol",
            "Juárez", "Larráinzar", "La Libertad", "La Grandeza", "La Independencia", "La Trinitaria",
            "Las Margaritas", "Las Rosas", "Mapastepec", "Maravilla Tenejapa", "Marqués de Comillas",
            "Mazapa de Madero", "Mazatán", "Metapa", "Mitontic", "Motozintla", "Nicolás Ruíz",
            "Ocosingo", "Ocotepec", "Ocozocoautla de Espinosa", "Ostuacán", "Osumacinta",
            "Oxchuc", "Palenque", "Pantelhó", "Pantepec", "Pichucalco", "Pijijiapan",
            "Pueblo Nuevo Solistahuacán", "Rayón", "Reforma", "Sabanilla", "Salto de Agua",
            "San Andrés Duraznal", "San Cristóbal de las Casas", "San Fernando", "San Juan Cancuc",
            "San Lucas", "Santiago el Pinar", "Siltepec", "Simojovel", "Sitalá", "Socoltenango",
            "Solosuchiapa", "Soyaló", "Suchiapa", "Suchiate", "Sunuapa", "Tapachula",
            "Tapalapa", "Tapilula", "Tecpatán", "Tenejapa", "Teopisca", "Tila", "Tonalá",
            "Totolapa", "Tuxtla Gutiérrez", "Tuxtla Chico", "Tuzantán", "Tzimol", "Unión Juárez",
            "Venustiano Carranza", "Villa Comaltitlán", "Villa Corzo", "Villaflores", "Yajalón",
            "Zinacantán"
        ]

        self.stdout.write('Iniciando carga de municipios de Chiapas...')
        
        municipios_creados = 0
        municipios_existentes = 0
        
        for nombre_municipio in municipios_chiapas:
            municipio, created = Municipio.objects.get_or_create(
                nombre=nombre_municipio,
                defaults={'activo': True}
            )
            
            if created:
                municipios_creados += 1
                self.stdout.write(f'✓ Creado: {nombre_municipio}')
            else:
                municipios_existentes += 1
                self.stdout.write(f'- Ya existe: {nombre_municipio}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n¡Proceso completado!\n'
                f'Municipios creados: {municipios_creados}\n'
                f'Municipios que ya existían: {municipios_existentes}\n'
                f'Total de municipios en Chiapas: {len(municipios_chiapas)}'
            )
        )