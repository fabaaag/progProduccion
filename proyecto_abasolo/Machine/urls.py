from django.urls import path
from . import views

urlpatterns = [
    path('api/v1/machines/', views.MachineListView.as_view(), name='machine-list'),
    path('api/v1/machine-types/', views.TipoMaquinaView.as_view(), name='machine-type-list'),
    path('api/v1/machines/<int:pk>/', views.MachineDetailView.as_view(), name='machine-detail'),
    path('api/v1/machines-diagnostico/', views.DiagnosticoMaquinasView.as_view(), name='machine-diagnostico'),
    path('api/v1/machines-diagnostico/<int:pk>/', views.DiagnosticoMaquinasView.as_view(), name='machine-diagnostico-detail'),
    path('api/v1/operator-machines/<int:operator_id>/', views.OperatorMachinesView.as_view(), name='operator-machines'),
    path('api/v1/operator-form-machines/', views.OperatorFormMachinesView.as_view(), name='operator-form-machines'),
]
