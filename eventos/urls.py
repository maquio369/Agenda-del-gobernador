# eventos/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),
    
    # Gestión básica de eventos
    path('eventos/crear/', views.crear_evento, name='crear_evento'),
    path('eventos/editar/<int:pk>/', views.editar_evento, name='editar_evento'),
    path('eventos/detalle/<int:pk>/', views.detalle_evento, name='detalle_evento'),
    path('eventos/lista/', views.lista_eventos, name='lista_eventos'),
    
    # Acciones de eventos
    path('eventos/finalizar/<int:pk>/', views.finalizar_evento, name='finalizar_evento'),
    path('eventos/cambiar-estado/<int:pk>/', views.cambiar_estado_evento, name='cambiar_estado_evento'),
    path('eventos/actualizar-estados/', views.actualizar_estados_eventos, name='actualizar_estados_eventos'),
    
    # Rutas de debug
    path('debug/fechas/', views.verificar_fechas_eventos, name='verificar_fechas_eventos'),
    path('debug/cambiar-fecha/<int:pk>/', views.cambiar_fecha_evento_debug, name='cambiar_fecha_evento_debug'),
    path('debug/crear-eventos-prueba/', views.crear_eventos_prueba, name='crear_eventos_prueba'),
    
    # Reportes y estadísticas
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/excel/', views.generar_excel, name='generar_excel'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
]