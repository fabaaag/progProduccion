from django.urls import path
from . import views

urlpatterns = [
    #Gestión de Operadores
    path('api/v1/operadores/', views.OperadorViewSet.as_view(), name='operador-list'),
    path('api/v1/operadores/<int:pk>/', views.OperadorDetailView.as_view(), name='operador-detail'),
    path('api/v1/operadores/<int:pk>/tareas/', views.OperadorTareasView.as_view(), name='operador-tares'),

    #Gestión de Máquinas por Operador
    path('api/v1/operadores/<int:pk>/maquinas/', views.OperadorMaquinasView.as_view(), name='operador_maquinas'),
    path('api/v1/operadores/por-maquina/<int:maquina_id>/', views.OperadoresPorMaquinaView.as_view(), name='operadores-por-maquina'),
    path('api/v1/operadores/por-maquina/', views.OperadoresPorMaquinaView.as_view(), name='operadores-por-maquina-query'),

    #Gestión de Asignaciones
    path('api/v1/asignaciones/', views.AsignacionOperadorView.as_view(), name='asignacion-list'),
    path('api/v1/asignaciones/<int:pk>/', views.AsignacionOperadorDetailView.as_view(), name='asignacion-detail'),
]
