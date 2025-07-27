from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('eventos/crear/', views.crear_evento, name='crear_evento'),
    path('eventos/editar/<int:pk>/', views.editar_evento, name='editar_evento'),
    path('eventos/finalizar/<int:pk>/', views.finalizar_evento, name='finalizar_evento'),
    path('eventos/cambiar-estado/<int:pk>/', views.cambiar_estado_evento, name='cambiar_estado_evento'),
    path('eventos/lista/', views.lista_eventos, name='lista_eventos'),
    path('eventos/detalle/<int:pk>/', views.detalle_evento, name='detalle_evento'),
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/pdf/', views.generar_pdf, name='generar_pdf'),
    path('reportes/excel/', views.generar_excel, name='generar_excel'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
]