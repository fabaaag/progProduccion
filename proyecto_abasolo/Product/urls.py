from django.urls import path
from . import views

urlpatterns = [
    # Endpoints de Productos
    path('productos/', views.ProductoListView.as_view(), name='producto-list'),
    path('productos/<int:id>/', views.ProductoDetailView.as_view(), name='producto-detail'),
    
    # Endpoints de Piezas
    path('piezas/', views.PiezaListView.as_view(), name='pieza-list'),
    path('piezas/<int:id>/', views.PiezaDetailView.as_view(), name='pieza-detail'),
    
    # Endpoints comunes
    path('familias/', views.FamiliaProductoView.as_view(), name='familia-list'),
    path('subfamilias/', views.SubfamiliaProductoView.as_view(), name='subfamilia-list'),
]
