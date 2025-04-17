import pytz
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from datetime import datetime, timedelta

from .models import Operador, OperadorMaquina, AsignacionOperador
from .serializers import (
    OperadorSerializer,
    OperadorMaquinaSerializer,
    AsignacionOperadorSerializer
)
from JobManagement.models import Maquina, ProgramaProduccion
from JobManagement.serializers import MaquinaSerializer

class OperadorViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Lista todos los operadores con filtros opcionales"""
        queryset = Operador.objects.all()

        #Filtros
        empresa = request.query_params.get('empresa')
        activo = request.query_params.get('activo')
        maquina = request.query_params.get('maquina')

        if empresa:
            queryset = queryset.filter(empresa_id=empresa)
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')
        if maquina:
            queryset = queryset.filter(maquinas_habilitadas__id=maquina)

        serializer = OperadorSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Crear nuevo operador"""
        serializer = OperadorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class OperadorDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Obtener detalles de un operador específico"""
        operador = get_object_or_404(Operador, pk=pk)
        serializer = OperadorSerializer(operador)
        return Response(serializer.data)
    
    def put(self, request, pk):
        """Actualizar operador"""
        operador = get_object_or_404(Operador, pk=pk)
        serializer = OperadorSerializer(operador, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """Desactivar operador (soft delete)"""
        operador = get_object_or_404(Operador, pk=pk)
        operador.activo = False
        operador.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class OperadorMaquinasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Obtener máquinas habilitadas para un operador"""
        operador = get_object_or_404(Operador, pk=pk)
        maquinas = operador.maquinas_habilitadas.all()
        serializer = MaquinaSerializer(maquinas, many=True)
        return Response(serializer.data)
    
    def post(self, request, pk):
        """Actualizar habilitaciones de máquinas para un operador"""
        operador = get_object_or_404(Operador, pk=pk)
        maquinas_ids = request.data.get('maquinas_habilitadas', request.data.get('maquinas', []))
        print('maqs', maquinas_ids)

        #Actualizar habilitaciones
        OperadorMaquina.objects.filter(operador=operador).delete()
        for maquina_id in maquinas_ids:
            OperadorMaquina.objects.create(
                operador=operador,
                maquina_id=maquina_id
            )

        return Response({"message": "Habilitaciones actualizadas"})
    

from django.utils import timezone
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from django.conf import settings
from JobManagement.models import ItemRuta

class AsignacionOperadorView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Obtener asignaciones con filtros"""
        queryset = AsignacionOperador.objects.all()

        #Filtros
        programa_id = request.query_params.get('programa')
        operador_id = request.query_params.get('operador')
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')

        if programa_id:
            queryset = queryset.filter(programa_id=programa_id)
        if operador_id:
            queryset = queryset.filter(operador_id=operador_id)
        if fecha_inicio and fecha_fin:
            queryset = queryset.filter(
                Q(fecha_inicio__range=[fecha_inicio, fecha_fin]) |
                Q(fecha_fin__range=[fecha_inicio, fecha_fin])
            )

        serializer = AsignacionOperadorSerializer(queryset, many=True)
        return Response(serializer.data)
    

    def post(self, request):
        try:
            programa_id = request.data.get('programa_id')
            item_ruta_id = request.data.get('item_ruta_id')
            operador_id = request.data.get('operador_id')
            fecha_inicio = request.data.get('fecha_inicio')
            fecha_fin = request.data.get('fecha_fin')
            is_removing = request.data.get('is_removing', False)
            
            # Validar datos
            if not programa_id or not item_ruta_id:
                return Response(
                    {"error": "Se requieren programa_id e item_ruta_id"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obtener objetos
            try:
                programa = ProgramaProduccion.objects.get(pk=programa_id)
                item_ruta = ItemRuta.objects.get(pk=item_ruta_id)
            except (ProgramaProduccion.DoesNotExist, ItemRuta.DoesNotExist):
                return Response(
                    {"error": "Programa o ItemRuta no encontrado"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Si estamos desasignando
            if is_removing:
                # Buscar y eliminar asignaciones existentes
                asignaciones = AsignacionOperador.objects.filter(
                    programa=programa,
                    item_ruta=item_ruta
                )
                if asignaciones.exists():
                    asignaciones.delete()
                    return Response(
                        {"message": "Operador desasignado correctamente"},
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {"message": "No había operador asignado"},
                        status=status.HTTP_200_OK
                    )
            
            # Si estamos asignando
            if not operador_id:
                return Response(
                    {"error": "Se requiere operador_id para asignar"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                operador = Operador.objects.get(pk=operador_id)
            except Operador.DoesNotExist:
                return Response(
                    {"error": "Operador no encontrado"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Convertir fechas a objetos datetime
            try:
                fecha_inicio_dt = parse_datetime(fecha_inicio)
                fecha_fin_dt = parse_datetime(fecha_fin)
                
                # IMPORTANTE: Usamos las fechas exactas del frontend sin modificarlas
                # Solo aseguramos que tengan zona horaria
                
                print(f"[Backend] Fecha inicio recibida: {fecha_inicio}")
                print(f"[Backend] Fecha fin recibida: {fecha_fin}")
                
                # Hacer las fechas timezone-aware si no lo son
                if settings.USE_TZ:
                    if fecha_inicio_dt.tzinfo is None:
                        fecha_inicio_dt = timezone.make_aware(fecha_inicio_dt, timezone=pytz.timezone('America/Santiago'))
                    if fecha_fin_dt.tzinfo is None:
                        fecha_fin_dt = timezone.make_aware(fecha_fin_dt, timezone=pytz.timezone('America/Santiago'))
                    # Si la fecha ya tiene zona horaria, convertirla a la zona horaria de Chile
                    else:
                        fecha_inicio_dt = fecha_inicio_dt.astimezone(pytz.timezone('America/Santiago'))
                        fecha_fin_dt = fecha_fin_dt.astimezone(pytz.timezone('America/Santiago'))
            except Exception as e:
                return Response(
                    {"error": f"Error al procesar fechas: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Eliminar asignaciones existentes para este item_ruta
            AsignacionOperador.objects.filter(
                programa=programa,
                item_ruta=item_ruta
            ).delete()
            
            # Crear nueva asignación
            asignacion = AsignacionOperador.objects.create(
                operador=operador,
                item_ruta=item_ruta,
                programa=programa,
                fecha_inicio=fecha_inicio_dt,
                fecha_fin=fecha_fin_dt,
                asignado_por=request.user
            )
            
            serializer = AsignacionOperadorSerializer(asignacion)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
        except Exception as e:
            return Response(
                {"error": f"Error al procesar la asignación: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AsignacionOperadorDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        """Eliminar una asignación"""
        asignacion = get_object_or_404(AsignacionOperador, pk=pk)
        asignacion.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class OperadorTareasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Obtiene todas las tareas asignadas a un operador específico, organizadas por programa y orden de trabajo"""

        try:
            operador = get_object_or_404(Operador, pk=pk)

            asignaciones = AsignacionOperador.objects.filter(
                operador=operador
            ).select_related(
                'programa',
                'item_ruta',
                'item_ruta__proceso',
                'item_ruta__maquina',
                'item_ruta__ruta',
                'item_ruta__ruta__orden_trabajo'
            ).order_by('fecha_inicio')
            print('after asign')
            tareas_asignadas = []

            print('data: ', asignaciones)
            for asignacion in asignaciones:
                try:
                        
                    item_ruta = asignacion.item_ruta
                    orden_trabajo = item_ruta.ruta.orden_trabajo

                    # Calcular cantidades diarias basadas en el estándar
                    estandar = float(item_ruta.estandar if item_ruta.estandar > 0 else 500)
                    cantidad_total = float(item_ruta.cantidad_pedido)
                    dias_trabajo = max(1, int(cantidad_total / estandar))
                    cantidad_diaria = min(estandar, cantidad_total)

                    tarea = {
                        'programa': {
                            'id' : asignacion.programa.id,
                            'nombre': asignacion.programa.nombre
                        },
                        'orden_trabajo': {
                            'codigo': orden_trabajo.codigo_ot,
                            'descripcion': orden_trabajo.descripcion_producto_ot
                        },
                        'proceso':{
                            'codigo': item_ruta.proceso.codigo_proceso,
                            'descripcion': item_ruta.proceso.descripcion
                        },
                        'maquina': {
                            'codigo': item_ruta.maquina.codigo_maquina if item_ruta.maquina else 'N/A',
                            'descripcion': item_ruta.maquina.descripcion if item_ruta.maquina else 'Sin máquina'
                        },
                        'fechas': {
                            'inicio': asignacion.fecha_inicio,
                            'fin': asignacion.fecha_fin
                        },
                        'produccion': {
                            'cantidad_total': cantidad_total,
                            'estandar_diario': estandar,
                            'dias_estimados': dias_trabajo,
                            'cantidad_diaria': cantidad_diaria
                        }
                    }

                    tareas_asignadas.append(tarea)
                    print(tareas_asignadas)
                except Exception as e:
                    print(f'[Backend] Error procesando asignación {asignacion.id}: {str(e)}')

            print(f'[Backend] Total de tareas procesadas: {len(tareas_asignadas)}')
            
            return Response({
                'operador': {
                    'id': operador.id,
                    'nombre': operador.nombre,
                    'rut': operador.rut
                },
                'tareas': tareas_asignadas
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            print(f'[Backend] Error general obteniendo tareas: {str(e)}')
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Error obteniendo tareas del operador: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OperadoresPorMaquinaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, maquina_id=None):
        """Obtiene operadores habilitados para una máquina específica"""
        try:
            # Verificar si se proporcionó un ID de máquina
            if not maquina_id:
                maquina_id = request.query_params.get('maquina_id')
                if not maquina_id:
                    return Response(
                        {"error": "Se requiere un ID de máquina"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            print(f"[Backend] Buscando operadores para máquina ID: {maquina_id}")
            
            # Obtener la máquina
            try:
                maquina = Maquina.objects.get(id=maquina_id)
                print(f"[Backend] Máquina encontrada: {maquina.codigo_maquina} - {maquina.descripcion}")
            except Maquina.DoesNotExist:
                print(f"[Backend] Máquina con ID {maquina_id} no encontrada")
                return Response(
                    {"error": f"Máquina con ID {maquina_id} no encontrada"},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                print(f"[Backend] Error al buscar máquina: {str(e)}")
                return Response(
                    {"error": f"Error al buscar máquina: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Obtener operadores habilitados para esta máquina
            try:
                operadores = Operador.objects.filter(
                    maquinas_habilitadas=maquina,
                    activo=True
                ).distinct()
                
                print(f"[Backend] Operadores encontrados: {operadores.count()}")
                
                serializer = OperadorSerializer(operadores, many=True)
                return Response(serializer.data)
            except Exception as e:
                print(f"[Backend] Error al filtrar operadores: {str(e)}")
                return Response(
                    {"error": f"Error al filtrar operadores: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            print(f"[Backend] Error general: {str(e)}")
            return Response(
                {"error": f"Error al obtener operadores: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )