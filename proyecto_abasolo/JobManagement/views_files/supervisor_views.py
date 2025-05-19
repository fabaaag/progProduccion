from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status

from ..models import (
    ProgramaProduccion,
    TareaFragmentada,
    EjecucionTarea,
    ReporteDiarioPrograma,
    ProgramaOrdenTrabajo,
    ItemRuta
)
from ..serializers import (
    TareaFragmentadaSerializer,
    EjecucionTareaSerializer
)
from ..services.time_calculations import TimeCalculator
from ..services.production_scheduler import ProductionScheduler

class SupervisorReportView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            programa = get_object_or_404(ProgramaProduccion, id=pk)
            fecha_solicitada = request.GET.get('fecha')
            
            if not fecha_solicitada:
                # Obtener el primer día con tareas fragmentadas
                primera_tarea = TareaFragmentada.objects.filter(
                    programa=programa
                ).order_by('fecha').first()
                
                # Si no hay tareas, usar la primera fecha laboral desde el inicio del programa
                if primera_tarea:
                    fecha_solicitada = primera_tarea.fecha.strftime('%Y-%m-%d')
                else:
                    fecha_inicio = programa.fecha_inicio
                    while fecha_inicio.weekday() >= 5:  # 5=Sábado, 6=Domingo
                        fecha_inicio += timedelta(days=1)
                    fecha_solicitada = fecha_inicio.strftime('%Y-%m-%d')
            
            # Convertir a datetime para mantener consistencia
            fecha = datetime.strptime(fecha_solicitada + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
            print(f"Fecha solicitada (string): {fecha_solicitada}")
            print(f"Fecha parseada (objeto): {fecha}")
            print(f"Fecha.date() usada en filtro: {fecha.date()}")
            
            # Verificar si es día laboral (Lunes-Viernes)
            es_dia_laboral = fecha.weekday() < 5
            
            # Verificar si hay tareas para esta fecha específica
            count_tareas = TareaFragmentada.objects.filter(
                programa=programa,
                fecha=fecha.date()
            ).count()
            print(f"Número de tareas encontradas para {fecha.date()}: {count_tareas}")

            # Buscar también un día después para verificar la teoría
            fecha_siguiente = fecha + timedelta(days=1)
            count_tareas_siguiente = TareaFragmentada.objects.filter(
                programa=programa,
                fecha=fecha_siguiente.date()
            ).count()
            print(f"Número de tareas encontradas para {fecha_siguiente.date()}: {count_tareas_siguiente}")
            
            # Preparar respuesta base
            response_data = {
                'programa': {
                    'id': programa.id,
                    'nombre': programa.nombre,
                    'fecha_inicio': programa.fecha_inicio,
                    'fecha_fin': programa.fecha_fin,
                    'fecha_actual': fecha_solicitada,
                    'es_dia_laboral': es_dia_laboral
                },
                'tareas': []
            }
            
            # Si no es día laboral, retornar respuesta sin tareas
            if not es_dia_laboral:
                return Response(response_data)
            
            # Obtener las tareas fragmentadas para esta fecha
            tareas_dia = TareaFragmentada.objects.filter(
                programa=programa,
                fecha=fecha.date()
            ).select_related(
                'tarea_original__proceso',
                'tarea_original__maquina',
                'tarea_original__ruta__orden_trabajo',
                'operador'
            )
            
            for tarea in tareas_dia:
                item_ruta = tarea.tarea_original
                if not item_ruta:
                    continue
                    
                orden_trabajo = item_ruta.ruta.orden_trabajo
                
                tarea_data = {
                    'id': tarea.id,
                    'item_ruta_id': item_ruta.id,
                    'orden_trabajo': {
                        'id': orden_trabajo.id,
                        'codigo': orden_trabajo.codigo_ot,
                        'descripcion': orden_trabajo.descripcion_producto_ot
                    },
                    'proceso': {
                        'id': item_ruta.proceso.id,
                        'codigo': item_ruta.proceso.codigo_proceso,
                        'descripcion': item_ruta.proceso.descripcion
                    },
                    'maquina': {
                        'id': item_ruta.maquina.id,
                        'codigo': item_ruta.maquina.codigo_maquina,
                        'descripcion': item_ruta.maquina.descripcion
                    } if item_ruta.maquina else None,
                    'cantidades': {
                        'programada': float(tarea.cantidad_asignada),
                        'pendiente_anterior': float(tarea.cantidad_pendiente_anterior),
                        'total_dia': float(tarea.cantidad_total_dia),
                        'completada': float(tarea.cantidad_completada),
                        'pendiente': float(tarea.cantidad_pendiente)
                    },
                    'kilos': {
                        'fabricados': float(tarea.kilos_fabricados),
                        'programados': float(tarea.cantidad_asignada) * float(orden_trabajo.peso_unitario)
                    },
                    'estado': tarea.estado,
                    'porcentaje_cumplimiento': float(tarea.porcentaje_cumplimiento),
                    'operador': {
                        'id': tarea.operador.id,
                        'nombre': tarea.operador.nombre
                    } if tarea.operador else None,
                    'es_continuacion': tarea.es_continuacion,
                    'observaciones': tarea.observaciones
                }
                print(tarea.cantidad_completada)
                response_data['tareas'].append(tarea_data)
            
            # Para depuración - Imprimir todas las tareas fragmentadas de este programa
            todas_tareas = TareaFragmentada.objects.filter(programa=programa).order_by('fecha')
            print(f"Programa {programa.id} - Tareas fragmentadas existentes:")
            for t in todas_tareas:
                print(f"  Fecha: {t.fecha}, OT: {t.tarea_original.ruta.orden_trabajo.codigo_ot if t.tarea_original else 'N/A'}, Proceso: {t.tarea_original.proceso.descripcion if t.tarea_original else 'N/A'}")
            
            return Response(response_data)
            
        except Exception as e:
            print(f"Error en SupervisorReportView.get: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, pk):
        try:
            tarea_id = request.data.get('tarea_id')
            print(f"[DEBUG] Datos recibidos: {request.data}")
            
            with transaction.atomic():
                if tarea_id:
                    tarea = get_object_or_404(TareaFragmentada, id=tarea_id)
                    print(f"[DEBUG] Tarea encontrada: {tarea.id} - Estado: {tarea.estado}")
                else:
                    tarea = get_object_or_404(TareaFragmentada, id=pk)
                
                # Si se reciben kilos fabricados, calcular unidades
                if 'kilos_fabricados' in request.data:
                    kilos_fabricados = float(request.data.get('kilos_fabricados', 0))
                    tarea.kilos_fabricados = kilos_fabricados
                    
                    # Obtener peso unitario
                    orden_trabajo = tarea.tarea_original.ruta.orden_trabajo
                    peso_unitario = float(orden_trabajo.peso_unitario) if orden_trabajo and orden_trabajo.peso_unitario else None
                    
                    # Si no tiene peso unitario en la orden, intentar obtenerlo del producto
                    if not peso_unitario or peso_unitario <= 0:
                        try:
                            from Product.models import Producto, Pieza
                            codigo_producto = orden_trabajo.codigo_producto_salida
                            if codigo_producto:
                                try:
                                    producto = Producto.objects.get(codigo_producto=codigo_producto)
                                    peso_unitario = float(producto.peso_unitario)
                                except Producto.DoesNotExist:
                                    try:
                                        pieza = Pieza.objects.get(codigo_pieza=codigo_producto)
                                        peso_unitario = float(pieza.peso_unitario)
                                    except Pieza.DoesNotExist:
                                        pass
                        except Exception as e:
                            print(f"Error al buscar peso unitario del producto: {str(e)}")
                    
                    # Calcular unidades si tenemos peso unitario
                    if peso_unitario and peso_unitario > 0:
                        unidades_fabricadas = round(kilos_fabricados / peso_unitario)
                        tarea.unidades_fabricadas = unidades_fabricadas
                        tarea.cantidad_completada = unidades_fabricadas
                        
                # Actualizar otros campos
                if 'observaciones' in request.data:
                    tarea.observaciones = request.data.get('observaciones', '')
                
                if 'estado' in request.data:
                    tarea.estado = request.data.get('estado')
                
                # Antes de crear/actualizar EjecucionTarea
                print(f"[DEBUG] Creando/actualizando ejecución para tarea {tarea.id}")
                print(f"[DEBUG] Fecha de tarea: {tarea.fecha}")
                print(f"[DEBUG] Estado: {tarea.estado}")
                print(f"[DEBUG] Cantidad completada: {tarea.cantidad_completada}")

                now = timezone.now()
                fecha_hora = timezone.datetime.combine(
                    tarea.fecha,
                    now.time(),
                    tzinfo=timezone.get_current_timezone()
                )
                print(f"[DEBUG] Fecha hora calculada: {fecha_hora}")

                ejecucion, created = EjecucionTarea.objects.get_or_create(
                    tarea=tarea,
                    fecha_hora_inicio__date=tarea.fecha,
                    defaults={
                        'fecha_hora_inicio': fecha_hora,
                        'fecha_hora_fin': fecha_hora,
                        'cantidad_producida': tarea.cantidad_completada,
                        'operador': tarea.operador,
                        'estado': tarea.estado
                    }
                )
                print(f"[DEBUG] Ejecución {'creada' if created else 'actualizada'}: {ejecucion.id}")

                if not created:
                    ejecucion.fecha_hora_fin = fecha_hora
                    ejecucion.cantidad_producida = tarea.cantidad_completada
                    ejecucion.estado = tarea.estado
                    ejecucion.save()
                    print(f"[DEBUG] Ejecución actualizada con nueva fecha fin: {ejecucion.fecha_hora_fin}")

                tarea.save()
                
                # Verificar registros después de guardar
                ejecuciones = EjecucionTarea.objects.filter(
                    tarea__programa_id=tarea.programa_id,
                    fecha_hora_inicio__date=tarea.fecha
                )
                print(f"[DEBUG] Total de ejecuciones para el día: {ejecuciones.count()}")
                for e in ejecuciones:
                    print(f"[DEBUG] - Ejecución {e.id}: Tarea {e.tarea_id}, Estado {e.estado}, Cantidad {e.cantidad_producida}")

                return Response({
                    'message': 'Tarea actualizada correctamente',
                    'tarea': TareaFragmentadaSerializer(tarea).data
                })
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TimelineEjecucionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def crear_ejecuciones_por_avance(self, programa, fecha):
        """
        Crea registros de ejecución para todas las tareas que tienen avance pero no tienen registro
        """
        print(f"[DEBUG] Creando ejecuciones por avance para programa {programa.id} fecha {fecha}")
        
        # Buscar todas las tareas que tienen avance
        tareas_con_avance = TareaFragmentada.objects.filter(
            programa=programa,
            fecha=fecha,
            cantidad_completada__gt=0  # Tareas que tienen algún avance
        ).select_related(
            'tarea_original__proceso',
            'tarea_original__maquina',
            'tarea_original__ruta__orden_trabajo',
            'operador'
        ).order_by(
            'tarea_original__ruta__orden_trabajo__codigo_ot',
            'tarea_original__item'
        )
        
        print(f"[DEBUG] Encontradas {tareas_con_avance.count()} tareas con avance")
        ejecuciones_creadas = 0
        
        for tarea in tareas_con_avance:
            # Verificar si ya existe una ejecución para esta tarea en esta fecha
            ejecucion_existente = EjecucionTarea.objects.filter(
                tarea=tarea,
                fecha_hora_inicio__date=fecha
            ).exists()
            
            if not ejecucion_existente:
                # Crear nueva ejecución
                fecha_hora = timezone.datetime.combine(
                    fecha,
                    timezone.now().time(),
                    tzinfo=timezone.get_current_timezone()
                )
                
                EjecucionTarea.objects.create(
                    tarea=tarea,
                    fecha_hora_inicio=fecha_hora,
                    fecha_hora_fin=fecha_hora,
                    cantidad_producida=tarea.cantidad_completada,
                    operador=tarea.operador,
                    estado=tarea.estado
                )
                ejecuciones_creadas += 1
                print(f"[DEBUG] Creada ejecución para tarea {tarea.id} - OT: {tarea.tarea_original.ruta.orden_trabajo.codigo_ot} - Proceso: {tarea.tarea_original.proceso.descripcion}")
        
        print(f"[DEBUG] Total de ejecuciones creadas: {ejecuciones_creadas}")
        return ejecuciones_creadas

    def get(self, request, pk):
        try:
            programa = get_object_or_404(ProgramaProduccion, id=pk)
            fecha_solicitada = request.GET.get('fecha', timezone.now().date().strftime('%Y-%m-%d'))
            fecha = datetime.strptime(fecha_solicitada, '%Y-%m-%d').date()
            
            print(f"[DEBUG] Buscando ejecuciones para programa {pk} en fecha {fecha}")
            
            # Crear ejecuciones para tareas con avance que no tengan registro
            ejecuciones_creadas = self.crear_ejecuciones_por_avance(programa, fecha)
            if ejecuciones_creadas > 0:
                print(f"[DEBUG] Se crearon {ejecuciones_creadas} nuevas ejecuciones")
            
            # Obtener todas las ejecuciones ordenadas
            ejecuciones = EjecucionTarea.objects.filter(
                tarea__programa=programa,
                fecha_hora_inicio__date=fecha
            ).select_related(
                'tarea__tarea_original__proceso',
                'tarea__tarea_original__maquina',
                'tarea__tarea_original__ruta__orden_trabajo',
                'operador'
            ).order_by(
                'tarea__tarea_original__ruta__orden_trabajo__codigo_ot',
                'tarea__tarea_original__item'
            )
            
            print(f"[DEBUG] Total de ejecuciones encontradas: {ejecuciones.count()}")
            
            timeline_data = []
            for ejecucion in ejecuciones:
                tarea = ejecucion.tarea
                item_ruta = tarea.tarea_original
                orden_trabajo = item_ruta.ruta.orden_trabajo
                
                timeline_data.append({
                    'id': ejecucion.id,
                    'tarea_id': tarea.id,
                    'orden_trabajo': {
                        'codigo': orden_trabajo.codigo_ot,
                        'descripcion': orden_trabajo.descripcion_producto_ot
                    },
                    'proceso': {
                        'codigo': item_ruta.proceso.codigo_proceso,
                        'descripcion': item_ruta.proceso.descripcion,
                        'item': item_ruta.item
                    },
                    'maquina': {
                        'codigo': item_ruta.maquina.codigo_maquina,
                        'descripcion': item_ruta.maquina.descripcion
                    },
                    'operador': {
                        'id': ejecucion.operador.id,
                        'nombre': ejecucion.operador.nombre
                    } if ejecucion.operador else None,
                    'tiempo': {
                        'inicio': ejecucion.fecha_hora_inicio,
                        'fin': ejecucion.fecha_hora_fin
                    },
                    'cantidad_producida': float(ejecucion.cantidad_producida),
                    'cantidad_total': float(tarea.cantidad_asignada),
                    'cantidad_pendiente': float(tarea.cantidad_pendiente),
                    'porcentaje_avance': float(tarea.porcentaje_cumplimiento),
                    'estado': ejecucion.estado,
                    'observaciones': ejecucion.observaciones
                })
            
            return Response({
                'programa': {
                    'id': programa.id,
                    'nombre': programa.nombre,
                    'fecha': fecha_solicitada
                },
                'timeline': timeline_data
            })
            
        except Exception as e:
            print(f"Error en TimelineEjecucionView: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ReporteSupervisorListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            fecha_inicio = request.GET.get('fecha_inicio')
            fecha_fin = request.GET.get('fecha_fin')
            programa_id = request.GET.get('programa_id')
            
            # Filtrar reportes
            reportes = ReporteDiarioPrograma.objects.all()
            
            if fecha_inicio:
                reportes = reportes.filter(fecha__gte=fecha_inicio)
            if fecha_fin:
                reportes = reportes.filter(fecha__lte=fecha_fin)
            if programa_id:
                reportes = reportes.filter(programa_id=programa_id)
                
            reportes = reportes.select_related('programa')
            
            data = []
            for reporte in reportes:
                data.append({
                    'id': reporte.id,
                    'fecha': reporte.fecha,
                    'programa': {
                        'id': reporte.programa.id,
                        'nombre': reporte.programa.nombre
                    },
                    'total_tareas': reporte.total_tareas,
                    'tareas_completadas': reporte.tareas_completadas,
                    'porcentaje_cumplimiento': float(reporte.porcentaje_cumplimiento),
                    'observaciones': reporte.observaciones
                })
                
            return Response(data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class ResumenDiarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, programa_id, fecha):
        try:
            programa = get_object_or_404(ProgramaProduccion, id=programa_id)
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()

            # Obtener las tareas del supervisor report
            supervisor_report = SupervisorReportView()
            response = supervisor_report.get(request, programa_id)
            tareas = response.data['tareas']

            total_tareas = len(tareas)
            completadas = sum(1 for t in tareas if t['estado'] == 'COMPLETADO')
            en_proceso = sum(1 for t in tareas if t['estado'] == 'EN_PROCESO')
            pendientes = sum(1 for t in tareas if t['estado'] == 'PENDIENTE')

            return Response({
                'total_tareas': total_tareas,
                'completadas': completadas,
                'en_proceso': en_proceso,
                'pendientes': pendientes,
                'porcentaje_completado': (completadas / total_tareas * 100) if total_tareas > 0 else 0
            })
        
        except Exception as e:
            print(f"Error en ResumenDiarioView.get: {str(e)}")  # Para debugging
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def calcular_porcentaje_completado(self, tareas):
        if not tareas:
            return 0
        return sum(tarea.porcentaje_cumplimiento for tarea in tareas) / tareas.count()

class FinalizarDiaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, programa_id, fecha):
        """Previsualiza el cierre del día"""
        try:
            programa = get_object_or_404(ProgramaProduccion, id=programa_id)
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()

            # Verificar si el día ya está cerrado
            if ReporteDiarioPrograma.objects.filter(
                programa=programa,
                fecha=fecha_obj,
                estado='CERRADO'
            ).exists():
                return Response({
                    'error': 'Este día ya está cerrado'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Obtener tareas incompletas
            tareas_incompletas = TareaFragmentada.objects.filter(
                programa=programa,
                fecha=fecha_obj,
                estado__in=['PENDIENTE', 'EN_PROCESO']
            ).select_related(
                'tarea_original__proceso',
                'tarea_original__maquina',
                'tarea_original__ruta__orden_trabajo'
            )

            preview_data = {
                'fecha': fecha,
                'siguiente_dia': self.obtener_siguiente_dia_laboral(fecha_obj).strftime('%Y-%m-%d'),
                'tareas_pendientes': []
            }

            for tarea in tareas_incompletas:
                if tarea.cantidad_pendiente > 0:
                    preview_data['tareas_pendientes'].append({
                        'id': tarea.id,
                        'orden_trabajo': tarea.tarea_original.ruta.orden_trabajo.codigo_ot,
                        'proceso': tarea.tarea_original.proceso.descripcion,
                        'cantidad_pendiente': float(tarea.cantidad_pendiente),
                        'porcentaje_completado': float(tarea.porcentaje_cumplimiento)
                    })

            return Response(preview_data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @transaction.atomic
    def post(self, request, programa_id, fecha):
        """Finaliza el día y crea las continuaciones necesarias"""
        try:
            programa = get_object_or_404(ProgramaProduccion, id=programa_id)
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
            siguiente_dia = self.obtener_siguiente_dia_laboral(fecha_obj)

            # Verificar si el día ya está cerrado
            if ReporteDiarioPrograma.objects.filter(
                programa=programa,
                fecha=fecha_obj,
                estado='CERRADO'
            ).exists():
                return Response({
                    'error': 'Este día ya está cerrado'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Procesar tareas incompletas
            tareas_procesadas = []
            for tarea in TareaFragmentada.objects.filter(
                programa=programa,
                fecha=fecha_obj,
                estado__in=['PENDIENTE', 'EN_PROCESO']
            ):
                if tarea.cantidad_pendiente > 0:
                    # Crear continuación
                    continuacion = tarea.crear_continuacion(
                        tarea.cantidad_pendiente,
                        siguiente_dia
                    )
                    
                    # Actualizar estado de la tarea actual
                    tarea.estado = 'CONTINUADO'
                    tarea.save()

                    tareas_procesadas.append({
                        'tarea_original_id': tarea.id,
                        'continuacion_id': continuacion.id,
                        'cantidad_pendiente': float(tarea.cantidad_pendiente)
                    })

            # Crear reporte diario
            ReporteDiarioPrograma.objects.create(
                programa=programa,
                fecha=fecha_obj,
                estado='CERRADO',
                cerrado_por=request.user,
                fecha_cierre=timezone.now()
            )

            return Response({
                'mensaje': 'Día finalizado correctamente',
                'fecha': fecha,
                'siguiente_dia': siguiente_dia.strftime('%Y-%m-%d'),
                'tareas_procesadas': tareas_procesadas
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def obtener_siguiente_dia_laboral(self, fecha):
        """Obtiene el siguiente día laboral (excluye fines de semana)"""
        siguiente_dia = fecha + timedelta(days=1)
        while siguiente_dia.weekday() >= 5:  # 5 = Sábado, 6 = Domingo
            siguiente_dia += timedelta(days=1)
        return siguiente_dia


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerar_tareas_programa(request, programa_id):
    try:
        programa = get_object_or_404(ProgramaProduccion, id=programa_id)
        
        # Eliminar tareas fragmentadas existentes
        TareaFragmentada.objects.filter(programa=programa).delete()
        
        # Eliminar reportes diarios existentes
        ReporteDiarioPrograma.objects.filter(programa=programa).delete()
        
        time_calculator = TimeCalculator()
        scheduler = ProductionScheduler(time_calculator)
        
        # Obtener datos del timeline
        program_ots = ProgramaOrdenTrabajo.objects.filter(
            programa=programa
        ).select_related(
            'orden_trabajo',
            'orden_trabajo__ruta_ot'
        ).prefetch_related(
            'orden_trabajo__ruta_ot__items',
            'orden_trabajo__ruta_ot__items__proceso',
            'orden_trabajo__ruta_ot__items__maquina'
        ).order_by('prioridad')
        
        # Preparar datos para la regeneración
        ordenes_trabajo = []
        for prog_ot in program_ots:
            ot = prog_ot.orden_trabajo
            ot_data = {
                'orden_trabajo': ot.id,
                'orden_trabajo_codigo_ot': ot.codigo_ot,
                'orden_trabajo_descripcion_producto_ot': ot.descripcion_producto_ot,
                'procesos': []
            }

            ruta = getattr(ot, 'ruta_ot', None)
            if ruta:
                for item in ruta.items.all().order_by('item'):
                    proceso_data = {
                        'id': item.id,
                        'item': item.item,
                        'descripcion': item.proceso.descripcion if item.proceso else None,
                        'maquina_id': item.maquina.id if item.maquina else None,
                        'cantidad': item.cantidad_pedido,
                        'estandar': item.estandar,
                        'prioridad': prog_ot.prioridad
                    }
                    ot_data['procesos'].append(proceso_data)
            
            ordenes_trabajo.append(ot_data)
        
        # Regenerar tareas fragmentadas
        success = scheduler.create_fragmented_tasks(programa, ordenes_trabajo)
        
        if success:
            return Response({
                'message': 'Tareas fragmentadas regeneradas correctamente',
                'tareas_generadas': TareaFragmentada.objects.filter(programa=programa).count()
            })
        else:
            return Response(
                {'error': 'Error al regenerar tareas fragmentadas'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    except Exception as e:
        print(f"Error regenerando tareas: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_production_details(request, task_id):
    try:
        tarea = TareaFragmentada.objects.select_related(
            'tarea_original__ruta__orden_trabajo',
            'tarea_original__proceso',
            'tarea_original__maquina',
            'operador'
        ).get(id=task_id)
        
        return Response({
            'numero_ot': tarea.tarea_original.ruta.orden_trabajo.codigo_ot,
            'etapa': tarea.tarea_original.item,
            'cantidad_unidades': tarea.cantidad_asignada,
            'saldo_pendiente': tarea.cantidad_pendiente,
            'codigo_producto': tarea.tarea_original.ruta.orden_trabajo.codigo_producto_salida,
            'nombre_producto': tarea.tarea_original.ruta.orden_trabajo.descripcion_producto_ot,
            'materia_prima': tarea.tarea_original.ruta.orden_trabajo.materia_prima.descripcion if tarea.tarea_original.ruta.orden_trabajo.materia_prima else '',
            'proceso': tarea.tarea_original.proceso.descripcion,
            'maquina': tarea.tarea_original.maquina.descripcion,
            'estandar_hora': tarea.tarea_original.estandar,
            'rut_trabajador': tarea.operador.rut if tarea.operador else '',
            'horas_trabajadas': 0,  # Esto vendría de EjecucionTarea
            'sobretiempo': 0,  # Esto vendría de EjecucionTarea
        })
    except TareaFragmentada.DoesNotExist:
        return Response(
            {"error": "Tarea no encontrada"},
            status=status.HTTP_404_NOT_FOUND
        )