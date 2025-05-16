from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import TipoMaquina, EstadoOperatividad, EstadoMaquina
from JobManagement.models import Maquina, Proceso, OrdenTrabajo, ItemRuta
from django.shortcuts import get_object_or_404
from .serializers import TipoMaquinaSerializer

class MachineListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        """Obtener lista de máquinas con su estado y tipos"""
        try:
            maquinas = Maquina.objects.select_related(
                'estadomaquina',
                'estadomaquina__estado_operatividad'
            ).prefetch_related(
                'estadomaquina__tipos_maquina'
            ).all()

            data = []
            for maquina in maquinas:
                maquina_data = {
                    'id': maquina.id,
                    'codigo': maquina.codigo_maquina,
                    'descripcion': maquina.descripcion,
                    'tipos_maquina': [
                        {
                            'id': tipo.id,
                            'codigo': tipo.codigo,
                            'descripcion': tipo.descripcion
                        }
                        for tipo in maquina.estadomaquina.tipos_maquina.all()
                    ] if hasattr(maquina, 'estadomaquina') else [],
                    'estado_operatividad': {
                        'estado': maquina.estadomaquina.estado_operatividad.estado,
                        'descripcion': maquina.estadomaquina.estado_operatividad.get_estado_display()
                    } if hasattr(maquina, 'estadomaquina') and maquina.estadomaquina.estado_operatividad else None,
                    'capacidad_hora': float(maquina.estadomaquina.capacidad_hora) if hasattr(maquina, 'estadomaquina') and maquina.estadomaquina.capacidad_hora else 0,
                    'factor_eficiencia': float(maquina.estadomaquina.factor_eficiencia) if hasattr(maquina, 'estadomaquina') else 1.00
                }
                data.append(maquina_data)
            
            return Response(data)
        except Exception as e:
            print(f"Error en MachineListView: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MachineDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        try:
            maquina = Maquina.objects.select_related(
                'estadomaquina',
                'estadomaquina__estado_operatividad',
                'empresa'
            ).prefetch_related(
                'estadomaquina__tipos_maquina'
            ).get(pk=pk)

            # Obtener procesos asociados a los tipos de máquina
            tipos_maquina_ids = maquina.estadomaquina.tipos_maquina.values_list('id', flat=True)
            procesos_asociados = Proceso.objects.filter(
                tipos_maquina_compatibles__in=tipos_maquina_ids
            ).distinct().values('id', 'codigo_proceso', 'descripcion')

            # Obtener órdenes de trabajo asociadas
            ordenes_trabajo = OrdenTrabajo.objects.filter(
                ruta_ot__items__maquina=maquina
            ).distinct().select_related('situacion_ot').values(
                'codigo_ot',
                'situacion_ot__codigo_situacion_ot',
                'situacion_ot__descripcion',
                'descripcion_producto_ot'
            )

            data = {
                'id': maquina.id,
                'codigo_maquina': maquina.codigo_maquina,
                'descripcion': maquina.descripcion,
                'sigla': maquina.sigla,
                'carga': float(maquina.carga),
                'golpes': maquina.golpes,
                'empresa': {
                    'id': maquina.empresa.id,
                    'nombre': maquina.empresa.nombre
                } if maquina.empresa else None,
                'estado': {
                    'tipos_maquina': [{
                        'id': tipo.id,
                        'codigo': tipo.codigo,
                        'descripcion': tipo.descripcion,
                    } for tipo in maquina.estadomaquina.tipos_maquina.all()],
                    'estado_operatividad': {
                        'id': maquina.estadomaquina.estado_operatividad.id,
                        'estado': maquina.estadomaquina.estado_operatividad.estado,
                        'descripcion': maquina.estadomaquina.estado_operatividad.get_estado_display()
                    } if maquina.estadomaquina.estado_operatividad else None,
                    'capacidad_hora': float(maquina.estadomaquina.capacidad_hora) if maquina.estadomaquina.capacidad_hora else 0,
                    'factor_eficiencia': float(maquina.estadomaquina.factor_eficiencia),
                    'horario': {
                        'hora_inicio': maquina.estadomaquina.hora_inicio_normal.strftime('%H:%M'),
                        'hora_fin': maquina.estadomaquina.hora_fin_normal.strftime('%H:%M')
                    }
                },
                'procesos_asociados': list(procesos_asociados),
                'ordenes_trabajo': [{
                    'codigo_ot': ot['codigo_ot'],
                    'situacion': ot['situacion_ot__descripcion'],
                    'situacion_codigo': ot['situacion_ot__codigo_situacion_ot'],
                    'descripcion': ot['descripcion_producto_ot']
                } for ot in ordenes_trabajo]
            }
            return Response(data)
        except Maquina.DoesNotExist:
            return Response(
                {'error': 'Máquina no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"Error en MachineDetailView: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    
        
class TipoMaquinaView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        """Obtener todos los tipos de máquina con su información completa"""
        try:
            tipos = TipoMaquina.objects.all()
            serializer = TipoMaquinaSerializer(tipos, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DiagnosticoMaquinasView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            diagnostico = {
                'maquinas_sin_tipo': [],
                'maquinas_sin_procesos': [],
                'maquinas_con_procesos': [],
                'maquinas_en_ot': []
            }

            # Obtener todas las máquinas con sus relaciones
            maquinas = Maquina.objects.select_related(
                'estadomaquina',
                'empresa'
            ).prefetch_related(
                'estadomaquina__tipos_maquina'
            ).all()

            for maquina in maquinas:
                maquina_info = {
                    'id': maquina.id,
                    'codigo': maquina.codigo_maquina,
                    'descripcion': maquina.descripcion,
                    'empresa': maquina.empresa.nombre if maquina.empresa else 'Sin empresa',
                    'tipos': [],
                    'procesos': [],
                    'ordenes_trabajo': []
                }

                # Verificar tipos de máquina
                if hasattr(maquina, 'estadomaquina'):
                    tipos = maquina.estadomaquina.tipos_maquina.all()
                    maquina_info['tipos'] = [{
                        'id': tipo.id,
                        'codigo': tipo.codigo,
                    } for tipo in tipos]

                    # Obtener procesos asociados a los tipos
                    if tipos:
                        procesos = Proceso.objects.filter(
                            tipos_maquina_compatibles__in=tipos
                        ).distinct()
                        maquina_info['procesos'] = [{
                            'id': proceso.id,
                            'codigo': proceso.codigo_proceso,
                            'descripcion': proceso.descripcion
                        } for proceso in procesos]

                # Obtener órdenes de trabajo asociadas
                ots = OrdenTrabajo.objects.filter(
                    ruta_ot__items__maquina=maquina
                ).distinct()
                maquina_info['ordenes_trabajo'] = [{
                    'codigo_ot': ot.codigo_ot,
                    'situacion': ot.situacion_ot.descripcion,
                    'descripcion': ot.descripcion_producto_ot
                } for ot in ots]

                # Clasificar la máquina según su estado
                if not maquina_info['tipos']:
                    diagnostico['maquinas_sin_tipo'].append(maquina_info)
                elif not maquina_info['procesos']:
                    diagnostico['maquinas_sin_procesos'].append(maquina_info)
                else:
                    diagnostico['maquinas_con_procesos'].append(maquina_info)

                if maquina_info['ordenes_trabajo']:
                    diagnostico['maquinas_en_ot'].append(maquina_info)

            return Response(diagnostico)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, pk):
        try:
            # Obtener o crear el estado de la máquina
            maquina = get_object_or_404(Maquina, pk=pk)
            estado_maquina, created = EstadoMaquina.objects.get_or_create(
                maquina=maquina,
                defaults={
                    'estado_operatividad': EstadoOperatividad.objects.get_or_create(
                        estado='OP',
                        defaults={'descripcion': 'Operativa'}
                    )[0]
                }
            )

            # Obtener los tipos de máquina
            tipos_maquina_ids = request.data.get('tipos_maquina_ids', [])
            
            if tipos_maquina_ids:
                # Actualizar los tipos de máquina
                estado_maquina.tipos_maquina.set(tipos_maquina_ids)
                
                return Response({
                    'message': 'Tipos de máquina actualizados correctamente',
                    'tipos_maquina': list(estado_maquina.tipos_maquina.values('id', 'codigo', 'descripcion'))
                })
            else:
                return Response(
                    {'error': 'tipos_maquina_ids es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        



class OperatorMachinesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, operator_id):
        try:
            # Obtener las máquinas del operador específico
            maquinas = Maquina.objects.filter(
                operadores_habilitados__id=operator_id
            ).select_related(
                'estadomaquina',
                'estadomaquina__estado_operatividad'
            ).prefetch_related(
                'estadomaquina__tipos_maquina'
            )

            data = []
            for maquina in maquinas:
                maquina_data = {
                    'id': maquina.id,
                    'codigo_maquina': maquina.codigo_maquina,
                    'descripcion': maquina.descripcion,
                    'tipos_maquina': [
                        {
                            'codigo': tipo.codigo,
                            'descripcion': tipo.descripcion
                        }
                        for tipo in maquina.estadomaquina.tipos_maquina.all()
                    ] if hasattr(maquina, 'estadomaquina') else [],
                    'estado_operatividad': (
                        maquina.estadomaquina.estado_operatividad.get_estado_display()
                        if hasattr(maquina, 'estadomaquina') and maquina.estadomaquina.estado_operatividad
                        else 'No especificado'
                    )
                }
                data.append(maquina_data)
            
            return Response(data)
        except Exception as e:
            print(f"Error en OperatorMachinesView: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class OperatorFormMachinesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Obtener todas las máquinas con sus relaciones
            maquinas = Maquina.objects.select_related(
                'estadomaquina',
                'estadomaquina__estado_operatividad'
            ).prefetch_related(
                'estadomaquina__tipos_maquina'
            ).all()

            data = []
            for maquina in maquinas:
                maquina_data = {
                    'id': maquina.id,
                    'codigo_maquina': maquina.codigo_maquina,
                    'descripcion': maquina.descripcion,
                    'tipos_maquina': [
                        {
                            'id': tipo.id,
                            'codigo': tipo.codigo,
                            'descripcion': tipo.descripcion
                        }
                        for tipo in maquina.estadomaquina.tipos_maquina.all()
                    ] if hasattr(maquina, 'estadomaquina') else [],
                    'estado_operatividad': {
                        'estado': maquina.estadomaquina.estado_operatividad.estado,
                        'descripcion': maquina.estadomaquina.estado_operatividad.get_estado_display()
                    } if hasattr(maquina, 'estadomaquina') and maquina.estadomaquina.estado_operatividad else None
                }
                data.append(maquina_data)
            
            return Response(data)
        except Exception as e:
            print(f"Error en OperatorFormMachinesView: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )