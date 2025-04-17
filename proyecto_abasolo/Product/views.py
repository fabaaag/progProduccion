from rest_framework import generics
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Producto, Pieza, FamiliaProducto, SubfamiliaProducto
from .serializers import (
    ProductoSerializer, PiezaSerializer, 
    FamiliaProductoSerializer, SubfamiliaProductoSerializer
)
from .filters import ProductoFilter, PiezaFilter
from .pagination import ProductoPagination, PiezaPagination

# Vistas de Productos
class ProductoListView(generics.ListAPIView):
    serializer_class = ProductoSerializer
    pagination_class = ProductoPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductoFilter
    search_fields = ['codigo_producto', 'descripcion']
    ordering_fields = ['codigo_producto', 'descripcion']
    ordering = ['codigo_producto']

    def get_queryset(self):
        return Producto.objects.all().select_related(
            'familia_producto',
            'subfamilia_producto',
            'ficha_tecnica',
            'und_medida'
        ).prefetch_related('rutas')

class ProductoDetailView(generics.RetrieveAPIView):
    serializer_class = ProductoSerializer
    lookup_field = 'id'
    queryset = Producto.objects.all().select_related(
        'familia_producto',
        'subfamilia_producto',
        'ficha_tecnica',
        'und_medida'
    ).prefetch_related('rutas')

# Vistas de Piezas
class PiezaListView(generics.ListAPIView):
    serializer_class = PiezaSerializer
    pagination_class = PiezaPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PiezaFilter
    search_fields = ['codigo_pieza', 'descripcion']
    ordering_fields = ['codigo_pieza', 'descripcion']
    ordering = ['codigo_pieza']

    def get_queryset(self):
        return Pieza.objects.all().select_related(
            'familia_producto',
            'subfamilia_producto',
            'ficha_tecnica',
            'und_medida'
        ).prefetch_related('rutas')

class PiezaDetailView(generics.RetrieveAPIView):
    serializer_class = PiezaSerializer
    lookup_field = 'id'
    queryset = Pieza.objects.all().select_related(
        'familia_producto',
        'subfamilia_producto',
        'ficha_tecnica',
        'und_medida'
    ).prefetch_related('rutas')

# Vistas comunes para Familias y Subfamilias
class FamiliaProductoView(generics.ListAPIView):
    serializer_class = FamiliaProductoSerializer
    ordering = ['codigo_familia']

    def get_queryset(self):
        tipo = self.request.query_params.get('tipo', 'ambos')
        queryset = FamiliaProducto.objects.all()
        
        if tipo == 'productos':
            queryset = queryset.filter(producto__isnull=False)
        elif tipo == 'piezas':
            queryset = queryset.filter(pieza__isnull=False)
        
        return queryset.distinct().order_by('codigo_familia')

class SubfamiliaProductoView(generics.ListAPIView):
    serializer_class = SubfamiliaProductoSerializer
    ordering = ['codigo_subfamilia']

    def get_queryset(self):
        familia_codigo = self.request.query_params.get('familia_codigo')
        tipo = self.request.query_params.get('tipo', 'ambos')
        
        queryset = SubfamiliaProducto.objects.all()
        
        if familia_codigo:
            queryset = queryset.filter(familia_producto__codigo_familia=familia_codigo)
        
        if tipo == 'productos':
            queryset = queryset.filter(producto__isnull=False)
        elif tipo == 'piezas':
            queryset = queryset.filter(pieza__isnull=False)
            
        return queryset.distinct().order_by('codigo_subfamilia')
    