from django_filters import rest_framework as filters
from django.db.models import Q
from.models import Producto, Pieza, FamiliaProducto, SubfamiliaProducto

class ProductoFilter(filters.FilterSet):
    search = filters.CharFilter(method='filter_search')
    codigo_producto = filters.CharFilter(lookup_expr='icontains')
    descripcion = filters.CharFilter(lookup_expr='icontains')
    familia_codigo = filters.CharFilter(field_name='familia_producto__codigo_familia')
    subfamilia_codigo = filters.CharFilter(field_name='subfamilia_producto__codigo_subfamilia')
    armado = filters.BooleanFilter()
    con_ruta = filters.BooleanFilter(method='filter_con_ruta')

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(codigo_producto__icontains=value) |
            Q(descripcion__icontains=value)
        )
    
    def filter_con_ruta(self, queryset, name, value):
        if value:
            return queryset.filter(rutas__isnull=False).distinct()
        return queryset

    class Meta:
        model = Producto
        fields = [
            'search', 'codigo_producto', 'descripcion',
            'familia_codigo', 'subfamilia_codigo', 
            'armado', 'con_ruta'
        ]

class PiezaFilter(filters.FilterSet):
    search = filters.CharFilter(method='filter_search')
    codigo_pieza = filters.CharFilter(lookup_expr='icontains')
    descripcion = filters.CharFilter(lookup_expr='icontains')
    familia_codigo = filters.CharFilter(field_name='familia_producto__codigo_familia')
    subfamilia_codigo = filters.CharFilter(field_name='subfamilia_producto__codigo_subfamilia')
    con_ruta = filters.BooleanFilter(method='filter_con_ruta')

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(codigo_pieza__icontains=value) |
            Q(descripcion__icontains=value)
        )
    
    def filter_con_ruta(self, queryset, name, value):
        if value:
            return queryset.filter(rutas__isnull=False).distinct()
        return queryset

    class Meta:
        model = Pieza
        fields = [
            'search', 'codigo_pieza', 'descripcion',
            'familia_codigo', 'subfamilia_codigo', 
            'con_ruta'
        ]