from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.utils.dateparse import parse_date
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import localtime, now
from django.shortcuts import get_object_or_404


from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


from .serializers import *
from .models import *
from Operator.models import *
from Utils.models import MeasurementUnit, MateriaPrima
from Client.models import Cliente

from datetime import datetime, timedelta, date, time
from collections import defaultdict
import csv, chardet, pytz, io, logging, traceback, os


from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, A3, A2, A1
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def importar_ordenes_trabajo(path_file):
    created_count = 0
    updated_count = 0
    failed_count = 0
    errors = []

    with open(path_file, 'rb') as f:
        result = chardet.detect(f.read())
        encoding = result['encoding']

    print(f'Usando la codificación detectada: {encoding}')
    try:
        with open(path_file, 'r', encoding=encoding) as file:
            reader = csv.reader(file, delimiter='$')
            next(reader)

            for row in reader:
                #if row[2].strip() in ['P', 'S']:
                try:
                    if len(row) != 24:
                        print(f"Fila inválida: {row}")
                        continue
                    
                    codigo_ot = int(row[0].strip())
                    tipo_ot_codigo = row[1].strip()
                    situacion_ot_codigo = row[2].strip()
                    try:
                        fecha_emision = datetime.strptime(row[3].strip(), '%Y/%m/%d')
                    except ValueError:
                        fecha_emision = None

                    try:
                        fecha_proc = datetime.strptime(row[4].strip(), '%Y/%m/%d')
                    except ValueError:
                        fecha_proc = None

                    try:
                        fecha_termino = datetime.strptime(row[5].strip(), '%Y/%m/%d')
                    except ValueError:
                        fecha_termino = None

                    cliente_codigo = row[7].strip()
                    nro_nota_venta_ot = row[8].strip()
                    item_nota_venta = int(row[9].strip())
                    referencia_nota_venta = int(row[10].strip())
                    codigo_producto_inicial = row[11].strip()
                    codigo_producto_salida = row[12].strip()
                    descripcion_producto_ot = row[13].strip()

                    try:
                        cantidad_str = row[14].strip()
                        puntos = puntos = ['', ' ', '.', '. ',' .']

                        if cantidad_str in puntos:
                            cantidad = 0.0
                        else:
                            cantidad = float(cantidad_str)
                    except (ValueError, IndexError) as e:
                        print(f'Error al convertir la cantidad en la fila: {row}: {str(e)}')
                        cantidad = 0.0

                    unidad_medida_codigo = row[15].strip()

                    try:
                        cantidad_avance_str = row[16].strip()
                        puntos = ['', ' ', '.', '. ',' .']
                        if cantidad_avance_str in puntos:
                            cantidad_avance = 0.0
                        else:
                            cantidad_avance = float(cantidad_avance_str)
                    except(ValueError, IndexError):
                        print(f'Error al convertir la cantidad_avance en la fila: {row} : {str(e)}')
                        cantidad_avance = 0.0

                    try:
                        peso_unitario_str = row[17].strip()
                        puntos = ['', ' ', '.', '. ',' .']
                        if peso_unitario_str in puntos:
                            peso_unitario = 0.0
                        else: 
                            peso_unitario = float(peso_unitario_str)
                    except(ValueError, IndexError) as e:
                        print(f'Error al convertir el peso unitario en la fila: {row} : {str(e)}')
                        peso_unitario = 0.0

                    materia_prima_codigo = row[18].strip()

                    try:
                        cantidad_materia_prima_str = row[17].strip()
                        puntos = ['', ' ', '.', '. ',' .']
                        if cantidad_materia_prima_str in puntos:
                            cantidad_materia_prima = 0.0
                        else:
                            cantidad_materia_prima = float(cantidad_materia_prima_str)
                    
                    except(ValueError, IndexError) as e:
                        print(f'Error al convertir la cantidad de materia prima en la fila: {row} : {str(e)}')
                        cantidad_materia_prima = 0.0

                    unidad_materia_prima_codigo = row[20].strip()

                    observacion_ot = row[21].strip()
                    empresa_codigo = row[22].strip()

                    multa_valor = row[23].strip()
                    
                    tipo_ot, _ = TipoOT.objects.get_or_create(codigo_tipo_ot=tipo_ot_codigo)

                    situacion_ot, _ = SituacionOT.objects.get_or_create(codigo_situacion_ot=situacion_ot_codigo)

                    if cliente_codigo != '000000' and len(cliente_codigo) < 7 and cliente_codigo != '':
                        cliente, _ = Cliente.objects.get_or_create(codigo_cliente=cliente_codigo)
                    else:
                        cliente = None

                    unidad_medida, _ = MeasurementUnit.objects.get_or_create(codigo_und_medida=unidad_materia_prima_codigo)

                    materia_prima, _ = MateriaPrima.objects.get_or_create(codigo=materia_prima_codigo)

                    unidad_medida_mprima, _ = MeasurementUnit.objects.get_or_create(codigo_und_medida=unidad_materia_prima_codigo)

                    empresa, _ = EmpresaOT.objects.get_or_create(codigo_empresa=empresa_codigo)

                    multa = multa_valor == 'M'

                    if situacion_ot.codigo_situacion_ot in ['P', 'S']:
                        orden_trabajo, created = OrdenTrabajo.objects.update_or_create(
                        codigo_ot=codigo_ot,
                        defaults={
                            'tipo_ot': tipo_ot,
                            'situacion_ot': situacion_ot,
                            'fecha_emision': fecha_emision,
                            'fecha_proc': fecha_proc,
                            'fecha_termino': fecha_termino,
                            'cliente': cliente,
                            'nro_nota_venta_ot': nro_nota_venta_ot,
                            'item_nota_venta': item_nota_venta,
                            'referencia_nota_venta': referencia_nota_venta,
                            'codigo_producto_inicial': codigo_producto_inicial,
                            'codigo_producto_salida': codigo_producto_salida,
                            'descripcion_producto_ot': descripcion_producto_ot,
                            'cantidad': cantidad,
                            'unidad_medida': unidad_medida,
                            'cantidad_avance': cantidad_avance,
                            'peso_unitario': peso_unitario,
                            'materia_prima': materia_prima,
                            'cantidad_mprima': cantidad_materia_prima,
                            'unidad_medida_mprima': unidad_medida_mprima,
                            'observacion_ot': observacion_ot,
                            'empresa': empresa,
                            'multa': multa,
                        }
                        )
                        if created:
                            print(f'Orden de trabajo {codigo_ot} creada.')
                            created_count+=1
                        else:
                            print(f'Orden de trabajo {codigo_ot} actualizada.')
                            updated_count+=1
                    else:
                        print('Situación no correspondiente. Saltando...')
                        continue
                    

                except (ValueError, IntegrityError) as e:
                    print(f'Error al procesar la fila {row}: {str(e)}')
                    failed_count += 1
                    errors.append(str(e))

                except Exception as e:
                    print(f'Error inesperado al procesar la fila {row}: {str(e)}')
                    failed_count += 1
                    errors.append(str(e))
    except UnicodeDecodeError:
        print(f'Error de codificación con {encoding}')
    
    return {
        'success': True,
        'created_count': created_count,
        'updated_count': updated_count,
        'failed_count': failed_count,
        'errors': errors
    }

def importar_ots_from_file(request):
    path_file = 'W:\\ot.txt'
    result = importar_ordenes_trabajo(path_file)
    if result['success']:
        return JsonResponse({
            'message': 'OrdenTrabajo instances imported successfully',
            'created_count': result['created_count'],
            'updated_count': result['updated_count'],
            'failed_count': result['failed_count'],
            'errors': result['errors'],
        }, status=200)
    else:
        return JsonResponse({'error': result['errors']}, status=500)

def importar_rutas_ot(path_file):
    created_count = 0
    updated_count = 0
    failed_count = 0
    errors = []
    ordenes = OrdenTrabajo.objects.all()
    codigos_ot = []
    for orden in ordenes:
        codigos_ot.append(orden.codigo_ot)

    with open(path_file, 'rb') as f:
        resultado = chardet.detect(f.read())
        encoding = resultado['encoding']
    print(f'Usando la codificación detectada: {encoding}')
    try:
        with open(path_file, 'r', encoding=encoding) as file:
            reader = csv.reader(file, delimiter='@')
            next(reader)

    
            for idx, row in enumerate(reader):
                try:
                    if len(row) != 9:
                        print(f'Fila inválida: {idx}')
                        continue
                    
                    codigo_ot = int(row[0].strip())
                    if codigo_ot in codigos_ot:
                        item = int(row[1].strip())

                        codigo_proceso = row[2].strip()
                        codigo_maquina = row[3].strip()

                        estandar = int(row[4].strip())
                        try:
                            cantidad_pedido_str = row[5].strip()
                            puntos = ['', ' ', '.', '. ',' .']

                            if cantidad_pedido_str in puntos:
                                cantidad_pedido = 0.0
                            else:
                                cantidad_pedido = float(cantidad_pedido_str)
                        except(ValueError, IndexError) as e:
                            print(f'Error al convretir la cantidad_pedido en la fila: {idx} - {str(e)}')

                        try:
                            cantidad_terminado_str = row[6].strip()
                            puntos = ['', ' ', '.', '. ',' .']

                            if cantidad_terminado_str in puntos:
                                cantidad_terminado = 0.0
                            else:
                                cantidad_terminado = float(cantidad_terminado_str)
                        except(ValueError, IndexError) as e:
                            print(f'Error al convertir la cantidad_terminado en la fila: {idx} - {str(e)}')

                        try:
                            cantidad_terminado_str = row[6].strip()
                            puntos = ['', ' ', '.', '. ',' .']

                            if cantidad_terminado_str in puntos:
                                cantidad_terminado = 0.0
                            else:
                                cantidad_terminado = float(cantidad_terminado_str)
                        except(ValueError, IndexError) as e:
                            print(f'Error al convertir la cantidad_terminado en la fila: {idx} - {str(e)}')

                        try:
                            cantidad_perdida_str = row[7].strip()
                            puntos = ['', ' ', '.', '. ',' .']

                            if cantidad_perdida_str in puntos:
                                cantidad_perdida = 0.0
                            else:
                                cantidad_perdida = float(cantidad_perdida_str)

                        except(ValueError, IndexError) as e:
                            print(f'Error al convertir la cantidad_perdida en la fila: {row} - {str(e)}')

                        try:
                            terminado_sin_actualizar_str = row[8].strip()
                            puntos = ['', ' ', '.', '. ', ' .']

                            if terminado_sin_actualizar_str in puntos:
                                terminado_sin_actualizar = 0.0
                            else:
                                terminado_sin_actualizar = float(terminado_sin_actualizar_str)
                        
                        except(ValueError, IndexError) as e: 
                            print(f'Error al convertir el campo terminado_sin_actualizar en la fila: {idx} - {str(e)}')

                        try:
                            three_months_ago = datetime.now().date() - timedelta(days=90)
                        except:
                            continue
                        
                        
                        orden_trabajo = ordenes.get(codigo_ot=codigo_ot)

                        situacion_ot = orden_trabajo.situacion_ot.codigo_situacion_ot
                        fecha_termino = orden_trabajo.fecha_termino
                        

                        ruta_ot, created_ruta = RutaOT.objects.get_or_create(orden_trabajo=orden_trabajo)
                        ### crear rutas que matcheen con la ots existentes en el sistema.
                        try:
                            maquina = Maquina.objects.get(codigo_maquina=codigo_maquina)
                        except Maquina.DoesNotExist:
                            continue

                        try:
                            proceso = Proceso.objects.get(codigo_proceso=codigo_proceso)
                        except Proceso.DoesNotExist:
                            continue
                        except MultipleObjectsReturned:
                            proceso = Proceso.objects.filter(codigo_proceso=codigo_proceso).first()

                        try:
                            with transaction.atomic():
                                item_ruta, created_item = ItemRuta.objects.get_or_create(
                                    ruta=ruta_ot,
                                    item=item,
                                    defaults={
                                        'maquina': maquina,
                                        'proceso': proceso,
                                        'estandar': estandar,
                                        'cantidad_pedido': cantidad_pedido,
                                        'cantidad_terminado_proceso': cantidad_terminado,
                                        'cantidad_perdida_proceso': cantidad_perdida,
                                        'terminado_sin_actualizar' : terminado_sin_actualizar,

                                    }
                                )

                                if not created_item:
                                    if situacion_ot in ['C', 'A']:
                                        pass
                                    elif situacion_ot == 'T' and fecha_termino <= three_months_ago and fecha_termino is not None:
                                        item_ruta.cantidad_pedido = cantidad_pedido
                                        item_ruta.cantidad_terminado_proceso = cantidad_terminado
                                        item_ruta.cantidad_perdida_proceso = cantidad_perdida
                                        item_ruta.terminado_sin_actualizar = terminado_sin_actualizar
                                        item_ruta.save()

                                    elif situacion_ot not in ['C', 'A', 'T']:
                                        item_ruta.cantidad_pedido = cantidad_pedido
                                        item_ruta.cantidad_terminado_proceso = cantidad_terminado
                                        item_ruta.cantidad_perdida_proceso = cantidad_perdida
                                        item_ruta.terminado_sin_actualizar = terminado_sin_actualizar
                                        item_ruta.save()

                                    print(f'ItemRuta de OT {item_ruta} actualizado.')
                                    updated_count +=1
                                else:
                                    print(f'ItemRuta de OT {item_ruta} creada.')
                                    created_count +=1
                        except Exception as e:
                            print(f'Error inesperado al procesar la fila {row}: {str(e)}')
                            failed_count += 1
                            errors.append(str(e))
                    else:
                        print(f'Orden {codigo_ot} no válida.')
                        continue
                    
                except (ValueError, IntegrityError) as e:
                    print(f'Error al procesar la fila: {row} : {str(e)}')
                    failed_count += 1
                    errors.append(str(e))
                except Exception as e:
                    print(f'Error inesperado al procesar la fila {row}: {str(e)}')
                    failed_count += 1
                    errors.append(str(e))
    except UnicodeDecodeError:
        print(f'Error de codificación con {encoding}')

    return {
        'success': True,
        'created_count': created_count,
        'updated_count': updated_count,
        'failed_count': failed_count,
        'errors': errors
    }

def importar_rutaot_file(request):
    path_file = 'W:\\ruta_ot.txt'
    result = importar_rutas_ot(path_file)
    if result['success']:
        return JsonResponse({
            'message': 'RutaOT instances imported successfully',
            'created_count': result['created_count'],
            'updated_count': result['updated_count'],
            'failed_count': result['failed_count'],
            'errors': result['errors'],
        }, status=200)
    else:
        return JsonResponse({'error': result['errors']}, status=500)

# Create your views here.
class OTView(generics.ListAPIView):
    serializer_class = OrdenTrabajoSerializer
    queryset = OrdenTrabajo.objects.all()

class ProgramListView(generics.ListAPIView):
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
            print(f"Programa {pk} eliminado exitosamente")
            return Response({
                "message": "Programa eliminado corretamente"
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
    def post(self, request, *args, **kwargs):
        data = request.data
        print(data)

        #Validar datos requeridos
        if 'fecha_inicio' not in data:
            return Response(
                {"detail": "Fecha de inicio es requerida."},
                status=status.HTTP_400_BAD_REQUEST
            )

        for ot_id in data.get('ordenes', []):
            print(f"Verificando OT con ID: {ot_id}")  # Log
            try:
                orden_trabajo = OrdenTrabajo.objects.select_related(
                    'ruta_ot',
                    'situacion_ot'
                ).prefetch_related(
                    'ruta_ot__items',
                    'ruta_ot__items__proceso',
                    'ruta_ot__items__maquina'
                ).get(id=ot_id)
                print(f"OT encontrada: {orden_trabajo.id} - {orden_trabajo.codigo_ot}")  # Debug
            
            except OrdenTrabajo.DoesNotExist:
                print(f"OT con ID {ot_id} no encontrada")
                raise NotFound(f"Orden de trabajo con ID {ot_id} no encontrada.")

        try:
            with transaction.atomic():
                # Crear ProgramaProduccion
                fecha_inicio = parse_date(data.get('fecha_inicio'))

                if not fecha_inicio:
                    return Response(
                        {"detail": "Fechas de inicio no válida."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                print("fecha pasa")

                programa = ProgramaProduccion.objects.create(
                    nombre=data.get('nombre'),
                    fecha_inicio=fecha_inicio,
                )
                print("programa pasa")
                # Iterar sobre las órdenes de trabajo y crear relaciones
                for ot_data in data.get('ordenes', []):  # Cambiar 'ordenes_trabajo' a 'ordenes' si corresponde
                    print("entra en el bucle for ot_data in data.get")
                    try:
                        orden_trabajo = OrdenTrabajo.objects.get(id=ot_data)
                        print("encuentra la ot")
                    except ObjectDoesNotExist:
                        raise NotFound(f"Orden de trabajo con código {ot_data['codigo_ot']} no encontrada.")

                    # Crear la relación ProgramaOrdenTrabajo
                    pot = ProgramaOrdenTrabajo.objects.create(
                        programa=programa,
                        orden_trabajo=orden_trabajo,
                        prioridad=0,
                    )
                    print(f"Relacion creada: {pot}")
                #Calcular y actualizar fecha_fin
                programa.fecha_fin = programa.fecha_inicio
                programa.save(update_fields=['fecha_fin'])

                # Serializar y devolver respuesta
                serializer = ProgramaProduccionSerializer(programa)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"detail": "Ha ocurrido un error en el servidor.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def update_ruta_ot_items(self, ruta_ot, items_data):
    #print("Items data:", items_data)

        for item_data in items_data:
            try:
                item = ruta_ot.items.get(item=item_data['item'])
                #print("Item instance:", item)
                # Update the machine if 'maquinaSelected' is provided
                if 'maquina' in item_data:
                    item.maquina = Maquina.objects.get(id=item_data['maquina'])
                # Update the standard if 'estandar' is provided
                if 'estandar' in item_data:
                    item.estandar = item_data['estandar']
                item.save()  # Save the changes to the database
            except Exception as e:
                print("Error updating ItemRuta:", e)

def is_working_day(date):
    """Determina si una fecha es día laboral (L-V)"""
    return date.weekday() < 5  # 0-4 son Lunes a Viernes

def get_next_working_day(date):
    """Obtiene el siguiente día laboral"""
    next_day = date + timedelta(days=1)
    while not is_working_day(next_day):
        next_day += timedelta(days=1)
    return next_day

def calculate_working_days(self, start_date, cantidad, estandar):
    """Calcula los intervalos de trabajo considerando horarios laborales."""
    if not isinstance(start_date, datetime):
        start_date = datetime.combine(start_date, time(7, 45))

    current_date = start_date.date()
    current_datetime = start_date
    remaining_units = float(cantidad)
    intervals = []

    # Definir horario laboral
    WORKDAY_START = time(7, 45)
    WORKDAY_END = time(17, 45)
    
    # Definir hora de descanso
    BREAK_START = time(13, 0)
    BREAK_END = time(14, 0)

    #Calcular estandar por hora (9 horas laborables efectivas)
    WORK_HOURS = 9
    estandar_hora = estandar / WORK_HOURS

    # Si la fecha inicial no es día laboral, mover al siguiente dia laboral
    if not is_working_day(current_date):
        next_day = get_next_working_day(current_date)
        current_datetime = datetime.combine(next_day, WORKDAY_START)
        current_date = current_datetime.date()

    while remaining_units > 0:
        # Si no es día laboral, pasar al siguiente
        if not is_working_day(current_date):
            next_day = get_next_working_day(current_date)
            current_datetime = datetime.combine(next_day, WORKDAY_START)
            current_date = current_datetime.date()
            continue

        # Ajustar current_datetime si está fuera del horario laboral
        if current_datetime.time() < WORKDAY_START:
            current_datetime = datetime.combine(current_date, WORKDAY_START)
        elif current_datetime.time() > WORKDAY_END:
            next_day = get_next_working_day(current_date + timedelta(days=1))
            current_datetime = datetime.combine(next_day, WORKDAY_START)
            current_date = current_datetime.date()
            continue
            
        # Verificar si estamos en hora de descanso
        if BREAK_START <= current_datetime.time() < BREAK_END:
            # Si estamos en hora de descanso, avanzar al final del descanso
            current_datetime = datetime.combine(current_date, BREAK_END)

        # Calcular unidades para este intervalo
        units_this_interval = min(remaining_units, estandar)
        
        # Calcular la duración proporcional de la tarea en horas
        # Limitar a máximo 2 horas para mejor visualización
        MAX_TASK_HOURS = 2.0
        
        # Calcular horas disponibles hasta el descanso o fin del día
        if current_datetime.time() < BREAK_START:
            hours_until_break = (datetime.combine(current_date, BREAK_START) - current_datetime).total_seconds() / 3600
            available_hours = min(hours_until_break, MAX_TASK_HOURS)
        else:  # Después del descanso
            hours_until_end = (datetime.combine(current_date, WORKDAY_END) - current_datetime).total_seconds() / 3600
            available_hours = min(hours_until_end, MAX_TASK_HOURS)
        
        # Calcular la duración de la tarea
        task_ratio = units_this_interval / estandar
        task_hours = min(task_ratio * 8, available_hours)  # 8 horas es un día laboral estándar
        
        # Asegurar un mínimo de 30 minutos para tareas pequeñas
        task_hours = max(task_hours, 0.5)
        
        # Calcular la hora de fin
        end_datetime = current_datetime + timedelta(hours=task_hours)
        
        # Verificar si la tarea cruza la hora de descanso
        if current_datetime.time() < BREAK_START and end_datetime.time() > BREAK_START:
            # Terminar esta tarea justo antes del descanso
            end_datetime = datetime.combine(current_date, BREAK_START)
            
            # Recalcular unidades completadas en este intervalo
            hours_worked = (end_datetime - current_datetime).total_seconds() / 3600
            units_completed = min(units_this_interval, (hours_worked / 8) * estandar)
            
            # Crear el intervalo hasta el descanso
            interval = {
                'fecha': current_date,
                'fecha_inicio': current_datetime,
                'fecha_fin': end_datetime,
                'unidades': units_completed,
                'unidades_restantes': remaining_units - units_completed,
                'continue_same_day': True  # Siempre continuar después del descanso
            }
            
            intervals.append(interval)
            
            # Actualizar unidades restantes y hora actual
            remaining_units -= units_completed
            current_datetime = datetime.combine(current_date, BREAK_END)
            
            # Continuar con el siguiente ciclo
            continue
        
        # Asegurar que no exceda el horario laboral
        end_of_day = datetime.combine(current_date, WORKDAY_END)
        if end_datetime > end_of_day:
            end_datetime = end_of_day
        
        # Determinar si el siguiente proceso puede comenzar el mismo día
        # Solo si hay al menos 30 minutos disponibles después de esta tarea
        minutes_left = (end_of_day - end_datetime).total_seconds() / 60
        continue_same_day = minutes_left >= 30 and end_datetime.time() < BREAK_START
        
        # Crear el intervalo
        interval = {
            'fecha': current_date,
            'fecha_inicio': current_datetime,
            'fecha_fin': end_datetime,
            'unidades': units_this_interval,
            'unidades_restantes': remaining_units - units_this_interval,
            'continue_same_day': continue_same_day
        }
        
        intervals.append(interval)
        
        # Actualizar unidades restantes
        remaining_units -= units_this_interval
        
        # Preparar para el siguiente intervalo
        if remaining_units > 0:
            if continue_same_day:
                # Si podemos continuar el mismo día, la próxima tarea comienza 
                # 15 minutos después de esta
                current_datetime = end_datetime + timedelta(minutes=15)
                
                # Verificar si el nuevo inicio cae en hora de descanso
                if BREAK_START <= current_datetime.time() < BREAK_END:
                    current_datetime = datetime.combine(current_date, BREAK_END)
            else:
                # Si no podemos continuar el mismo día, ir al siguiente día laboral
                next_day = get_next_working_day(current_date + timedelta(days=1))
                current_datetime = datetime.combine(next_day, WORKDAY_START)
                current_date = current_datetime.date()
    
    # Calcular próxima fecha disponible
    if intervals:
        last_interval = intervals[-1]
        
        if last_interval['continue_same_day']:
            # Si el último intervalo indica que se puede continuar el mismo día,
            # la próxima fecha disponible es 15 minutos después de la hora de fin
            next_available_time = last_interval['fecha_fin'] + timedelta(minutes=15)
            
            # Verificar si el nuevo inicio cae en hora de descanso
            if BREAK_START <= next_available_time.time() < BREAK_END:
                next_available_time = datetime.combine(next_available_time.date(), BREAK_END)
        else:
            # Si no, la próxima fecha disponible es el siguiente día laboral
            next_day = get_next_working_day(last_interval['fecha'] + timedelta(days=1))
            next_available_time = datetime.combine(next_day, WORKDAY_START)
    else:
        next_available_time = current_datetime
    
    return {
        'intervals': intervals,
        'start_date': intervals[0]['fecha'] if intervals else current_date,
        'end_date': intervals[-1]['fecha'] if intervals else current_date,
        'next_available_time': next_available_time
    }

# Métodos auxiliares para mantener la función principal más limpia
def calculate_task_end_time(self, start_datetime, units, estandar):
    """Calcula la hora de fin de una tarea basada en la cantidad de unidades."""
    WORKDAY_START = time(7, 45)
    WORKDAY_END = time(17, 45)
    WORKDAY_HOURS = (WORKDAY_END.hour - WORKDAY_START.hour) + (WORKDAY_END.minute - WORKDAY_START.minute) / 60
    
    # Calcular la duración proporcional de la tarea en horas
    # Ajustamos para que las tareas no sean demasiado largas visualmente
    # Una tarea con estandar completo tomará como máximo 4 horas
    MAX_TASK_HOURS = 4.0
    task_hours = min((units / estandar) * WORKDAY_HOURS, MAX_TASK_HOURS)
    
    # Redondear a incrementos de 15 minutos para mejor visualización
    task_hours = round(task_hours * 4) / 4  # Redondea a 0.25, 0.5, 0.75, etc.
    
    # Asegurar un mínimo de 30 minutos para tareas pequeñas
    task_hours = max(task_hours, 0.5)
    
    # Calcular la hora de fin
    end_datetime = start_datetime + timedelta(hours=task_hours)
    
    # Asegurar que no exceda el horario laboral
    end_of_day = datetime.combine(start_datetime.date(), WORKDAY_END)
    if end_datetime > end_of_day:
        end_datetime = end_of_day
    
    return end_datetime

def can_continue_same_day(self, end_datetime, workday_end):
    """Determina si hay suficiente tiempo para continuar el mismo día."""
    # Convertir a minutos desde medianoche para comparación fácil
    end_minutes = end_datetime.hour * 60 + end_datetime.minute
    workday_end_minutes = workday_end.hour * 60 + workday_end.minute
    
    # Debe haber al menos 30 minutos disponibles para la siguiente tarea
    return (workday_end_minutes - end_minutes) >= 30

def generate_routes_data(program):
    """Genera los datos de rutas para el timeline basado en un programa de producción."""
    program_ots = ProgramaOrdenTrabajo.objects.filter(
        programa=program
    ).select_related(
        'orden_trabajo',
        'orden_trabajo__ruta_ot'
    ).prefetch_related(
        'orden_trabajo__ruta_ot__items',
        'orden_trabajo__ruta_ot__items__proceso',
        'orden_trabajo__ruta_ot__items__maquina'
    ).order_by('prioridad')

    groups = []
    items = []
    process_timeline = {} #Rastrear ultimo uso de cada máquina
    unidades_acumuladas = {} #Rastrear unidades disponibles por proceso y tiempo

    for prog_ot in program_ots:
        print(f"\nProcesando OT: {prog_ot.orden_trabajo.codigo_ot}")
        ot = prog_ot.orden_trabajo
        ruta = getattr(ot, 'ruta_ot', None)
        if not ruta:
            continue

        ot_group = {
            "id": f"ot_{ot.id}",
            "orden_trabajo_codigo_ot": ot.codigo_ot,
            "descripcion": ot.descripcion_producto_ot,
            "procesos": []
        }

        ruta_items = ruta.items.all().order_by('item')
        next_available_start = datetime.combine(
            ot.fecha_emision or ot.fecha_proc or program.fecha_inicio,
            time(7, 45)
        )
        produccion_acumulada = defaultdict(float)
        
        for i, item_ruta in enumerate(ruta_items):
            print(f"\nProceso {i+1}: {item_ruta.proceso.descripcion}")
            print(f"fecha inicio actual: {next_available_start}")

            proceso = item_ruta.proceso
            maquina = item_ruta.maquina


            proceso_id = f"proc_{item_ruta.id}"
            ot_group["procesos"].append({
                "id": proceso_id,
                "descripcion": f"{proceso.descripcion} - {maquina.descripcion if maquina else 'Sin máquina'}",
                "item": item_ruta.item
            })

            if item_ruta.estandar <= 0:
                item_ruta.estandar = 500

            # Calcular fechas e intervalos
            dates_data = calculate_working_days(
                next_available_start,
                item_ruta.cantidad_pedido,
                item_ruta.estandar
            )

            # Crear un item por cada intervalo
            for idx, interval in enumerate(dates_data['intervals']):
                print(f"Intervalo {idx+1}:")
                print(f"    Inicio: {interval['fecha_inicio']}")
                print(f"    Fin: {interval['fecha_fin']}")
                print(f"    Unidades: {interval['unidades']}")
                print(f"    Continue same day: {interval.get('continue_same_day', False)}")


                # Actualizar producción acumulada
                produccion_acumulada[i] += interval['unidades']

                items.append({
                            "id": f'item_{item_ruta.id}_{idx}',
                            "ot_id": f"ot_{ot.id}",
                            "proceso_id": proceso_id,
                            "name": f"{proceso.descripcion} - {interval['unidades']:.0f} de {item_ruta.cantidad_pedido} unidades",
                            "start_time": interval['fecha_inicio'].strftime('%Y-%m-%d %H:%M:%S'),
                            "end_time": interval['fecha_fin'].strftime('%Y-%m-%d %H:%M:%S'),
                            "cantidad_total": float(item_ruta.cantidad_pedido),
                            "cantidad_intervalo": float(interval['unidades']),
                            "unidades_restantes": float(interval['unidades_restantes']),
                        
                })

                # Verificar si el siguiente proceso puede comenzar
                if i < len(ruta_items) - 1 and interval['continue_same_day']:
                    print(f"    Próximo inicio")
                    siguiente_item = ruta_items[i + 1]
                    if produccion_acumulada[i] >= siguiente_item.estandar:
                        # El siguiente proceso puede comenzar inmediatamente
                        next_available_start = interval['fecha_fin']
                    else:
                        # Esperar al siguiente día si no hay suficientes unidades
                        next_day = get_next_working_day(interval['fecha_fin'].date())
                        next_available_start = datetime.combine(next_day, time(7, 45))
                else:
                    # Si no podemos continuar en el mismo día
                    next_day = get_next_working_day(interval['fecha_fin'].date())
                    next_available_start = datetime.combine(next_day, time(7, 45))

        groups.append(ot_group)

    return {
        "groups": groups,
        "items": items
    }
            #if dates_data['intrevals'] and maquina_id is not None:
             #   process_timeline[maquina_id] = dates_data['intervals'][-1]['fecha_fin']

class UpdatePriorityView(APIView):
    def put(self, request, pk): 
        try:
            # Log de los datos recibidos
            print("Datos recibidos:", request.data)
            
            programa = ProgramaProduccion.objects.get(id=pk)
            order_data = request.data.get("order_ids", [])
            recalculate_dates = request.data.get("recalculate_dates", False)

            if not isinstance(order_data, list):
                return Response(
                    {"error": "Formato incorrecto. 'order_ids' debe ser una lista de IDs."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            #Si solo es reordenamiento, usar método específico
            if not recalculate_dates:
                return self.handle_reorder(programa, order_data) 

            #Si hay recálculo de fechas, usar método existente
            return self.handle_update_with_recalculation(programa, order_data)

        except ProgramaProduccion.DoesNotExist:
            return Response(
                {'error': f'El programa con ID {pk} no existe.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
            return Response({
                "message": "Error al actualizar las prioridades y estándares.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def handle_reorder(self, programa, order_data):
        """Maneja solo el reordenamiento de prioridades"""

        try:
            with transaction.atomic():
                for index, order in enumerate(order_data):
                        prog_ot = ProgramaOrdenTrabajo.objects.get(
                            programa=programa,
                        orden_trabajo_id=order['id']
                        )
                        prog_ot.prioridad = index + 1
                        prog_ot.save()
                    
            # Actualizar fecha_fin después de los cambios
            programa.actualizar_fecha_fin()
            programa.refresh_from_db()

            #Obtener datos actualizados
            program_ots = ProgramaOrdenTrabajo.objects.filter(
                programa=programa
            ).select_related(
                'orden_trabajo'
            ).order_by('prioridad')

            ordenes_trabajo = []
            for prog_ot in program_ots:
                ot = prog_ot.orden_trabajo
                ordenes_trabajo.append({
                    'orden_trabajo': ot.id,
                    'orden_trabajo_codigo_ot': ot.codigo_ot,
                    'orden_trabajo_descripcion_producto_ot': ot.descripcion_producto_ot
                })
            
            return Response({
                "message": "Prioridades actualizadas correctamente",
                "ordenes_trabajo": ordenes_trabajo
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            print(f"Error en handle_reorder: {str(e)}")
            return Response({
                "error": f"Error al reordenar: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def handle_process_updates(self, order_data):
        """Maneja las actualizaciones de máquinas y estándares de los procesos."""
        success = {'updated': 0, 'errors': 0}
        error_details = []

        try:
            for proceso in order_data.get('procesos', []):
                proceso_id = proceso.get('id')
                maquina_id = proceso.get('maquina_id')
                estandar = proceso.get('estandar')

                try:
                    item_ruta = ItemRuta.objects.get(id=proceso_id)

                    #Actualizar máquina si viene en los datos
                    if maquina_id is not None:
                        try:
                            maquina = Maquina.objects.get(id=maquina_id)
                            item_ruta.maquina = maquina
                        except Maquina.DoesNotExist:
                            error_details.append(f'Maquina {maquina_id} no encontrada')
                            success['errors'] += 1
                            continue

                    #Actualizar estándar si viene en los datos
                    if estandar is not None:
                        item_ruta.estandar = estandar

                    item_ruta.save()
                    success['updated'] += 1
                    print(f'ItemRuta {proceso_id} actualizado correctamente')

                except ItemRuta.DoesNotExist:
                    error_details.append(f'ItemRuta {proceso_id} no encontrado')
                    success['errors'] += 1
                except Exception as e:
                    error_details.append(f'Error al actualizar ItemRuta {proceso_id}: {str(e)}')
                    success['errors'] += 1
        except Exception as e:
            error_details.append(f'Error al actualizar ItemRuta {proceso_id}: {str(e)}')
            success['errors'] += 1

        return {
            'success': success,
            'error_details': error_details
        }

    def handle_update_with_recalculation(self, programa, order_data):
        """Maneja actualizaciones que requieren recálculo de fechas"""
        success = {'updated': 0, 'errors': 0}
        error_details = []

        try:
            with transaction.atomic():
                for order in order_data:
                    try:
                        print(f"Procesando orden: {order}")
                        prog_ot = ProgramaOrdenTrabajo.objects.get(
                            programa=programa,
                            orden_trabajo_id=order['id']
                        )
                        prog_ot.prioridad = order['priority']
                        prog_ot.save()
                        success['updated'] += 1

                         # Procesar los cambios en los procesos
                        if 'procesos' in order:
                            for proceso in order['procesos']:
                                try:
                                    # Obtener el ItemRuta correspondiente
                                    item_ruta = ItemRuta.objects.get(id=proceso['id'])
                                    
                                    # Actualizar el estándar si viene en los datos
                                    if 'estandar' in proceso and proceso['estandar'] is not None:
                                        print(f"Actualizando estándar para proceso {proceso['id']}: {proceso['estandar']}")
                                        item_ruta.estandar = proceso['estandar']

                                    # Actualizar la máquina si viene en los datos
                                    if 'maquina_id' in proceso and proceso['maquina_id']:
                                        try:
                                            maquina = Maquina.objects.get(id=proceso['maquina_id'])
                                            item_ruta.maquina = maquina
                                        except Maquina.DoesNotExist:
                                            error_details.append(f"Máquina {proceso['maquina_id']} no encontrada")
                                            success['errors'] += 1

                                    # Guardar los cambios
                                    item_ruta.save()
                                    print(f"ItemRuta {proceso['id']} actualizado correctamente")

                                except ItemRuta.DoesNotExist:
                                    error_details.append(f"ItemRuta {proceso['id']} no encontrado")
                                    success['errors'] += 1
                                except Exception as e:
                                    error_details.append(f"Error al actualizar ItemRuta {proceso['id']}: {str(e)}")
                                    success['errors'] += 1
                    
                    except ProgramaOrdenTrabajo.DoesNotExist as e:
                        error_details.append(f"ProgramaOrdenTrabajo no encontrado para orden {order['id']}")
                        success['errors'] += 1
                    except Exception as e:
                        error_details.append(f"Error procesando orden {order['id']}: {str(e)}")
                        success['errors'] += 1

                
                try:
                    #Obtener datos actualizados de las OTs
                    programa_ots = ProgramaOrdenTrabajo.objects.filter(
                        programa=programa
                    ).select_related(
                        'orden_trabajo',
                        'orden_trabajo__ruta_ot'
                    ).prefetch_related(
                        'orden_trabajo__ruta_ot__items',
                        'orden_trabajo__ruta_ot__items__proceso',
                        'orden_trabajo__ruta_ot__items__maquina',
                    ).order_by('prioridad')

                    ordenes_trabajo = []
                    for prog_ot in programa_ots:
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
                                ot_data['procesos'].append({
                                    'id': item.id,
                                    'item': item.item,
                                    'codigo_proceso': item.proceso.codigo_proceso,
                                    'descripcion': item.proceso.descripcion,
                                    'maquina_id': item.maquina.id if item.maquina else None,
                                    'cantidad': item.cantidad_pedido,
                                    'estandar': item.estandar
                                })
                        ordenes_trabajo.append(ot_data)

                    try:
                        routes_data = generate_routes_data(programa)
                    except Exception as route_error:
                        print(f"Error al generar routes_data: {str(route_error)}")
                        routes_data = None
                        error_details.append(f"Error al generar datos de rutas: {str(route_error)}")

                    #Recalcular fecha_fin del programa
                    programa.actualizar_fecha_fin()
                    programa.refresh_from_db()

                    return Response({
                        "message": "Prioridades actualizadas correctamente",
                        "result": success,
                        "error_details": error_details,
                        "routes_data": routes_data,
                        "ordenes_trabajo": ordenes_trabajo
                    }, status=status.HTTP_200_OK)
                
                except Exception as e:
                    error_details.append(f"Error al procesar datos actualizados: {str(e)}")
                    return Response({
                        "error": f"Error en actualización con recálculo: {str(e)}",
                        "error_details": error_details
                    }, status=status.HTTP_500_INTERVAL_SERVER_ERROR)

        except Exception as e:
            print(f"Error en handle_update_with_recalculation: {str(e)}")
            return Response({
                "error": f"Error en actualización con recálculo: {str(e)}",
                "error details": error_details
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update_prio(self, pk, order_ids):
        success = {'success': 0, 'updated': 0, 'errors': 0}
        try:
            programa = ProgramaProduccion.objects.get(id=pk)
        except ProgramaProduccion.DoesNotExist:
            return {"error": f"El programa con ID {pk} no existe."}

        # Obtener las órdenes de trabajo asociadas al programa
        programas_ot = ProgramaOrdenTrabajo.objects.filter(programa=programa, orden_trabajo__id__in=order_ids)

        for idx, order_id in enumerate(order_ids):
            # Verificar si la orden de trabajo está asociada al programa
            prog_ot = programas_ot.filter(orden_trabajo__id=order_id).first()
            if prog_ot:
                prog_ot.prioridad = idx + 1  # Actualizar prioridad
                prog_ot.save()
                success['updated'] += 1
            else:
                success['errors'] += 1  # Orden de trabajo no encontrada en el programa

        if success['errors']:
            return {"message": "Algunas prioridades no se actualizaron correctamente.", "result": success}
        
        return {"message": "Prioridades actualizadas correctamente.", "result": success}
    
    def delete(self, request, pk):
        order_ids = request.data.get("order_ids", [])
        print(f"Recibiendo solicitud de eliminación para order_ids: {order_ids}")
        
        if not isinstance(order_ids, list):
            return Response(
                {"error": "Formato incorrecto. 'order_ids' debe ser una lista de IDs."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            programa = ProgramaProduccion.objects.get(id=pk)
            print(f"Programa encontrado: {programa}")
        except ProgramaProduccion.DoesNotExist:
            return Response(
                {"error": f"El programa con ID {pk} no existe."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        success = {'deleted': 0, 'errors': 0}
        errores = {'descripcion':''}
        for order_id in order_ids:
            try:
                print(f"Buscando ProgramaOrdenTrabajo con programa_id={pk} y orden_trabajo_id={order_id}")
                prog_ot = ProgramaOrdenTrabajo.objects.get(
                    programa=programa, 
                    orden_trabajo__id=order_id
                )
                print(f"ProgramaOrdenTrabajo encontrado: {prog_ot}")
                prog_ot.delete()
                print(f"ProgramaOrdenTrabajo eliminado exitosamente")
                success['deleted'] += 1
            except ProgramaOrdenTrabajo.DoesNotExist:
                print(f"No se encontró ProgramaOrdenTrabajo para orden_trabajo_id={order_id}")
                success['errors'] += 1
                errores['descripcion'] = f"No se encontró ProgramaOrdenTrabajo para orden_trabajo_id={order_id}"
            except Exception as e:
                print(f"Error inesperado al eliminar orden: {str(e)}")
                success['errors'] += 1
                errores['descripcion'] = f"Error inesperado al eliminar orden: {str(e)}"

        print(f"Resultado final: {success}")
        print(f"Errores: {errores}")
        return Response({
            "message": "Órdenes procesadas", 
            "result": success,
            "errors": errores
        }, status=status.HTTP_200_OK)

class ProgramDetailView(APIView):
    def get_procesos_con_asignaciones(self, programa_id):
        """Obtiene los procesos y sus asignaciones de operadores para un programa especifico. Retorna un diccionario con la información de asignaciones por proceso."""
        try:
            # Obtener todas las asignaciones para el programa
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
        """Obtiene los detalles de un programa con sus asignaciones"""
        try:
            self.programa_id = pk
            programa = ProgramaProduccion.objects.get(id=pk)

            #Actualizar fecha_fin 
            fecha_fin = self.calculate_program_end_date(programa)
            if fecha_fin != programa.fecha_fin:
                programa.fecha_fin = fecha_fin
                programa.save(update_fields=['fecha_fin'])
                programa.refresh_from_db()
            

            serializer = ProgramaProduccionSerializer(programa)

            # Obtener las asignaciones y verificar su contenido
            asignaciones_por_item = self.get_procesos_con_asignaciones(pk)
            ordenes_trabajo = self.get_ordenes_trabajo(programa)

            #Agregar asignaciones a los procesos
            for ot in ordenes_trabajo:
                for proceso in ot['procesos']:
                    if proceso['id'] in asignaciones_por_item:
                        proceso['asignacion'] = asignaciones_por_item[proceso['id']]
            
            response_data = {
                "program": serializer.data,
                "ordenes_trabajo": ordenes_trabajo,
                "routes_data": self.generate_timeline_data(programa, ordenes_trabajo)
            }

            return Response(response_data, status=status.HTTP_200_OK)
        
        except ProgramaProduccion.DoesNotExist:
            return Response(
                {'error': 'Programa no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error interno del servidor: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @transaction.atomic
    def post(self, request, pk):
        """Crea una nueva asignación de operador"""
        try:
            programa = ProgramaProduccion.objects.get(id=pk)
            data = request.data
            
            #Validar datos requeridos
            required_fields = ['operador_id', 'item_ruta_id', 'fecha_inicio', 'fecha_fin']
            if not all(field in data for field in required_fields):
                return Response(
                    {'error': 'Faltan campos requeridos'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            #Obtener y validar objetos relacionados
            try:
                operador = Operador.objects.get(id=data['operador_id'])
                item_ruta = ItemRuta.objects.select_related(
                    'proceso',
                    'maquina',
                    'ruta'
                ).get(id=data['item_ruta_id'])

                # Verificar si ya existe una asignación para este item_ruta en este programa
                existing_assignment = AsignacionOperador.objects.filter(
                    programa=programa,
                    item_ruta=item_ruta
                ).first()

                if existing_assignment:
                    # Si existe, actualizarla
                    existing_assignment.operador = operador
                    existing_assignment.fecha_inicio = parse_datetime(data['fecha_inicio'])
                    existing_assignment.fecha_fin = parse_datetime(data['fecha_fin'])
                    existing_assignment.save()
                    asignacion = existing_assignment
                else:
                    # Si no existe, crear una nueva
                    asignacion = AsignacionOperador(
                        operador=operador,
                        item_ruta=item_ruta,
                        programa=programa,
                        fecha_inicio=parse_datetime(data['fecha_inicio']),
                        fecha_fin=parse_datetime(data['fecha_fin'])
                    )
                    asignacion.full_clean()
                    asignacion.save()

                # Recalcular asignaciones posteriores
                asignacion.recalcular_asignaciones_posteriores()

                return Response({
                    'message': 'Asignación creada exitosamente',
                    'id': asignacion.id,
                }, status=status.HTTP_201_CREATED)

            except (Operador.DoesNotExist, ItemRuta.DoesNotExist) as e:
                return Response(
                    {'error': f'Objeto no encontrado: {str(e)}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except ValidationError as e:
                return Response(
                    {'error': f'Error de validación: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except Exception as e:
            print(f"Error al procesar la asignación: {str(e)}")
            return Response(
                {'error': f'Error al procesar la asignación: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def generate_timeline_data(self, programa, ordenes_trabajo):
        groups = []
        items = []
        hay_estandar_cero = False
        operador_timeline = {}  # Para rastrear el último uso de cada operador
        
        for ot_data in ordenes_trabajo:
            try:
                ot_id = ot_data['orden_trabajo']
                ot_codigo = ot_data['orden_trabajo_codigo_ot']
                ot_descripcion = ot_data['orden_trabajo_descripcion_producto_ot']
                procesos = ot_data.get('procesos', [])

                if not procesos:
                    continue

                ot_group = {
                    "id": f"ot_{ot_id}",
                    "orden_trabajo_codigo_ot": ot_codigo,
                    "descripcion": ot_descripcion,
                    "procesos": []
                }

                fecha_inicio = ot_data.get('fecha_emision') or ot_data.get('fecha_proc') or programa.fecha_inicio
                next_available_start = datetime.combine(fecha_inicio, time(7, 45))

                for proceso in procesos:
                    proceso_id = f"proc_{proceso['id']}"
                    ot_group["procesos"].append({
                        "id": proceso_id,
                        "descripcion": proceso.get('descripcion', 'Sin descripción'),
                        "item": proceso.get('item', 0)
                    })

                    estandar = float(proceso.get('estandar', 0))
                    if estandar <= 0:
                        hay_estandar_cero = True
                        continue

                    cantidad = float(proceso.get('cantidad', 0))
                    if cantidad <= 0:
                        continue

                    # Verificar si el proceso tiene una asignación existente
                    asignacion = proceso.get('asignacion')
                    if asignacion:
                        operador_id = asignacion.get('operador_id')
                        # Ajustar fecha de inicio basada en la última asignación del operador
                        if operador_id in operador_timeline:
                            ultima_fecha = operador_timeline[operador_id]
                            next_available_start = max(next_available_start, ultima_fecha)
                            
                            # Si la nueva fecha de inicio cae en horario de almuerzo, ajustar
                            if time(13, 0) <= next_available_start.time() < time(14, 0):
                                next_available_start = datetime.combine(next_available_start.date(), time(14, 0))

                    # Calcular intervalos considerando el next_available_start
                    dates_data = self.calculate_working_days(
                        next_available_start,
                        cantidad,
                        estandar
                    )

                    # Crear items para cada intervalo
                    for idx, interval in enumerate(dates_data['intervals']):
                        timeline_item = {
                            "id": f'item_{proceso["id"]}_{idx}',
                            "ot_id": f"ot_{ot_id}",
                            "proceso_id": proceso_id,
                            "name": f"{proceso.get('descripcion', 'Proceso')} - {interval['unidades']:.0f} de {cantidad:.0f} unidades",
                            "start_time": interval['fecha_inicio'].strftime('%Y-%m-%d %H:%M:%S'),
                            "end_time": interval['fecha_fin'].strftime('%Y-%m-%d %H:%M:%S'),
                            "cantidad_total": cantidad,
                            "cantidad_intervalo": float(interval['unidades']),
                            "unidades_restantes": float(interval['unidades_restantes']),
                            "estandar": estandar
                        }

                        # Agregar información de asignación
                        if asignacion:
                            timeline_item.update({
                                "asignacion_id": asignacion.get('id'),
                                "operador_id": asignacion.get('operador_id'),
                                "operador_nombre": asignacion.get('operador_nombre'),
                                "asignado": True
                            })
                            # Actualizar el timeline del operador
                            operador_timeline[asignacion.get('operador_id')] = interval['fecha_fin']
                        else:
                            timeline_item.update({
                                "asignacion_id": None,
                                "operador_id": None,
                                "operador_nombre": None,
                                "asignado": False
                            })

                        items.append(timeline_item)

                    # Actualizar fecha de inicio para el siguiente proceso
                    next_available_start = dates_data['next_available_time']

                if ot_group["procesos"]:
                    groups.append(ot_group)

            except Exception as e:
                print(f"Error generando timeline para OT {ot_id}: {str(e)}")
                continue

        return {
            "groups": groups,
            "items": items,
            "error": "Hay procesos con estándar 0. Por favor, corrija los valores antes de proyectar." if hay_estandar_cero else None
        }
    
    def calculate_working_days(self, start_date, cantidad, estandar):
        if not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, time(7, 45))

        if not estandar or estandar <= 0:
        # En lugar de usar un valor predeterminado, devolver un error o un resultado vacío
            return {
                'intervals': [],
                'start_date': start_date.date() if isinstance(start_date, datetime) else start_date,
                'end_date': start_date.date() if isinstance(start_date, datetime) else start_date,
                'next_available_time': start_date,
                'error': 'El estándar debe ser mayor que 0'
            }
    

        current_date = start_date.date()
        current_datetime = start_date
        remaining_units = float(cantidad)
        intervals = []

        # Definir horario laboral
        WORKDAY_START = time(7, 45)
        WORKDAY_END = time(17, 45)
        
        # Añadir definición de hora de descanso
        BREAK_START = time(13, 0)
        BREAK_END = time(14, 0)
        
        # El estándar ya tiene valor hora
        estandar_hora = float(estandar) 
        # Si la fecha inicial no es día laboral, mover al siguiente dia laboral
        if not is_working_day(current_date):
            next_day = get_next_working_day(current_date)
            current_datetime = datetime.combine(next_day, WORKDAY_START)
            current_date = current_datetime.date()

        while remaining_units > 0:
            # Si no es día laboral, pasar al siguiente
            if not is_working_day(current_date):
                next_day = get_next_working_day(current_date)
                current_datetime = datetime.combine(next_day, WORKDAY_START)
                current_date = current_datetime.date()
                continue

            # Ajustar current_datetime si está fuera del horario laboral
            if current_datetime.time() < WORKDAY_START:
                current_datetime = datetime.combine(current_date, WORKDAY_START)
            elif current_datetime.time() > WORKDAY_END:
                next_day = get_next_working_day(current_date + timedelta(days=1))
                current_datetime = datetime.combine(next_day, WORKDAY_START)
                current_date = current_datetime.date()
                continue

            # Procesar por horas
            hora_actual = current_datetime
            while hora_actual.time() < WORKDAY_END and remaining_units > 0:
                # Si estamos en la hora de descanso, saltar a la siguiente hora
                if BREAK_START <= hora_actual.time() < BREAK_END:
                    hora_actual = datetime.combine(current_date, BREAK_END)
                    continue

                # Calcular el fin del intervalo actual (próxima hora o límite)
                next_hour = (hora_actual + timedelta(hours=1)).replace(minute=0, second=0)
                if next_hour.time() > WORKDAY_END:
                    next_hour = datetime.combine(current_date, WORKDAY_END)
                if hora_actual.time() < BREAK_START and next_hour.time() > BREAK_START:
                    next_hour = datetime.combine(current_date, BREAK_START)

                # Calcular unidades para esta hora
                hours_in_interval = (next_hour - hora_actual).total_seconds() / 3600
                units_this_interval = min(remaining_units, hours_in_interval * estandar_hora)

                if units_this_interval > 0:
                    #Verificar si este intervalo completa el estándar por hora
                    is_full_capacity = units_this_interval >= (estandar_hora * hours_in_interval
                                                               )
                    interval = {
                        'fecha': current_date,
                        'fecha_inicio': hora_actual,
                        'fecha_fin': next_hour,
                        'unidades': units_this_interval,
                        'unidades_restantes': remaining_units - units_this_interval,
                        'continue_same_day': next_hour.time() < WORKDAY_END and next_hour.time() != BREAK_START
                    }
                    intervals.append(interval)
                    remaining_units -= units_this_interval

                hora_actual = next_hour

            # Si quedan unidades, preparar para el siguiente día
            if remaining_units > 0:
                last_interval = intervals[-1] if intervals else None
                if last_interval and last_interval['continue_same_day']:
                    #Continuar desde la ultima hora de fin
                    current_datetime = last_interval['fecha_fin']
                else:
                    next_day = get_next_working_day(current_date)
                    current_datetime = datetime.combine(next_day, WORKDAY_START)
                    current_date = current_datetime.date()

        # Mantener el formato de retorno existente
        return {
            'intervals': intervals,
            'start_date': intervals[0]['fecha'] if intervals else current_date,
            'end_date': intervals[-1]['fecha'] if intervals else current_date,
            'next_available_time': intervals[-1]['fecha_fin'] if intervals else current_datetime
        }
    
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
        """Formatea una orden de trabajo para la respuesta API"""
        try:
            # Usar el programa_id pasado como parámetro o el atributo de la clase
            programa_id = programa_id or getattr(self, 'programa_id', None)
            
            if not programa_id:
                print(f"Advertencia: No se proporcionó programa_id para la orden {orden_trabajo.id}")
            
            ot_data = {
                'orden_trabajo': orden_trabajo.id,
                'orden_trabajo_codigo_ot': orden_trabajo.codigo_ot,
                'orden_trabajo_descripcion_producto_ot': orden_trabajo.descripcion_producto_ot,
                'procesos': []
            }
            
            # Obtener la ruta y sus procesos
            ruta = getattr(orden_trabajo, 'ruta_ot', None)
            if ruta:
                for item in ruta.items.all().order_by('item'):
                    # Obtener asignación de operador si existe
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
        
    def calculate_program_end_date(self, programa, ordenes_trabajo=None):
        """Calcula la fecha de fin del programa basada en el último item del timeline."""
        try:
            # Si no se proporcionan órdenes de trabajo, obtenerlas del programa
            if ordenes_trabajo is None:
                ordenes_trabajo = self.get_ordenes_trabajo(programa)

            # Generar datos del timeline usando el método de la clase
            timeline_data = self.generate_timeline_data(programa, ordenes_trabajo)
            
            # Si no hay items en el timeline, retornar la fecha de inicio
            if not timeline_data.get('items'):
                print("No se encontraron items en el timeline")
                return programa.fecha_inicio

            # Buscar la fecha de fin más tardía entre todos los items
            latest_end_time = None
            for item in timeline_data['items']:
                try:
                    end_time = datetime.strptime(item['end_time'], '%Y-%m-%d %H:%M:%S')
                    if latest_end_time is None or end_time > latest_end_time:
                        latest_end_time = end_time
                        print(f"Nueva fecha fin encontrada: {latest_end_time}")
                except (KeyError, ValueError) as e:
                    print(f"Error procesando item del timeline: {str(e)}")
                    continue

            # Si encontramos una fecha válida y es posterior a la fecha de inicio, retornarla
            if latest_end_time and latest_end_time.date() > programa.fecha_inicio:
                print(f"Fecha fin calculada: {latest_end_time.date()}")
                return latest_end_time.date()

            print(f"No se encontró fecha fin posterior a la fecha de inicio: {programa.fecha_inicio}")
            return programa.fecha_inicio

        except Exception as e:
            print(f"Error calculando fecha fin del programa: {str(e)}")
            return programa.fecha_inicio


class MaquinasView(APIView):
    def get(self, request, pk=None):
        print(f"\n[Backend] MaquinasView: Recibida solicitud para programa_id={pk}")
        print(f"[Backend] Query params: {request.query_params}")
        
        try:
            programa = ProgramaProduccion.objects.get(pk=pk)
            print(f"[Backend] Programa encontrado: {programa}")
            
            # Obtener el código del proceso de los query params
            proceso_codigo = request.query_params.get('proceso_codigo')
            print(f"[Backend] Código de proceso recibido: {proceso_codigo}")
            
            # Base query para máquinas
            maquinas = Maquina.objects.filter(
                Q(empresa__isnull=False)
            ).distinct()
            print(f"[Backend] Total de máquinas iniciales: {maquinas.count()}")

            # Si hay proceso_codigo, filtrar por máquinas compatibles
            if proceso_codigo:
                try:
                    proceso = Proceso.objects.get(codigo_proceso=proceso_codigo)
                    print(f"[Backend] Proceso encontrado: {proceso}")
                    
                    maquinas_compatibles = proceso.get_maquinas_compatibles()
                    print(f"[Backend] Máquinas compatibles: {maquinas_compatibles.count()}")
                    
                    maquinas = maquinas_compatibles.filter(id__in=maquinas)
                    print(f"[Backend] Máquinas filtradas: {maquinas.count()}")
                    
                except Proceso.DoesNotExist:
                    print(f"[Backend] ERROR: Proceso con código {proceso_codigo} no encontrado")
                    # Si no se encuentra el proceso, simplemente devolver todas las máquinas
                    # sin generar un error 404
                    pass
            # Ordenar por código
            maquinas = maquinas.order_by('codigo_maquina')
            
            serializer = MaquinaSerializer(maquinas, many=True)
            print(f"[Backend] Enviando {len(serializer.data)} máquinas en respuesta")
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ProgramaProduccion.DoesNotExist:
            print(f"[Backend] ERROR: Programa con ID {pk} no encontrado")
            return Response(
                {'error':'Programa no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"[Backend] ERROR general: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['GET'])
def get_unassigned_ots(request):
    """
    Obtiene todas las órdenes de trabajo que no están asignadas a ningún programa de producción.
    """
    try:
        # Filtra órdenes de trabajo que no están relacionadas con ningún programa
        ordenes_unassigned = OrdenTrabajo.objects.filter(
            ~Q(id__in=ProgramaOrdenTrabajo.objects.values_list('orden_trabajo_id', flat=True))
        )

        # Serializa las órdenes no asignadas
        serializer = OrdenTrabajoSerializer(ordenes_unassigned, many=True)

        return Response(serializer.data, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

#Configurar logger 
logger = logging.getLogger(__name__)
class GenerateProgramPDF(APIView):
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

            # Si no hay asignación, usar la lógica del timeline
            program_detail_view = ProgramDetailView()
            
            # Obtener las órdenes de trabajo ordenadas por prioridad
            program_ots = ProgramaOrdenTrabajo.objects.filter(
                programa=programa
            ).select_related(
                'orden_trabajo'
            ).order_by('prioridad')

            # Encontrar la OT que contiene este item_ruta
            for prog_ot in program_ots:
                ot = prog_ot.orden_trabajo
                ruta = getattr(ot, 'ruta_ot', None)
                if not ruta:
                    continue

                # Si encontramos el item_ruta en esta OT
                if item_ruta.ruta_id == ruta.id:
                    # Formatear la OT para el timeline
                    ot_data = program_detail_view.format_orden_trabajo(ot, programa.id)
                    
                    # Generar datos del timeline para esta OT
                    timeline_data = program_detail_view.generate_timeline_data(programa, [ot_data])
                    
                    # Buscar los intervalos correspondientes a este proceso
                    if timeline_data.get('items'):
                        proceso_items = [
                            item for item in timeline_data['items'] 
                            if item['proceso_id'] == f"proc_{item_ruta.id}"
                        ]
                        
                        if proceso_items:
                            # Tomar la fecha de inicio del primer intervalo y la fecha fin del último
                            fecha_inicio = datetime.strptime(proceso_items[0]['start_time'], '%Y-%m-%d %H:%M:%S')
                            fecha_fin = datetime.strptime(proceso_items[-1]['end_time'], '%Y-%m-%d %H:%M:%S')
                            
                            return {
                                'fecha_inicio': fecha_inicio,
                                'fecha_fin': fecha_fin
                            }

            # Si no se encontraron fechas válidas
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
                        fecha_inicio_str = proceso.get('fecha_inicio').strftime('%d/%m/%Y') if proceso.get('fecha_inicio') else 'No definida'
                        fecha_fin_str = proceso.get('fecha_fin').strftime('%d/%m/%Y') if proceso.get('fecha_fin') else 'No definida'
                        
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

class MaquinaListView(APIView):
    def get(self, request):
        """Obtener lista de todas las máquinas"""
        maquinas = Maquina.objects.all()
        serializer = MaquinaSerializer(maquinas, many=True)
        return Response(serializer.data)

class EmpresaListView(APIView):
    def get(self, request):
        empresas = EmpresaOT.objects.all()
        serializer = EmpresaOTSerializer(empresas, many=True)
        return Response(serializer.data)

class ProcesoTimelineView(APIView):
    """Obtiene las fechas del timeline para un proceso específico"""
    permission_classes = [IsAuthenticated]

    def get(self, request, programa_id, proceso_id):
        try:
            print(f"[Backend] Obteniendo fechas de timeline para programa_id={programa_id}, y proceso_id={proceso_id}")

            #Obtener el programa
            programa = get_object_or_404(ProgramaProduccion, pk=programa_id)

            #Obtener el item_ruta
            item_ruta = get_object_or_404(ItemRuta, pk=proceso_id)

            #Obtener la orden de trabajo asociada
            orden_trabajo = item_ruta.ruta.orden_trabajo

            #Calcular fechas basadas en el estándar y la cantidad
            estandar = float(item_ruta.estandar if item_ruta.estandar >0 else 500)
            cantidad = float(item_ruta.cantidad_pedido)

            #Obtener la fecha de inicio del programa

            fecha_inicio_programa = programa.fecha_inicio

            #Calcular días de trabajo usando la misma lógica que el timeline
            program_detail_view = ProgramDetailView()
            dates_data = program_detail_view.calculate_working_days(
                fecha_inicio_programa,
                cantidad,
                estandar
            )

            #Obtener la primera fecha de inicio y la ultima fecha de fin
            if dates_data['intervals']:
                fecha_inicio = dates_data['intervals'][0]['fecha_inicio']
                fecha_fin = dates_data['intervals'][-1]['fecha_fin']
                
                return Response({
                    'proceso_id': proceso_id,
                    'fecha_inicio': fecha_inicio.isoformat(),
                    'fecha_fin': fecha_fin.isoformat(),
                    'intervals':[
                        {
                            'fecha_inicio': interval['fecha_inicio'].isoformat(),
                            'fecha_fin': interval['fecha_fin'].isoformat(),
                            'unidades': interval['unidades'],
                            'unidades_restantes': interval['unidades_restantes']
                        } for interval in dates_data['intervals']
                    ]
                })
            else: 
                return Response(
                    {'error': 'No se pudieron calcular intervalos de trabajo'},
                    status=status.HTTP_400_BAD_REQUEST
                    )

        except Exception as e:
            print(f'[Backend] Error al obtener fechas de timeline: {str(e)}')
            return Response(
                {'error': f'Error al obtener fechas de timeline: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProcesoDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            proceso = Proceso.objects.get(pk=pk)
            data = {
                'id': proceso.id,
                'codigo_proceso': proceso.codigo_proceso,
                'descripcion': proceso.descripcion,
                'tipos_maquina_compatibles': [{
                    'id': tipo.id,
                    'codigo': tipo.codigo,
                    'descripcion': tipo.descripcion,
                } for tipo in proceso.tipos_maquina_compatibles.all()]
            }
            return Response(data)
        except Proceso.DoesNotExist:
            return Response(
                {'error': 'Proceso no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

class ProcesoListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            procesos = Proceso.objects.all().prefetch_related('tipos_maquina_compatibles')
            data = [{
                'id': proceso.id,
                'codigo_proceso': proceso.codigo_proceso,
                'descripcion': proceso.descripcion,
                'tipos_maquina_compatibles': [{
                    'id': tipo.id,
                    'codigo': tipo.codigo,
                    'descripcion': tipo.descripcion,
                } for tipo in proceso.tipos_maquina_compatibles.all()]
            } for proceso in procesos]
            return Response(data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SupervisorReportView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            programa = get_object_or_404(ProgramaProduccion, id=pk)
            
            programa_info = {
                'id': programa.id,
                'nombre': programa.nombre,
                'fecha_inicio': programa.fecha_inicio.strftime('%Y-%m-%d'),
                'fecha_fin': programa.fecha_fin.strftime('%Y-%m-%d') if programa.fecha_fin else None
            }

            # Obtener datos del timeline para agrupar tareas por día
            program_detail_view = ProgramDetailView()
            timeline_data = program_detail_view.generate_timeline_data(
                programa,
                program_detail_view.get_ordenes_trabajo(programa)
            )

            tareas_agrupadas = {}
            total_kilos_programados = 0

            # Obtener todos los reportes diarios para este programa
            reportes_diarios = ReporteDiario.objects.filter(
                programa=programa
            ).select_related(
                'item_ruta'
            ).order_by('fecha', 'created_at')

            # Crear un diccionario para acceder fácilmente a los reportes por proceso_id y fecha
            reportes_por_proceso = defaultdict(list)
            for reporte in reportes_diarios:
                clave = f"{reporte.item_ruta.id}_{reporte.fecha.strftime('%Y-%m-%d')}"
                reportes_por_proceso[clave].append(ReporteDiarioSerializer(reporte).data)

            # Procesar los items del timeline y agruparlos por día
            for item in timeline_data.get('items', []):
                try:
                    fecha_inicio = datetime.strptime(item['start_time'], '%Y-%m-%d %H:%M:%S')
                    
                    if programa.fecha_inicio <= fecha_inicio.date() <= programa.fecha_fin:
                        proceso_id = item['proceso_id'].replace('proc_', '')
                        clave = f"{item['ot_id']}_{proceso_id}"
                        
                        if clave not in tareas_agrupadas:
                            try:
                                item_ruta = ItemRuta.objects.select_related(
                                    'proceso',
                                    'maquina',
                                    'ruta__orden_trabajo'
                                ).get(id=proceso_id)

                                # Calcular kilos programados
                                peso_unitario = float(item_ruta.ruta.orden_trabajo.peso_unitario or 0)
                                kilos_programados = peso_unitario * float(item['cantidad_total'])
                                total_kilos_programados += kilos_programados

                                # Obtener el último reporte para esta fecha y proceso
                                clave_reporte = f"{proceso_id}_{fecha_inicio.strftime('%Y-%m-%d')}"
                                reportes = reportes_por_proceso.get(clave_reporte, [])
                                ultimo_reporte = reportes[-1] if reportes else None

                                # Crear la tarea con la fecha del programa
                                tarea = {
                                    'id': item['id'],
                                    'ot_codigo': item_ruta.ruta.orden_trabajo.codigo_ot,
                                    'proceso': item_ruta.proceso.descripcion,
                                    'maquina': {
                                        'id': item_ruta.maquina.id if item_ruta.maquina else None,
                                        'descripcion': item_ruta.maquina.descripcion if item_ruta.maquina else 'Sin máquina'
                                    },
                                    'operador': item.get('operador_nombre', 'Sin asignar'),
                                    'cantidad_programada': item['cantidad_total'],
                                    'kilos_programados': kilos_programados,
                                    'hora_inicio': fecha_inicio.strftime('%H:%M'),
                                    'hora_fin': datetime.strptime(item['end_time'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M'),
                                    'estado': ultimo_reporte['estado'] if ultimo_reporte else 'Pendiente',
                                    'observaciones': ultimo_reporte['observaciones'] if ultimo_reporte else '',
                                    'proceso_id': proceso_id,
                                    'fecha': fecha_inicio.strftime('%Y-%m-%d'),
                                    'kilos_fabricados': ultimo_reporte['kilos_fabricados'] if ultimo_reporte else 0,
                                    'porcentaje_cumplimiento': (float(ultimo_reporte['kilos_fabricados']) / kilos_programados * 100) if ultimo_reporte and kilos_programados > 0 else 0,
                                    'historial': reportes
                                }
                                #Info sobre quién realizó la asignación
                                from Operator.models import AsignacionOperador
                                asignacion = AsignacionOperador.objects.filter(
                                    item_ruta_id=proceso_id,
                                    programa_id=programa.id
                                ).first()

                                if asignacion and asignacion.asignado_por:
                                    tarea['asignado_por_nombre'] = f"{asignacion.asignado_por.first_name} {asignacion.asignado_por.last_name}".strip() or asignacion.asignado_por.username
                                    tarea['fecha_asignacion'] = asignacion.fecha_asignacion
                                else:
                                    tarea['asignado_por_nombre'] = None
                                    tarea['fecha_asignacion'] = None

                                tareas_agrupadas[clave] = tarea

                            except ItemRuta.DoesNotExist:
                                print(f"No se encontró ItemRuta para proceso_id: {proceso_id}")
                except Exception as e:
                    print(f"Error procesando item del timeline: {str(e)}")

            return Response({
                'programa': programa_info,
                'total_kilos_programados': total_kilos_programados,
                'tareas': list(tareas_agrupadas.values())
            })
        except Exception as e:
            print(f"Error general en SupervisorReportView: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, pk):
        """Actualiza los kilos fabricados sin duplicar registros"""
        try:
            programa = get_object_or_404(ProgramaProduccion, id=pk)
            data = request.data
            tarea_id = data.get('tarea_id')
            proceso_id = data.get('proceso_id')
            kilos_fabricados = float(data.get('kilos_fabricados', 0))
            estado = data.get('estado', 'Pendiente')
            fecha_actual = datetime.strptime(data.get('fecha'), '%Y-%m-%d')
            observaciones = data.get('observaciones', '')
            
            # Obtener el item_ruta
            item_ruta = ItemRuta.objects.select_related(
                'proceso', 'maquina', 'ruta__orden_trabajo'
            ).get(id=proceso_id)
            
            # Calcular unidades fabricadas
            peso_unitario = float(item_ruta.ruta.orden_trabajo.peso_unitario or 0)
            unidades_programadas = float(data.get('cantidad_programada', 0))
            unidades_fabricadas = kilos_fabricados / peso_unitario if peso_unitario > 0 else 0
            
            # Buscar si ya existe un reporte para este día y actualizar
            reporte_diario, created = ReporteDiario.objects.update_or_create(
                programa=programa,
                item_ruta=item_ruta,
                fecha=fecha_actual,
                defaults={
                    'estado': estado,
                    'kilos_fabricados': kilos_fabricados,
                    'unidades_fabricadas': unidades_fabricadas,
                    'observaciones': observaciones
                }
            )
            
            # Calcular unidades pendientes para eventos adicionales
            unidades_pendientes = unidades_programadas - unidades_fabricadas
            
            # Lógica adicional similar al método post actual...
            
            return Response({
                'message': 'Actualización exitosa',
                'kilos_fabricados': kilos_fabricados,
                'porcentaje_cumplimiento': (kilos_fabricados / (peso_unitario * unidades_programadas)) * 100 if peso_unitario > 0 else 0,
                'unidades_pendientes': unidades_pendientes,
                'siguiente_fecha': get_next_working_day(fecha_actual).strftime('%Y-%m-%d') if unidades_pendientes > 0 else None
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @transaction.atomic
    def post(self, request, pk):
        """Actualiza los kilos fabricados y recalcula el programa si es necesario"""
        try:
            programa = get_object_or_404(ProgramaProduccion, id=pk)
            data = request.data
            tarea_id = data.get('tarea_id')
            proceso_id = data.get('proceso_id')
            kilos_fabricados = float(data.get('kilos_fabricados', 0))
            estado = data.get('estado', 'Pendiente')
            fecha_actual = datetime.strptime(data.get('fecha'), '%Y-%m-%d')
            observaciones = data.get('observaciones', '')
            
            # Obtener el item_ruta y sus datos relacionados
            item_ruta = ItemRuta.objects.select_related(
                'proceso', 'maquina', 'ruta__orden_trabajo'
            ).get(id=proceso_id)
            
            peso_unitario = float(item_ruta.ruta.orden_trabajo.peso_unitario or 0)
            unidades_programadas = float(data.get('cantidad_programada', 0))
            unidades_fabricadas = kilos_fabricados / peso_unitario if peso_unitario > 0 else 0
            
            # Calcular unidades pendientes
            unidades_pendientes = unidades_programadas - unidades_fabricadas
            
            # Manejar diferentes estados
            if estado == 'Terminado':
                # No necesitamos recalcular nada si está terminado
                return Response({
                    'message': 'Tarea completada',
                    'kilos_fabricados': kilos_fabricados,
                    'porcentaje_cumplimiento': 100
                })
            
            elif estado in ['Pendiente', 'En Proceso', 'Detenido'] and unidades_pendientes > 0:
                # Obtener la siguiente fecha hábil
                siguiente_dia = get_next_working_day(fecha_actual)
                
                # Recalcular fechas para las unidades pendientes
                program_detail_view = ProgramDetailView()
                dates_data = program_detail_view.calculate_working_days(
                    datetime.combine(siguiente_dia, time(7, 45)),
                    unidades_pendientes,
                    item_ruta.estandar
                )
                
                # Actualizar el timeline con los nuevos intervalos
                if dates_data['intervals']:
                    # Aquí actualizamos las fechas en el programa
                    # Esto afectará a todas las tareas subsiguientes
                    self.recalcular_fechas_programa(
                        programa, 
                        item_ruta, 
                        dates_data['intervals'][0]['fecha_inicio'],
                        unidades_pendientes
                    )
            
            # Guardar el estado y las observaciones
            reporte_diario = ReporteDiario.objects.create(
                programa=programa,
                item_ruta=item_ruta,
                fecha=fecha_actual,
                estado=estado,
                kilos_fabricados=kilos_fabricados,
                unidades_fabricadas=unidades_fabricadas,
                observaciones=observaciones
            )
            
            return Response({
                'message': 'Actualización exitosa',
                'kilos_fabricados': kilos_fabricados,
                'porcentaje_cumplimiento': (kilos_fabricados / (peso_unitario * unidades_programadas)) * 100 if peso_unitario > 0 else 0,
                'unidades_pendientes': unidades_pendientes,
                'siguiente_fecha': siguiente_dia.strftime('%Y-%m-%d') if unidades_pendientes > 0 else None
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def recalcular_fechas_programa(self, programa, item_ruta_actual, nueva_fecha_inicio, unidades_pendientes):
        """Recalcula las fechas de todas las tareas posteriores"""
        try:
            # Obtener todas las tareas del programa ordenadas por prioridad
            program_ots = ProgramaOrdenTrabajo.objects.filter(
                programa=programa
            ).select_related(
                'orden_trabajo',
                'orden_trabajo__ruta_ot'
            ).prefetch_related(
                'orden_trabajo__ruta_ot__items'
            ).order_by('prioridad')

            fecha_actual = nueva_fecha_inicio
            tarea_encontrada = False

            for prog_ot in program_ots:
                ruta = prog_ot.orden_trabajo.ruta_ot
                if not ruta:
                    continue

                for item in ruta.items.all().order_by('item'):
                    # Una vez que encontramos la tarea actual, comenzamos a recalcular
                    if item.id == item_ruta_actual.id:
                        tarea_encontrada = True
                        # Actualizar la tarea actual con las unidades pendientes
                        dates_data = self.calculate_working_days(
                            fecha_actual,
                            unidades_pendientes,
                            item.estandar
                        )
                        if dates_data['intervals']:
                            fecha_actual = dates_data['next_available_time']
                    
                    elif tarea_encontrada:
                        # Recalcular todas las tareas posteriores
                        dates_data = self.calculate_working_days(
                            fecha_actual,
                            item.cantidad_pedido,
                            item.estandar
                        )
                        if dates_data['intervals']:
                            fecha_actual = dates_data['next_available_time']

            # Actualizar la fecha de fin del programa si es necesario
            if fecha_actual.date() > programa.fecha_fin:
                programa.fecha_fin = fecha_actual.date()
                programa.save()

        except Exception as e:
            print(f"Error al recalcular fechas: {str(e)}")
            raise
        
@api_view(['GET'])
def search_orders(request):
    search_term = request.GET.get('search', '')
    status = request.GET.get('status', 'all')
    
    queryset = OrdenTrabajo.objects.all()
    
    # Aplicar filtro de búsqueda
    if search_term:
        queryset = queryset.filter(
            Q(codigo_ot__icontains=search_term) |
            Q(descripcion_producto_ot__icontains=search_term) |
            Q(cliente__nombre__icontains=search_term)
        )
    
    # Aplicar filtro de estado
    if status != 'all':
        queryset = queryset.filter(situacion_ot__codigo_situacion_ot=status)
    
    # Incluir relaciones necesarias
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
        
class FinalizarDiaReporteView(APIView):
    permission_classes = [IsAuthenticated]

    def obtener_siguiente_dia_laboral(self, fecha):
        """Obtiene el siguiente dia laboral (excluyendo sabados y domingos)"""
        siguiente_dia = fecha + timedelta(days=1)
        #Si es sabado (5) o domingo (6), avanzar al lunes
        if siguiente_dia.weekday() >= 5:
            siguiente_dia = siguiente_dia + timedelta(days=(7 - siguiente_dia.weekday()))
        return siguiente_dia
    
    def identificar_tareas_incompletas(self, programa_id, fecha):
        """Identifica tareas que no se han completado para el dia especificado"""
        try:
            #Obtener el programa
            programa = get_object_or_404(ProgramaProduccion, id=programa_id)

            #Obtener tareas del día
            from .serializers import SupervisorReporteSerializer
            supervisor_view = SupervisorReportView()
            reporte_data = supervisor_view.get(None, programa_id).data

            tareas = reporte_data.get('tareas', [])
            tareas_del_dia = [tarea for tarea in tareas if tarea.get('fecha') == fecha]

            #Identificar tareas incompletas (menos del 100% de cumplimiento)
            tareas_incompletas = []
            for tarea in tareas_del_dia:
                kilos_prog = float(tarea.get('kilos_programados', 0))
                kilos_fab = float(tarea.get('kilos_fabricados', 0))

                if kilos_prog > 0 and kilos_fab < kilos_prog:
                    porcentaje = (kilos_fab / kilos_prog) * 100
                    kilos_restantes = kilos_prog - kilos_fab

                    tareas_incompletas.append({
                        'id': tarea.get('id'),
                        'ot_codigo': tarea.get('ot_codigo'),
                        'proceso': tarea.get('proceso'),
                        'maquina': tarea.get('maquina'),
                        'kilos_programados': kilos_prog,
                        'kilos_fabricados': kilos_fab,
                        'kilos_restantes': kilos_restantes,
                        'porcentaje_completado': round(porcentaje, 2),
                        'porcentaje_restante': round(100 - porcentaje, 2)
                    })
            return tareas_incompletas
        except Exception as e:
            print(f'Error identificando tareas incompletas: {str(e)}')
            raise e
        
    @transaction.atomic
    def post(self, request, programa_id, fecha_str):
        """
        Finaliza el dia, identificando tareas incompletas y creando continuaciones.
        Admite modo de previsualizacion que no realiza cambios en la base de datos.
        """
        try:
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Formato de fecha inválido. Use el formato YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            #Determinar si estamos en modo previsualización
            preview_only = request.data.get('preview_only', True)

            #Calcular siguiente dia laboral
            siguiente_dia = self.obtener_siguiente_dia_laboral(fecha)

            #Identificar tareas incompletas
            tareas_incompletas = self.identificar_tareas_incompletas(programa_id, fecha_str)

            #Si estamos en modo previsualización, solo devolver datos sin hacer cambios
            if preview_only:
                return Response({
                    'mensaje': f'Previsualización de finalización del día {fecha_str}',
                    'tareas_incompletas': tareas_incompletas,
                    'siguiente_dia': siguiente_dia.strftime('%Y-%m-%d'),
                    'total_tareas': len(tareas_incompletas)
                })
            #Si no estamos en previsualización, rear fragmentos y continuaciones
            programa = get_object_or_404(ProgramaProduccion, id=programa_id)
            tareas_procesadas = []

            for tarea in tareas_incompletas:
                item_ruta = get_object_or_404(ItemRuta, id=tarea['id'])

                #Buscar si ya existe un fragmento para esta tarea en esta fecha
                fragmento_existente = TareaFragmentada.objects.filter(
                    tarea_original=item_ruta,
                    fecha=fecha
                ).first()

                #Si no existe, crear el fragmento para el día actual
                if not fragmento_existente:
                    fragmento = TareaFragmentada.objects.create(
                        tarea_original=item_ruta,
                        fecha=fecha,
                        porcentaje_completado=tarea['porcentaje_completado'],
                        cantidad_asignada=tarea['kilos_programados'],
                        cantidad_completada=tarea['kilos_fabricados'],
                        es_continuacion=False,
                        nivel_fragmentacion=0
                    )
                else:
                    #Actualizar el fragmento existente
                    fragmento = fragmento_existente
                    fragmento.porcentaje_completado = tarea['porcentaje_completado']
                    fragmento.cantidad_completada = tarea['kilos_fabricados']
                    fragmento.save()

                #Crear la continuación para el siguiente día
                continuacion = TareaFragmentada.objects.create(
                    tarea_original=item_ruta,
                    tarea_padre=fragmento,
                    fecha=siguiente_dia,
                    porcentaje_completado=0,
                    cantidad_asignada=tarea['kilos_restantes'],
                    cantidad_completada=0,
                    es_continuacion=True,
                    nivel_fragmentacion=fragmento.nivel_fragmentacion + 1
                )

                #Actualizar registro de tareas procesadas 
                tareas_procesadas.append({
                    'id': tarea['id'],
                    'proceso': tarea['proceso'],
                    'ot_codigo': tarea['ot_codigo'],
                    'porcentaje_completado': tarea['porcentaje_completado'],
                    'kilos_restantes': tarea['kilos_restantes'],
                    'continuacion_id': continuacion.id,
                    'fecha_continuacion': siguiente_dia.strftime('%Y-%m-%d')
                })

            return Response({
                'mensaje': f'Día {fecha_str} finalizado con éxito',
                'tareas_procesadas': tareas_procesadas,
                'siguiente_dia': siguiente_dia.strftime('%Y-%m-%d'),
                'total_tareas': len(tareas_procesadas)
            })
        except Exception as e:
            print(f'Error finalizando día: {str(e)}')
            return Response(
                {'error': f'Error al finalizar el día: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TareaGenealogiaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, tarea_id):
        """Obtiene la genealogía completa de una tarea fragmentada"""
        try:
            #Obtener el item ruta
            item_ruta = get_object_or_404(ItemRuta, id=tarea_id)

            #Buscar el fragmento raíz (nivel 0, no es continuacion)
            fragmento_raiz = TareaFragmentada.objects.filter(
                tarea_original=item_ruta,
                nivel_fragmentacion=0
            ).first()

            if not fragmento_raiz:
                #Si no hay fragmento raíz pero hay fragmentos, buscar el de menor nivel
                fragmento_raiz = TareaFragmentada.objects.filter(
                    tarea_original=item_ruta
                ).order_by('nivel_fragmentacion').first()

                if not fragmento_raiz:
                    return Response(
                        {'mensaje': 'Esta tarea no tiene fragmentos asociados'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
            #Serializer con anidación recursiva
            serializer = TareaFragmentadaSerializer(fragmento_raiz)

            return Response({
                'tarea_original': {
                    'id': item_ruta.id,
                    'proceso': item_ruta.proceso.descripcion,
                    'maquina': item_ruta.maquina.descripcion if item_ruta.maquina else 'Sin maquina',
                    'cantidad_total': float(item_ruta.cantidad_pedido)
                },
                'genealogia': serializer.data,
                'progreso_global': serializer.data.get('progreso_acumulado', 0)
            })
        except Exception as e:
            print(f'Error obteniendo genealogía: {str(e)}')
            return Response(
                {'error': f'Error al obtener genealogía: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
