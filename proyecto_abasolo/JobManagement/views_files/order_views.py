from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from ..models import OrdenTrabajo, ProgramaOrdenTrabajo
from ..serializers import OrdenTrabajoSerializer

class OTView(generics.ListAPIView):
    serializer_class = OrdenTrabajoSerializer
    queryset = OrdenTrabajo.objects.all()

@api_view(['GET'])
def search_orders(request):
    search_term = request.GET.get('search', '')
    status = request.GET.get('status', 'all')

    queryset = OrdenTrabajo.objects.all()

    if search_term:
        queryset = queryset.filter(
            Q(codigo_ot__icontains=search_term) |
            Q(descripcion_producto_ot__icontains=search_term) |
            Q(cliente__nombre__icontains=search_term)
        )

    if status != 'all':
        queryset = queryset.filter(situacion_ot__codigo_situacion_ot=status)

    queryset = queryset.select_related(
        'tipo_ot',
        'situacion_ot',
        'cliente',
        'materia_prima'
    ).prefetch_related(
        'ruta_ot__items__proceso',
        'ruta_ot__items__maquina'
    )

    serializer = OrdenTrabajoSerializer(queryset, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_unassigned_ots(request):
    try:
        ordenes_unassigned = OrdenTrabajo.objects.filter(
            ~Q(id__in=ProgramaOrdenTrabajo.objects.values_list('orden_trabajo_id', flat=True))
        )
        serializer = OrdenTrabajoSerializer(ordenes_unassigned, many=True)
        return Response(serializer.data, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
                       