from django.urls import path
from .views_files import (
    program_views,
    machine_views,
    order_views,
    import_views,
    supervisor_views
)
from . import views
#Urls para Programas
urlpatterns = [
    #Imports
    path('importar_ots/', import_views.importar_ots_from_file, name='importar_ot'),
    path('importar_ruta_ot/', import_views.importar_rutaot_file),
        
    #Ordenes
    path('api/v1/ordenes/', order_views.OTView.as_view(), name='ordenes-list'),
    path('api/v1/ordenes/search/', order_views.search_orders, name='search-orders'),
    path('api/v1/ordenes/no_asignadas/', order_views.get_unassigned_ots, name='ordenes-unassigned'),

    #Programa
    path('api/v1/programas/crear_programa/', program_views.ProgramCreateView.as_view(), name='crear_programa'),
    path('api/v1/programas/', program_views.ProgramListView.as_view(), name='programas-list'),
    path('api/v1/programas/<int:pk>/', program_views.ProgramDetailView.as_view(), name='get-program'),
    path('api/v1/programas/<int:pk>/update-prio/', program_views.ProgramDetailView.as_view(), name='program-detail'),
    #path('api/v1/programas/<int:pk>/delete-orders/', program_views.UpdatePriorityView.as_view(), name='delete_orders'),
    path('api/v1/programas/<int:pk>/delete/', program_views.ProgramListView.as_view(), name='delete_program'),
    path('api/v1/programas/<int:pk>/generar_pdf/', program_views.GenerateProgramPDF.as_view(), name='generar_pdf'),
    path('api/v1/programas/<int:pk>/check-status/', program_views.ProgramDetailView.as_view(), name='check_status'),
    path('api/v1/programas/<int:pk>/add-orders/', program_views.AddOrdersToProgram.as_view(), name='add-orders-to-program'),
    path('api/v1/programas/<int:pk>/reajustar/', program_views.ReajustarProgramaView.as_view(), name='reajustar-programa'),

    #Maquinas
    path('api/v1/programas/<int:pk>/maquinas/', machine_views.MaquinasView.as_view(), name='maquinas-list'),
    path('api/v1/maquinas/', machine_views.MaquinaListView.as_view(), name='maquinas-get-list'),
    path('api/v1/empresas/', program_views.EmpresaListView.as_view(), name='empresas-get-list'),

    #Reporte
    path('api/v1/programas/<int:pk>/supervisor-report/', supervisor_views.SupervisorReportView.as_view(), name='supervisor-report'),
    path('api/v1/programas/<int:programa_id>/resumen-diario/<str:fecha>/', supervisor_views.ResumenDiarioView.as_view(), name='resumen-diario'),
    path('api/v1/programas/<int:pk>/supervisor-report/update-priority/', supervisor_views.SupervisorReportView.as_view(), name='supervisor-report'),
    path('api/v1/programas/<int:programa_id>/finalizar-dia/<str:fecha_str>/', supervisor_views.FinalizarDiaView.as_view(), name='finalizar_dia'),
    path('api/v1/reportes-supervisor/', supervisor_views.ReporteSupervisorListView.as_view(), name='reportes-supervisor-list'),
    path('api/v1/programas/<int:pk>/timeline-ejecucion/', supervisor_views.TimelineEjecucionView.as_view(), name='timeline-ejecucion'),
    path('api/supervisor/task/<int:task_id>/details/', supervisor_views.get_task_production_details, name='task_production_details'),
    # En urls.py
    path('api/v1/programas/<int:programa_id>/regenerar-tareas/', supervisor_views.regenerar_tareas_programa, name='regenerar-tareas'),
]


