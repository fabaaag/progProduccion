from django.forms import CheckboxSelectMultiple
from django_filters import rest_framework as filters
from django_filters import MultipleChoiceFilter, BaseInFilter

from django.db.models import Q
from django.db.models.functions import Lower
from django.db.models import Count, Case, When, IntegerField

import re
from .models import OrdenTrabajo, TipoOT

import logging

logger = logging.getLogger(__name__)

class OrdenTrabajoFilter(filters.FilterSet):
    fecha_emision_termino = filters.DateFromToRangeFilter(field_name='fecha_termino', label='Fecha de Término')
    fecha_prod = filters.DateFromToRangeFilter(field_name='fecha_proc', label='Fecha de Producción')
    cliente = filters.CharFilter(method='filter_cliente', label='Cliente')
    descripcion_producto_ot = filters.CharFilter(field_name='descripcion_producto_ot', label='Descripción Producto', lookup_expr='icontains')
    empresa = filters.CharFilter(field_name='empresa__apodo', label='Descripción Producto', lookup_expr='icontains')
    tipo_ot = filters.BaseInFilter(field_name='tipo_ot__codigo_tipo_ot', label = 'Codigo Tipo OT', lookupexpr='in')
    multa = filters.BooleanFilter(field_name='multa', label='¿Multa?')
    codigo_ot = filters.CharFilter(field_name='codigo_ot', label='Código OT', lookup_expr='exact')

    class Meta:
        model = OrdenTrabajo
        fields = ['fecha_emision_termino', 'fecha_prod', 'cliente', 'descripcion_producto_ot', 'empresa', 'tipo_ot', 'situacion_ot', 'multa', 'codigo_ot']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        if not self.request.GET.getlist('situacion_ot'):
            queryset = queryset.filter(situacion_ot__codigo_situacion_ot__in = ['S', 'P'])
        return queryset
    
    def filter_cliente(self, queryset, name, value):
        return queryset.filter(
            Q(cliente__codigo_cliente__icontains=value) |
            Q(cliente__nombre__icontains = value)

        )