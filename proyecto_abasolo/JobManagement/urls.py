from django.urls import path
from . import views

urlpatterns = [
    path('importar_ots/', views.importar_ots_from_file, name='importar_ot'),
    path('importar_ruta_ot/', views.importar_rutaot_file)
]

#Urls para OT
urlpatterns += [
    path('api/v1/ordenes/', views.OTView.as_view(), name='ordenes-list'),
]

#Urls para Programas
urlpatterns += [
    path('api/v1/programas/crear_programa/', views.ProgramCreateView.as_view(), name='crear_programa'),
    path('api/v1/ordenes/no_asignadas/', views.get_unassigned_ots, name='ordenes-unassigned'),
    path('api/v1/programas/', views.ProgramListView.as_view(), name='programas-list'),
    path('api/v1/programas/<int:pk>/', views.ProgramDetailView.as_view(), name='get-program'),
    path('api/v1/programas/<int:pk>/update-prio/', views.UpdatePriorityView.as_view(), name='program-detail'),
    path('api/v1/programas/<int:pk>/delete-orders/', views.UpdatePriorityView.as_view(), name='delete_orders'),
    path('api/v1/programas/<int:pk>/delete/', views.ProgramListView.as_view(), name='delete_program'),
    path('api/v1/programas/<int:pk>/generar_pdf/', views.GenerateProgramPDF.as_view(), name='generar_pdf'),
    path('api/v1/programas/<int:programa_id>/procesos/<int:proceso_id>/timeline/', views.ProcesoTimelineView.as_view(), name='proceso-timeline'),
    path('api/v1/procesos/<int:pk>/', views.ProcesoDetailView.as_view(), name='proceso-detail'),
    path('api/v1/procesos/', views.ProcesoListView.as_view(), name='proceso-list'),
    path('api/v1/programas/<int:pk>/supervisor-report/', views.SupervisorReportView.as_view(), name='supervisor-report'),
    path('api/v1/programas/<int:pk>/supervisor-report/update-priority/', views.SupervisorReportView.as_view(), name='supervisor-report'),
    path('api/v1/programas/<int:programa_id>/finalizar-dia/<str:fecha_str>/', views.FinalizarDiaReporteView.as_view(), name='finalizar_dia'),
    path('api/v1/tareas/<int:tarea_id>/genealogia/', views.TareaGenealogiaView.as_view(), name='tarea_genealogia'),
]

#Urls para maquinas dentro del programa
urlpatterns += [
    path('api/v1/programas/<int:pk>/maquinas/', views.MaquinasView.as_view(), name='maquinas-list'),
    path('api/v1/maquinas/', views.MaquinaListView.as_view(), name='maquinas-get-list'),
    path('api/v1/empresas/', views.EmpresaListView.as_view(), name='empresas-get-list'),
    path('api/v1/programas/<int:pk>/asignaciones/', views.ProgramDetailView.as_view(), name='asignaciones-programa')
]

urlpatterns += [
    path('api/v1/ordenes/search/', views.search_orders, name='search-orders'),
]
