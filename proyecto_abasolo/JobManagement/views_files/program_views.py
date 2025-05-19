from django.db import transaction
from django.utils.dateparse import parse_date
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, time, timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, generics

from ..models import (
    ProgramaProduccion, 
    ProgramaOrdenTrabajo, 
    OrdenTrabajo, 
    Maquina,
    ItemRuta,
    TareaFragmentada,
    EmpresaOT,
    ReporteDiarioPrograma
)
from Operator.models import AsignacionOperador
from ..serializers import ProgramaProduccionSerializer, EmpresaOTSerializer
from ..services.time_calculations import TimeCalculator
from ..services.production_scheduler import ProductionScheduler
from ..services.machine_availability import MachineAvailabilityService

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, A3, A2, A1
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

import traceback, logging, os


class ProgramListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = ProgramaProduccion.objects.all()
    serializer_class = ProgramaProduccionSerializer

    def delete(self, request, pk):
        try:
            print(f"Intentando eliminar el programa con ID: {pk}")
            programa = ProgramaProduccion.objects.get(id=pk)
            ordenes_asociadas = ProgramaOrdenTrabajo.objects.filter(programa=programa)

            if ordenes_asociadas.exists():
                ordenes_asociadas.delete()
                print(f"Ordenes de trabajo asociadas eliminadas para programa {pk}")
            
            programa.delete()
            print(f"Programa {pk} eliminado exitósamente.")
            return Response({
                "message": "Programa eliminado correctamente"
            }, status=status.HTTP_200_OK)
        
        except ProgramaProduccion.DoesNotExist:
            print(f"Programa {pk} no encontrado")
            return Response({
                "error": "Programa no encontrado"
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            print(f"Error al eliminar el programa {pk}: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"Error al eliminar el programa: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
      
class ProgramCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        data = request.data
        
        # Validar datos requeridos (mantenemos validación existente)
        if 'fecha_inicio' not in data:
            return Response(
                {"detail": "Fecha de inicio es requerida."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificación inicial de OTs (mantenemos código existente)
        for ot_id in data.get('ordenes', []):
            print(f"Verificando OT con ID: {ot_id}")
            try:
                orden_trabajo = OrdenTrabajo.objects.select_related(
                    'ruta_ot',
                    'situacion_ot'
                ).prefetch_related(
                    'ruta_ot__items',
                    'ruta_ot__items__proceso',
                    'ruta_ot__items__maquina'
                ).get(id=ot_id)
                print(f"OT encontrada: {orden_trabajo.id} - {orden_trabajo.codigo_ot}")
            except OrdenTrabajo.DoesNotExist:
                print(f"OT con Id {ot_id} no encontrada")
                raise NotFound(f"Orden de trabajo con ID {ot_id} no encontrada.")
        
        try:
            with transaction.atomic():
                # Crear ProgramaProduccion (mantenemos código existente)
                fecha_inicio = parse_date(data.get('fecha_inicio'))
                if not fecha_inicio:
                    return Response(
                        {"detail": "Fecha de inicio no válida"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                programa = ProgramaProduccion.objects.create(
                    nombre=data.get('nombre'),
                    fecha_inicio=fecha_inicio
                )
                print("Programa creado:", programa.id)

                # Lista para almacenar datos para el scheduler
                ordenes_trabajo_scheduler = []
                
                # Crear relaciones ProgramaOrdenTrabajo (mantenemos código existente y añadimos preparación para scheduler)
                for index, ot_id in enumerate(data.get('ordenes', [])):
                    try:
                        orden_trabajo = OrdenTrabajo.objects.get(id=ot_id)
                        
                        # Crear la relación ProgramaOrdenTrabajo (existente)
                        pot = ProgramaOrdenTrabajo.objects.create(
                            programa=programa,
                            orden_trabajo=orden_trabajo,
                            prioridad=index  # Usamos index como prioridad
                        )
                        print(f"Relación creada: {pot}")

                        # NUEVO: Preparar datos para el scheduler
                        if orden_trabajo.ruta_ot:
                            ot_data = {
                                'orden_trabajo': orden_trabajo.id,
                                'orden_trabajo_codigo_ot': orden_trabajo.codigo_ot,
                                'orden_trabajo_descripcion_producto_ot': orden_trabajo.descripcion_producto_ot,
                                'procesos': []
                            }
                            
                            for item in orden_trabajo.ruta_ot.items.all().order_by('item'):
                                proceso_data = {
                                    'id': item.id,
                                    'item': item.item,
                                    'descripcion': item.proceso.descripcion if item.proceso else None,
                                    'maquina_id': item.maquina.id if item.maquina else None,
                                    'cantidad': item.cantidad_pedido,
                                    'estandar': item.estandar,
                                    'prioridad': pot.prioridad
                                }
                                ot_data['procesos'].append(proceso_data)
                            
                            ordenes_trabajo_scheduler.append(ot_data)
                            print(f"Datos preparados para scheduler - OT: {orden_trabajo.codigo_ot}")

                    except OrdenTrabajo.DoesNotExist:
                        raise NotFound(f"Orden de trabajo con ID {ot_id} no encontrada.")
                    except Exception as e:
                        print(f"Error procesando OT {ot_id}: {str(e)}")
                        raise

                # NUEVO: Crear tareas fragmentadas
                try:
                    scheduler = ProductionScheduler(TimeCalculator())
                    print("Iniciando creación de tareas fragmentadas...")
                    
                    if not scheduler.create_fragmented_tasks(programa, ordenes_trabajo_scheduler):
                        print("Error en create_fragmented_tasks")
                        # No lanzamos excepción, solo registramos el error
                    else:
                        print("Tareas fragmentadas creadas exitosamente")

                    # Intentar calcular fecha fin con el scheduler
                    try:
                        fecha_fin = scheduler.calculate_program_end_date(programa, ordenes_trabajo_scheduler)
                        if fecha_fin:
                            programa.fecha_fin = fecha_fin
                            print(f"Nueva fecha fin calculada: {fecha_fin}")
                        else:
                            programa.fecha_fin = programa.fecha_inicio
                            print("Usando fecha inicio como fecha fin (fallback)")
                    except Exception as e:
                        print(f"Error calculando fecha fin: {str(e)}")
                        programa.fecha_fin = programa.fecha_inicio
                        print("Usando fecha inicio como fecha fin (error)")

                except Exception as e:
                    print(f"Error en operaciones del scheduler: {str(e)}")
                    programa.fecha_fin = programa.fecha_inicio
                    print("Usando fecha inicio como fecha fin (error en scheduler)")

                # Guardar fecha fin (mantenemos código existente)
                programa.save(update_fields=['fecha_fin'])
                print(f"Programa guardado con fecha fin: {programa.fecha_fin}")

                # Serializar y devolver respuesta (mantenemos código existente)
                serializer = ProgramaProduccionSerializer(programa)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            print(f"Error creando programa: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"detail": "Ha ocurrido un error en el servidor.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update_ruta_ot_items(self, ruta_ot, items_data):
        for item_data in items_data:
            try:
                item = ruta_ot.items.get(item=item_data['item'])
                if 'maquina' in item_data:
                    item.maquina = Maquina.objects.get(id=item_data['maquina'])
                if 'estandar' in item_data:
                    item.estandar = item_data['estandar']
                item.save()
            except Exception as e:
                print("Error updating ItemRuta:", e)

    # En ProgramCreateView
    def verificar_creacion_programa(self, programa_id):
        """Verifica que todos los elementos necesarios se hayan creado"""
        try:
            programa = ProgramaProduccion.objects.get(id=programa_id)
            
            # Verificar TareaFragmentada
            tareas = TareaFragmentada.objects.filter(programa=programa).count()
            print(f"Tareas fragmentadas creadas: {tareas}")
            
            # Verificar ReporteDiarioPrograma
            reportes = ReporteDiarioPrograma.objects.filter(programa=programa).count()
            print(f"Reportes diarios creados: {reportes}")
            
            return {
                'tareas_fragmentadas': tareas,
                'reportes_diarios': reportes
            }
        except Exception as e:
            print(f"Error en verificación: {str(e)}")
            return None

class ProgramDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.time_calculator = TimeCalculator()
        self.production_scheduler = ProductionScheduler(self.time_calculator)
        self.machine_availability = MachineAvailabilityService()

    def get_procesos_con_asignaciones(self, programa_id):
        """Obtiene los procesos y sus asignaciones de operadores para un programa específico"""
        try:
            asignaciones = AsignacionOperador.objects.filter(
                programa_id=programa_id
            ).select_related(
                'operador',
                'item_ruta',
                'item_ruta__proceso',
                'item_ruta__maquina'
            )
            return {
                asignacion.item_ruta_id: {
                    'operador_id': asignacion.operador.id,
                    'operador_nombre': asignacion.operador.nombre,
                    'fecha_inicio': asignacion.fecha_inicio,
                    'fecha_fin': asignacion.fecha_fin,
                } for asignacion in asignaciones
            }
        
        except Exception as e:
            print(f"Error obteniendo asignaciones: {str(e)}")
            return {}
        
    def get(self, request, pk):
        try:
            print(f"[Backend] Iniciando obtención de programa {pk}")
            self.programa_id = pk
            programa = ProgramaProduccion.objects.get(id=pk)
            print(f"[Backend] Programa encontrado: {programa.nombre}")

            try:
                #Usar el production_scheduler para calcular la fecha fin
                print(f"[Backend] Calculando fecha fin para programa {pk}")
                fecha_fin = self.production_scheduler.calculate_program_end_date(programa)
                print(f"[Backend] Fecha fin calculada: {fecha_fin}")
                
                if fecha_fin != programa.fecha_fin:
                    programa.fecha_fin = fecha_fin
                    programa.save(update_fields=['fecha_fin'])
                    programa.refresh_from_db()
            except Exception as e:
                print(f"[Backend] Error calculando fecha fin: {str(e)}")
                # No dejar que este error detenga toda la vista
                fecha_fin = programa.fecha_inicio

            print(f"[Backend] Serializando programa {pk}")
            serializer = ProgramaProduccionSerializer(programa)
            
            print(f"[Backend] Obteniendo asignaciones para programa {pk}")
            asignaciones_por_item = self.get_procesos_con_asignaciones(pk)
            
            print(f"[Backend] Obteniendo órdenes de trabajo para programa {pk}")
            ordenes_trabajo = self.get_ordenes_trabajo(programa)

            for ot in ordenes_trabajo:
                for proceso in ot['procesos']:
                    if proceso['id'] in asignaciones_por_item:
                        proceso['asignacion'] = asignaciones_por_item[proceso['id']]

            try:
                print(f"[Backend] Generando timeline para programa {pk}")
                routes_data = self.production_scheduler.generate_timeline_data(programa, ordenes_trabajo)
                print(f"[Backend] Timeline generado exitosamente")
            except Exception as e:
                print(f"[Backend] Error generando timeline: {str(e)}")
                # No dejar que este error detenga toda la vista
                routes_data = {"groups": [], "items": []}

            response_data = {
                "program": serializer.data,
                "ordenes_trabajo": ordenes_trabajo,
                "routes_data": routes_data
            }

            print(f"[Backend] Enviando respuesta para programa {pk}")
            return Response(response_data, status=status.HTTP_200_OK)
        
        except ProgramaProduccion.DoesNotExist:
            print(f"[Backend] Programa {pk} no encontrado")
            return Response(
                {'error': 'Programa no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            print(f"[Backend] Error general obteniendo programa {pk}: {str(e)}")
            return Response(
                {'error': f'Error interno del servidor: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def get_ordenes_trabajo(self, programa):
        """Obtiene las órdenes de trabajo del programa dado."""
        try:
            program_ots = ProgramaOrdenTrabajo.objects.filter(
                programa=programa
            ).select_related(
                'orden_trabajo',
                'orden_trabajo__ruta_ot',
            ).prefetch_related(
                'orden_trabajo__ruta_ot__items',
                'orden_trabajo__ruta_ot__items__proceso',
                'orden_trabajo__ruta_ot__items__maquina',
            ).order_by('prioridad')

            ordenes_trabajo = []

            for prog_ot in program_ots:
                ot_data = self.format_orden_trabajo(prog_ot.orden_trabajo, programa.id)
                if ot_data:
                    ordenes_trabajo.append(ot_data)
            return ordenes_trabajo
        except Exception as e:
            print(f'Error obteniendo órdenes de trabajo: {str(e)}')
            return []
        
    def format_orden_trabajo(self, orden_trabajo, programa_id=None):
        """Formatea una orden de trabajo para la respuesta de la API"""
        try:
            programa_id = programa_id or getattr(self, 'programa_id', None)

            if not programa_id:
                print(f"Advertencia: No se proporcionó programa_id para la orden {orden_trabajo.id}")

            ot_data = {
                'orden_trabajo': orden_trabajo.id,
                'orden_trabajo_codigo_ot': orden_trabajo.codigo_ot,
                'orden_trabajo_descripcion_producto_ot': orden_trabajo.descripcion_producto_ot,
                'procesos': []
            }
            ruta = getattr(orden_trabajo, 'ruta_ot', None)
            if ruta:
                for item in ruta.items.all().order_by('item'):
                    asignacion = None
                    if programa_id:
                        asignacion = AsignacionOperador.objects.filter(
                            programa_id=programa_id,
                            item_ruta_id=item.id
                        ).first()

                    operador_id = None
                    operador_nombre = None
                    asignacion_data = None
                    
                    if asignacion:
                        operador_id = asignacion.operador.id
                        operador_nombre = asignacion.operador.nombre
                        asignacion_data = {
                            'id': asignacion.id,
                            'fecha_asignacion': asignacion.created_at.isoformat() if asignacion.created_at else None
                        }

                    proceso_data = {
                        'id': item.id,
                        'item': item.item,
                        'codigo_proceso': item.proceso.codigo_proceso if item.proceso else None, 
                        'descripcion': item.proceso.descripcion if item.proceso else None,
                        'maquina_id': item.maquina.id if item.maquina else None,
                        'maquina_descripcion': item.maquina.descripcion if item.maquina else None,
                        'cantidad': item.cantidad_pedido,
                        'estandar': item.estandar,
                        'operador_id': operador_id,
                        'operador_nombre': operador_nombre,
                        'asignacion': asignacion_data
                    }
                    ot_data['procesos'].append(proceso_data)

                return ot_data
        except Exception as e:
            print(f"Error formateando orden de trabajo {orden_trabajo.id}: {str(e)}")
            return None
        
    def put(self, request, pk):
        try:
            programa = get_object_or_404(ProgramaProduccion, id=pk)
            print(f"Actualizando programa {pk}")
            print(f"Datos recibidos: {request.data}")

            with transaction.atomic():
                # Manejar tanto el formato 'ordenes' como 'order_ids'
                ordenes_data = request.data.get('ordenes', request.data.get('order_ids', []))
                
                for orden_data in ordenes_data:
                    # Manejar ambos formatos de ID de orden
                    orden_id = orden_data.get('orden_trabajo', orden_data.get('id'))
                    print(f"Procesando orden: {orden_id}")
                    
                    try:
                        programa_ot = ProgramaOrdenTrabajo.objects.get(
                            programa=programa,
                            orden_trabajo_id=orden_id
                        )
                        
                        # Manejar ambos formatos de prioridad
                        prioridad = orden_data.get('prioridad', orden_data.get('priority'))
                        if prioridad is not None:
                            programa_ot.prioridad = prioridad
                            programa_ot.save()
                            print(f"Prioridad actualizada para OT {orden_id} a {prioridad}")

                        if 'procesos' in orden_data:
                            for proceso in orden_data['procesos']:
                                print(f"Procesando proceso: {proceso}")
                                try:
                                    item_ruta = ItemRuta.objects.get(id=proceso['id'])
                                    print(f"ItemRuta encontrado: {item_ruta}")
                                    cambios = False

                                    if 'maquina_id' in proceso and proceso['maquina_id']:
                                        maquina = get_object_or_404(Maquina, id=proceso['maquina_id'])
                                        item_ruta.maquina = maquina
                                        cambios = True
                                        print(f"Máquina actualizada a: {maquina}")

                                    if 'estandar' in proceso:
                                        try:
                                            nuevo_estandar = int(proceso['estandar'])
                                            if nuevo_estandar >= 0:
                                                item_ruta.estandar = nuevo_estandar
                                                cambios = True
                                                print(f"Estándar actualizado a: {nuevo_estandar}")
                                            else:
                                                print(f"Valor de estándar inválido: {nuevo_estandar}")
                                        except (ValueError, TypeError) as e:
                                            print(f"Error al convertir estándar: {e}")
                                            continue

                                    if cambios:
                                        item_ruta.save()
                                        print(f"ItemRuta {item_ruta.id} guardado con éxito")

                                except ItemRuta.DoesNotExist:
                                    print(f"No se encontró ItemRuta con id {proceso['id']}")
                                except Exception as e:
                                    print(f"Error procesando proceso: {str(e)}")
                                    raise

                    except ProgramaOrdenTrabajo.DoesNotExist:
                        print(f"No se encontró ProgramaOrdenTrabajo para orden {orden_id}")
                    except Exception as e:
                        print(f"Error procesando orden {orden_id}: {str(e)}")
                        raise

                # Recalcular fechas si se solicita
                if request.data.get('recalculate_dates', True):
                    fecha_fin = self.production_scheduler.calculate_program_end_date(programa)
                    programa.fecha_fin = fecha_fin
                    programa.save()
                    print(f"Fecha fin actualizada a: {fecha_fin}")

                return Response({
                    "message": "Programa actualizado correctamente",
                    "fecha_fin": programa.fecha_fin
                }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error general: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"Error al actualizar el programa: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def verificar_estado_produccion(self, programa_id):
        """Verifica el estado actual de la producción y detecta retrasos"""
        programa = get_object_or_404(ProgramaProduccion, id=programa_id)
        tareas_retrasadas = []
        
        for prog_ot in programa.programaordentrabajo_set.all():
            for item_ruta in prog_ot.orden_trabajo.ruta_ot.items.all():
                asignacion = AsignacionOperador.objects.filter(
                    programa=programa,
                    item_ruta=item_ruta
                ).first()
                
                if asignacion:
                    tiempo_transcurrido = timezone.now() - asignacion.fecha_inicio
                    tiempo_total = asignacion.fecha_fin - asignacion.fecha_inicio
                    progreso_esperado = (tiempo_transcurrido / tiempo_total) * 100
                    
                    if progreso_esperado > item_ruta.porcentaje_cumplimiento + 20:
                        tareas_retrasadas.append({
                            'ot_codigo': item_ruta.ruta.orden_trabajo.codigo_ot,
                            'proceso': item_ruta.proceso.descripcion,
                            'retraso': progreso_esperado - item_ruta.porcentaje_cumplimiento,
                            'operador': asignacion.operador.nombre if asignacion.operador else 'Sin asignar'
                        })
        
        return tareas_retrasadas

    def identificar_cuellos_botella(self, programa):
        """Identifica cuellos de botella en la producción"""
        cuellos_botella = []
        maquinas_usadas = Maquina.objects.filter(
            itemruta__ruta__orden_trabajo__programaordentrabajo__programa=programa
        ).distinct()

        for maquina in maquinas_usadas:
            carga = self.machine_availability.calcular_carga_maquina(maquina, programa)
            
            # Consideramos cuello de botella si la carga supera 8 horas
            if carga['carga_total'] > 8:
                cuellos_botella.append({
                    'maquina_codigo': maquina.codigo_maquina,
                    'maquina_descripcion': maquina.descripcion,
                    'tiempo_total': carga['carga_total'],
                    'tareas_afectadas': carga['desglose']
                })

        return cuellos_botella

    def post(self, request, pk):
        """Endpoint para verificar estado y problemas"""
        try:
            programa = get_object_or_404(ProgramaProduccion, id=pk)
            
            tareas_retrasadas = self.verificar_estado_produccion(pk)
            cuellos_botella = self.identificar_cuellos_botella(programa)
            
            return Response({
                'estado': 'actualizado',
                'tareas_retrasadas': len(tareas_retrasadas),
                'tareas_retrasadas_detalle': tareas_retrasadas,
                'cuellos_botella': len(cuellos_botella),
                'cuellos_botella_detalle': cuellos_botella,
                'acciones_tomadas': []  # Por ahora no hay acciones automáticas
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Error al verificar estado: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 2. Métodos de acción correctiva
    def aplicar_acciones_correctivas(self, tarea_retrasada):
        """
        Implementa acciones correctivas para tareas retrasadas
        """
        item_ruta = tarea_retrasada['item_ruta']
        asignacion = tarea_retrasada['asignacion']
        retraso = tarea_retrasada['retraso']
        
        acciones_tomadas = []

        # 1. Ajustar estimaciones
        if retraso > 30:  # Si el retraso es mayor al 30%
            nuevo_estandar = self.calcular_nuevo_estandar(item_ruta)
            item_ruta.estandar = nuevo_estandar
            item_ruta.save()
            acciones_tomadas.append(f"Estándar ajustado a {nuevo_estandar}")

        # 2. Buscar recursos alternativos
        if retraso > 40:
            recursos_alt = self.buscar_recursos_disponibles(item_ruta)
            if recursos_alt:
                self.reasignar_recursos(item_ruta, recursos_alt)
                acciones_tomadas.append("Recursos reasignados")

        # 3. Fragmentar tarea si es necesario
        if retraso > 50:
            self.fragmentar_tarea(item_ruta, asignacion)
            acciones_tomadas.append("Tarea fragmentada")

        return acciones_tomadas


class EmpresaListView(APIView):
    def get(self, request):
        empresas = EmpresaOT.objects.all()
        serializer = EmpresaOTSerializer(empresas, many=True)
        return Response(serializer.data)
    
logger = logging.getLogger(__name__)
class GenerateProgramPDF(APIView):
    def __init__(self):
        super().__init__()
        # Inicializar el time calculator y el scheduler
        self.time_calculator = TimeCalculator()
        self.production_scheduler = ProductionScheduler(self.time_calculator)

    def get_ordenes_trabajo(self, programa):
        """Obtiene las órdenes de trabajo del programa dado."""
        try:
            program_ots = ProgramaOrdenTrabajo.objects.filter(
                programa=programa
            ).select_related(
                'orden_trabajo',
                'orden_trabajo__ruta_ot',
            ).prefetch_related(
                'orden_trabajo__ruta_ot__items',
                'orden_trabajo__ruta_ot__items__proceso',
                'orden_trabajo__ruta_ot__items__maquina',
            ).order_by('prioridad')

            ordenes_trabajo = []
            for prog_ot in program_ots:
                ot = prog_ot.orden_trabajo
                ot_data = {
                    'orden_trabajo_codigo_ot': ot.codigo_ot,
                    'orden_trabajo_descripcion_producto_ot': ot.descripcion_producto_ot,
                    'procesos': []
                }
    
                ruta = getattr(ot, 'ruta_ot', None)
                if ruta:
                    for item in ruta.items.all().order_by('item'):
                        #Obtener asignación de operador si existe
                        asignacion = AsignacionOperador.objects.filter(
                            programa=programa,
                            item_ruta=item
                        ).first()

                        #Obtener fechas de inicio y fin del proceso
                        fechas_proceso = self.get_fechas_procesos(programa, item)

                        proceso_data = {
                            'item': item.item,
                            'codigo_proceso': item.proceso.codigo_proceso if item.proceso else None,
                            'descripcion': item.proceso.descripcion if item.proceso else None,
                            'maquina_codigo': item.maquina.codigo_maquina if item.maquina else None,
                            'maquina_descripcion': item.maquina.descripcion if item.maquina else None,
                            'operador_nombre': asignacion.operador.nombre if asignacion and asignacion.operador else 'No asignado',
                            'cantidad': item.cantidad_pedido,
                            'estandar': item.estandar,
                            'fecha_inicio': fechas_proceso.get('fecha_inicio'),
                            'fecha_fin': fechas_proceso.get('fecha_fin')
                        }
                        ot_data['procesos'].append(proceso_data)
                
                ordenes_trabajo.append(ot_data)
            return ordenes_trabajo
        except Exception as e:
            logger.error(f'Error obteniendo órdenes de trabajo: {str(e)}')
            logger.error(traceback.format_exc())
            raise

    def get_fechas_procesos(self, programa, item_ruta):
        """Obtiene las fechas de inicio y fin para un proceso específico."""
        try:
            # Intentar obtener fechas de asignación primero
            asignacion = AsignacionOperador.objects.filter(
                programa=programa,
                item_ruta=item_ruta
            ).first()

            if asignacion and asignacion.fecha_inicio and asignacion.fecha_fin:
                return {
                    'fecha_inicio': asignacion.fecha_inicio,
                    'fecha_fin': asignacion.fecha_fin
                }

            # Si no hay asignación, obtener todas las OTs del programa
            program_ots = ProgramaOrdenTrabajo.objects.filter(
                programa=programa
            ).select_related(
                'orden_trabajo',
                'orden_trabajo__ruta_ot'
            ).prefetch_related(
                'orden_trabajo__ruta_ot__items'
            ).order_by('prioridad')

            # Preparar datos para el scheduler
            ordenes_trabajo = []
            for prog_ot in program_ots:
                ot = prog_ot.orden_trabajo
                ot_data = {
                    'orden_trabajo': ot.id,
                    'orden_trabajo_codigo_ot': ot.codigo_ot,
                    'orden_trabajo_descripcion_producto_ot': ot.descripcion_producto_ot,
                    'procesos': []
                }

                if ot.ruta_ot:
                    for item in ot.ruta_ot.items.all().order_by('item'):
                        proceso_data = {
                            'id': item.id,
                            'item': item.item,
                            'descripcion': item.proceso.descripcion if item.proceso else None,
                            'maquina_id': item.maquina.id if item.maquina else None,
                            'maquina_descripcion': item.maquina.descripcion if item.maquina else None,
                            'cantidad': item.cantidad_pedido,
                            'estandar': item.estandar,
                            'prioridad': prog_ot.prioridad
                        }
                        ot_data['procesos'].append(proceso_data)
            
                ordenes_trabajo.append(ot_data)

            # Generar timeline data para todas las OTs
            timeline_data = self.production_scheduler.generate_timeline_data(programa, ordenes_trabajo)

            # Buscar el proceso específico en el timeline completo
            if timeline_data.get('items'):
                proceso_items = [
                    item for item in timeline_data['items'] 
                    if item['proceso_id'] == f"proc_{item_ruta.id}"
                ]

                if proceso_items:
                    # Ordenar items por fecha
                    proceso_items.sort(key=lambda x: datetime.strptime(x['start_time'], '%Y-%m-%d %H:%M:%S'))
                    
                    fecha_inicio = datetime.strptime(proceso_items[0]['start_time'], '%Y-%m-%d %H:%M:%S')
                    
                    # Calcular la fecha fin real basada en la cantidad total y los intervalos
                    cantidad_total = float(item_ruta.cantidad_pedido)
                    cantidad_acumulada = 0
                    fecha_fin = None
                    
                    for item in proceso_items:
                        cantidad_acumulada += float(item['cantidad_intervalo'])
                        fecha_fin = datetime.strptime(item['end_time'], '%Y-%m-%d %H:%M:%S')
                        
                        # Si ya procesamos toda la cantidad, esta es la fecha fin real
                        if cantidad_acumulada >= cantidad_total:
                            break

                    if fecha_fin:
                        return {
                            'fecha_inicio': fecha_inicio,
                            'fecha_fin': fecha_fin
                        }

            return {
                'fecha_inicio': None,
                'fecha_fin': None,
                'error': 'No se pudieron calcular las fechas del proceso'
            }

        except Exception as e:
            logger.error(f'Error obteniendo fechas de proceso: {str(e)}')
            logger.error(traceback.format_exc())
            return {
                'fecha_inicio': None,
                'fecha_fin': None,
                'error': str(e)
            }

    def get(self, request, pk):
        try:
            logger.info(f"Iniciando generación de PDF para programa {pk}")

            # Obtener el programa
            programa = get_object_or_404(ProgramaProduccion, pk=pk)
            logger.info(f"Programa encontrado: {programa.nombre}")

            # Obtener datos necesarios para el PDF
            try:
                ordenes_trabajo = self.get_ordenes_trabajo(programa)
                logger.info(f"Órdenes de trabajo obtenidas: {len(ordenes_trabajo)}")
            except Exception as e:
                logger.error(f"Error al obtener órdenes de trabajo: {str(e)}")
                logger.error(traceback.format_exc())
                return Response(
                    {"detail": f'Error al obtener datos de órdenes de trabajo: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Verificar si hay datos para generar el PDF
            if not ordenes_trabajo:
                logger.warning(f"No hay órdenes de trabajo en el programa {pk}")
                return Response(
                    {"detail": "No hay órdenes de trabajo en este programa para generar el PDF"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generar el PDF
            try:
                logger.info("Generando PDF...")

                # Crear directorio temporal si no existe
                temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                    logger.info(f"Directorio temporal creado: {temp_dir}")

                # Generar nombre de archivo único
                import uuid
                pdf_filename = f"programa_{pk}_{uuid.uuid4().hex[:8]}.pdf"
                pdf_path = os.path.join(temp_dir, pdf_filename)
                logger.info(f"Ruta del PDF: {pdf_path}")

                # Crear el documento con orientación horizontal
                doc = SimpleDocTemplate(
                    pdf_path, 
                    pagesize=landscape(letter),
                    rightMargin=20,
                    leftMargin=20,
                    topMargin=30,
                    bottomMargin=30
                )
                elements = []

                # Estilos 
                styles = getSampleStyleSheet()
                title_style = styles['Heading1']
                subtitle_style = styles['Heading2']
                normal_style = styles['Normal']
                
                # Estilo para texto en celdas
                cell_style = ParagraphStyle(
                    'CellStyle',
                    parent=normal_style,
                    fontSize=8,
                    leading=9,
                    wordWrap='CJK',
                    alignment=0  # 0=left
                )
                
                # Estilo para texto centrado en celdas
                cell_style_center = ParagraphStyle(
                    'CellStyleCenter',
                    parent=cell_style,
                    alignment=1  # 1=center
                )

                # Estilo personalizado para títulos centrados
                centered_title = ParagraphStyle(
                    'CenteredTitle',
                    parent=title_style,
                    alignment=1,  # 0=left, 1=center, 2=right
                    spaceAfter=10
                )

                # Título 
                elements.append(Paragraph(f"Programa de Producción: {programa.nombre}", centered_title))
                elements.append(Paragraph(f"Fecha Inicio: {programa.fecha_inicio.strftime('%d/%m/%Y')} - Fecha Fin: {programa.fecha_fin.strftime('%d/%m/%Y') if programa.fecha_fin else 'No definida'}", centered_title))
                elements.append(Spacer(1, 10))

                # Crear una única tabla para todo el programa
                data = []
                
                # Encabezados de la tabla - usar Paragraph para permitir ajuste de texto
                headers = [
                    Paragraph('<b>OT</b>', cell_style_center),
                    Paragraph('<b>Item</b>', cell_style_center),
                    Paragraph('<b>Proceso</b>', cell_style_center),
                    Paragraph('<b>Máquina</b>', cell_style_center),
                    Paragraph('<b>Operador</b>', cell_style_center),
                    Paragraph('<b>Cantidad</b>', cell_style_center),
                    Paragraph('<b>Estándar</b>', cell_style_center),
                    Paragraph('<b>Fecha Inicio</b>', cell_style_center),
                    Paragraph('<b>Fecha Fin</b>', cell_style_center)
                ]
                data.append(headers)
                
                # Procesar cada orden de trabajo
                for ot in ordenes_trabajo:
                    # Agregar fila con información de la OT
                    ot_row = [
                        Paragraph(f"{ot['orden_trabajo_codigo_ot']}", cell_style_center),
                        "",
                        Paragraph(f"{ot['orden_trabajo_descripcion_producto_ot']}", cell_style),
                        "", "", "", "", "", ""
                    ]
                    data.append(ot_row)
                    
                    # Agregar procesos
                    for proceso in ot.get('procesos', []):
                        # Formatear fechas
                        fecha_inicio_str = proceso.get('fecha_inicio').strftime('%d/%m/%Y %H:%M') if proceso.get('fecha_inicio') else 'No definida'
                        fecha_fin_str = proceso.get('fecha_fin').strftime('%d/%m/%Y %H:%M') if proceso.get('fecha_fin') else 'No definida'
                        
                        # Crear fila con Paragraphs para permitir ajuste de texto
                        proceso_row = [
                            "",  # OT ya incluido en la fila anterior
                            Paragraph(str(proceso.get('item', '')), cell_style_center),
                            Paragraph(f"{proceso.get('codigo_proceso', '')} - {proceso.get('descripcion', '')}", cell_style),
                            Paragraph(f"{proceso.get('maquina_codigo', 'No asignada')} - {proceso.get('maquina_descripcion', '')}", cell_style),
                            Paragraph(proceso.get('operador_nombre', 'No asignado'), cell_style),
                            Paragraph(str(proceso.get('cantidad', 0)), cell_style_center),
                            Paragraph(str(proceso.get('estandar', 0)), cell_style_center),
                            Paragraph(fecha_inicio_str, cell_style_center),
                            Paragraph(fecha_fin_str, cell_style_center)
                        ]
                        data.append(proceso_row)
                    
                    # NO agregar filas vacías entre órdenes de trabajo
                
                # Crear tabla con todos los datos - ajustar anchos de columna
                col_widths = [50, 30, 140, 140, 80, 40, 40, 60, 60]  # Ajustar según necesidades
                table = Table(data, colWidths=col_widths, repeatRows=1)
                
                # Aplicar estilos a la tabla
                style = TableStyle([
                    # Estilo para encabezados
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alineación vertical al centro
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    
                    # Bordes para todas las celdas
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    
                    # Alineación para columnas numéricas
                    ('ALIGN', (5, 1), (6, -1), 'CENTER'),  # CANTIDAD Y ESTÁNDAR
                    ('ALIGN', (7, 1), (8, -1), 'CENTER'),  # FECHAS
                    
                    # Ajustar el espacio interno de las celdas
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 3),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ])
                
                # Identificar filas de OT para aplicar estilos específicos
                ot_rows = []
                row_idx = 1  # Empezar después de los encabezados
                
                for ot in ordenes_trabajo:
                    ot_rows.append(row_idx)
                    row_idx += 1 + len(ot.get('procesos', []))  # OT + sus procesos (sin fila vacía)
                
                # Aplicar estilos a filas de OT
                for row in ot_rows:
                    style.add('BACKGROUND', (0, row), (-1, row), colors.lightgrey)
                    style.add('FONTNAME', (0, row), (-1, row), 'Helvetica-Bold')
                    style.add('SPAN', (2, row), (-1, row))  # Combinar celdas para descripción
                
                table.setStyle(style)
                elements.append(table)
                
                # Construir el PDF
                doc.build(elements)
                logger.info("PDF generado correctamente")
                
                # Verificar que el PDF se generó correctamente
                if not os.path.exists(pdf_path):
                    raise Exception("El archivo PDF no se creó correctamente")
                
                if os.path.getsize(pdf_path) == 0:
                    raise Exception("El archivo PDF está vacío")
                
                # Devolver el PDF
                with open(pdf_path, 'rb') as pdf:
                    response = HttpResponse(pdf.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="programa_{pk}.pdf"'
                    
                    # Eliminar el archivo temporal después de enviarlo
                    try:
                        os.remove(pdf_path)
                        logger.info(f'Archivo temporal eliminado: {pdf_path}')
                    except Exception as e:
                        logger.warning(f'No se pudo eliminar el archivo temporal: {str(e)}')
                    
                    return response
            
            except Exception as e:
                logger.error(f"Error al generar el PDF: {str(e)}")
                logger.error(traceback.format_exc())
                return Response(
                    {'detail': f'Error al generar el PDF: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        except Exception as e:
            logger.error(f"Error general en GenerateProgramPDF: {str(e)}")
            logger.error(traceback.format_exc())
            return Response(
                {"detail": f"Error al procesar la solicitud: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AddOrdersToProgram(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.time_calculator = TimeCalculator()
        self.production_scheduler = ProductionScheduler(self.time_calculator)

    def post(self, request, pk):
        try:
            programa = get_object_or_404(ProgramaProduccion, id=pk)
            ordenes_ids = request.data.get('ordenes', [])

            if not ordenes_ids:
                return Response({
                    "error": "No se proporcionaron órdenes para añadir"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # Obtener la última prioridad usada en el programa
                ultima_prioridad = ProgramaOrdenTrabajo.objects.filter(
                    programa=programa
                ).order_by('-prioridad').first()

                prioridad_inicial = (ultima_prioridad.prioridad + 1) if ultima_prioridad else 0

                ordenes_agregadas = []
                for idx, orden_id in enumerate(ordenes_ids):
                    try:
                        orden = OrdenTrabajo.objects.get(id=orden_id)

                        # Verificar si la orden ya está en el programa
                        if ProgramaOrdenTrabajo.objects.filter(
                            programa=programa,
                            orden_trabajo=orden
                        ).exists():
                            continue

                        # Crear nueva relación programa-orden
                        ProgramaOrdenTrabajo.objects.create(
                            programa=programa,
                            orden_trabajo=orden,
                            prioridad=prioridad_inicial + idx
                        )
                        ordenes_agregadas.append(orden.codigo_ot)

                    except OrdenTrabajo.DoesNotExist:
                        return Response({
                            "error": f"Orden de trabajo {orden_id} no encontrada"
                        }, status=status.HTTP_404_NOT_FOUND)
                    
                # Recalcular fechas del programa
                fecha_fin = self.production_scheduler.calculate_program_end_date(programa)
                programa.fecha_fin = fecha_fin
                programa.save()

                return Response({
                    "message": "Órdenes agregadas correctamente",
                    "ordenes_agregadas": ordenes_agregadas,
                    "fecha_fin": programa.fecha_fin
                }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": f"Error al agregar órdenes al programa: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ReajustarProgramaView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.machine_availability = MachineAvailabilityService()

    def post(self, request, pk):
        try:
            programa = get_object_or_404(ProgramaProduccion, id=pk)
            
            # Obtener ajustes necesarios
            ajustes = self.machine_availability.obtener_ajustes_necesarios(programa)
            
            if ajustes:
                return Response({
                    "requiere_ajustes": True,
                    "ajustes_sugeridos": [
                        {
                            "orden_trabajo": str(ajuste['orden_trabajo']),
                            "proceso": {
                                "id": ajuste['proceso'].id,
                                "descripcion": ajuste['proceso'].descripcion
                            },
                            "maquina": {
                                "id": ajuste['maquina'].id,
                                "codigo": ajuste['maquina'].codigo_maquina
                            },
                            "fecha_original": ajuste['fecha_original'].strftime("%Y-%m-%d %H:%M"),
                            "fecha_propuesta": ajuste['fecha_ajustada'].strftime("%Y-%m-%d %H:%M")
                        } for ajuste in ajustes
                    ],
                    "fecha_actual": programa.fecha_fin.strftime("%Y-%m-%d %H:%M") if programa.fecha_fin else None
                }, status=status.HTTP_200_OK)
            
            return Response({
                "requiere_ajustes": False,
                "mensaje": "El programa no requiere ajustes"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": f"Error al verificar ajustes del programa: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)