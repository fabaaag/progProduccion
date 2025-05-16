from datetime import datetime, timedelta, date, time
from .time_calculations import TimeCalculator
from ..models import TareaFragmentada, ProgramaOrdenTrabajo, Maquina, ItemRuta, ReporteDiarioPrograma, EjecucionTarea
from Operator.models import AsignacionOperador
from .machine_availability import MachineAvailabilityService

class ProcessNode:
    def __init__(self, proceso_id, proceso_data, fecha_inicio, fecha_fin, ot_id):
        self.proceso_id = proceso_id
        self.proceso_data = proceso_data
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.siguiente_proceso = None
        self.maquina_id = proceso_data.get('maquina_id')
        self.prioridad = proceso_data.get('prioridad', 0)
        self.intervals = []  # Lista para almacenar los intervalos de tiempo del proceso
        self.ot_id = ot_id  # Guardamos la referencia a la OT
        
    def actualizar_fechas(self, nueva_fecha_inicio):
        """Actualiza las fechas del proceso y sus intervalos"""
        # Asegurarnos que la nueva fecha sea un día laboral
        if not TimeCalculator.is_working_day(nueva_fecha_inicio.date()):
            nueva_fecha_inicio = datetime.combine(
                TimeCalculator.get_next_working_day(nueva_fecha_inicio.date()),
                TimeCalculator.WORKDAY_START
            )
        
        # Si la hora está fuera del horario laboral, ajustar al inicio del siguiente día
        if nueva_fecha_inicio.time() < TimeCalculator.WORKDAY_START:
            nueva_fecha_inicio = datetime.combine(nueva_fecha_inicio.date(), TimeCalculator.WORKDAY_START)
        elif nueva_fecha_inicio.time() > TimeCalculator.WORKDAY_END:
            siguiente_dia = TimeCalculator.get_next_working_day(nueva_fecha_inicio.date())
            nueva_fecha_inicio = datetime.combine(siguiente_dia, TimeCalculator.WORKDAY_START)

        # Recalcular los intervalos usando TimeCalculator
        calculo_tiempo = TimeCalculator().calculate_working_days(
            nueva_fecha_inicio,
            float(self.proceso_data['cantidad']),
            float(self.proceso_data['estandar'])
        )
        
        if 'error' not in calculo_tiempo:
            self.fecha_inicio = nueva_fecha_inicio
            self.fecha_fin = calculo_tiempo['next_available_time']
            self.intervals = calculo_tiempo['intervals']
        
    def propagar_ajuste(self, tiempo_setup=timedelta(minutes=30), procesos_por_maquina=None):
        """Propaga el ajuste a los procesos siguientes en la cadena y verifica conflictos de máquina"""
        if procesos_por_maquina and self.maquina_id:
            # Obtener todos los procesos que usan la misma máquina
            procesos_misma_maquina = procesos_por_maquina.get(self.maquina_id, [])
            
            # Ordenar por prioridad
            procesos_misma_maquina.sort(key=lambda x: x.prioridad)
            
            # Encontrar el índice de este proceso
            mi_indice = procesos_misma_maquina.index(self)
            
            # Ajustar todos los procesos posteriores que usan la misma máquina
            fecha_maquina_disponible = self.fecha_fin + tiempo_setup
            for proceso in procesos_misma_maquina[mi_indice + 1:]:
                if proceso.fecha_inicio < fecha_maquina_disponible:
                    proceso.actualizar_fechas(fecha_maquina_disponible)
                    # Propagar el ajuste a los procesos siguientes de esa OT
                    proceso.propagar_ajuste(tiempo_setup, procesos_por_maquina)
                fecha_maquina_disponible = proceso.fecha_fin + tiempo_setup

        # Propagar normalmente al siguiente proceso de la misma OT
        if self.siguiente_proceso:
            nueva_fecha_inicio = self.fecha_fin + tiempo_setup
            self.siguiente_proceso.actualizar_fechas(nueva_fecha_inicio)
            self.siguiente_proceso.propagar_ajuste(tiempo_setup, procesos_por_maquina)

    def agregar_intervalo(self, interval_data):
        """Agrega un intervalo de tiempo al proceso"""
        self.intervals.append(interval_data)

class ProductionScheduler:
    def __init__(self, time_calculator):
        self.time_calculator = time_calculator if time_calculator else TimeCalculator()
        self.machine_availability = MachineAvailabilityService()

    def generate_timeline_data(self, programa, ordenes_trabajo):
        """Genera datos del timeline considerando asignaciones y fragmentación"""
        try:
            print(f"[ProductionScheduler] Generando timeline base para programa {programa.id}")
            timeline_data = self._generate_base_timeline(programa, ordenes_trabajo)
            print("[ProductionScheduler] Timeline base generado")
            
            print("[ProductionScheduler] Agregando tareas fragmentadas")
            self._add_fragmented_tasks(timeline_data, programa)
            print("[ProductionScheduler] Tareas fragmentadas agregadas")
            
            return timeline_data
        except Exception as e:
            print(f"[ProductionScheduler] Error generando timeline data: {str(e)}")
            print(f"[ProductionScheduler] Detalles del error: {type(e).__name__}")
            import traceback
            print(f"[ProductionScheduler] Stack trace: {traceback.format_exc()}")
            return {"groups": [], "items": []}

    def _generate_base_timeline(self, programa, ordenes_trabajo):
        cascade_calculator = ProductionCascadeCalculator(self.time_calculator)
        groups = []
        all_items = []  # Lista separada para todos los items
        procesos_por_maquina = {}
        nodos_procesos = {}

        for ot_data in ordenes_trabajo:
            ot_id = ot_data['orden_trabajo']
            fecha_inicio = datetime.combine(programa.fecha_inicio, self.time_calculator.WORKDAY_START)
            
            # Grupo principal (OT)
            group = {
                "id": f"ot_{ot_id}",
                "orden_trabajo_codigo_ot": ot_data['orden_trabajo_codigo_ot'],
                "descripcion": ot_data['orden_trabajo_descripcion_producto_ot'],
                "procesos": []
            }
            
            # Calcular tiempos ideales en cascada
            cascade_times = cascade_calculator.calculate_cascade_times(ot_data['procesos'], fecha_inicio)
            
            proceso_anterior = None
            for proceso in ot_data['procesos']:
                if not proceso.get('estandar') or not proceso.get('cantidad'):
                    continue
                
                proceso_id = f"proc_{proceso['id']}"
                
                # Agregar proceso al grupo
                group['procesos'].append({
                    "id": proceso_id,
                    "descripcion": proceso['descripcion'],
                    "item": proceso['item']
                })
                
                # Crear nodo de proceso
                nodo = ProcessNode(
                    proceso_id=proceso_id,
                    proceso_data=proceso,
                    fecha_inicio=cascade_times[proceso_id]['inicio'],
                    fecha_fin=cascade_times[proceso_id]['fin'],
                    ot_id=ot_id  # Pasamos el ot_id al constructor
                )
                
                # Establecer dependencia con proceso anterior
                if proceso_anterior:
                    proceso_anterior.siguiente_proceso = nodo
                
                # Guardar nodo
                nodos_procesos[proceso_id] = nodo
                proceso_anterior = nodo
                
                # Agrupar por máquina
                if proceso.get('maquina_id'):
                    if proceso['maquina_id'] not in procesos_por_maquina:
                        procesos_por_maquina[proceso['maquina_id']] = []
                    procesos_por_maquina[proceso['maquina_id']].append(nodo)

                # Generar intervalos iniciales
                calculo_tiempo = self.time_calculator.calculate_working_days(
                    nodo.fecha_inicio,
                    float(proceso['cantidad']),
                    float(proceso['estandar'])
                )
                
                if 'error' not in calculo_tiempo:
                    # Agrupar intervalos por día
                    intervalos_por_dia = {}
                    
                    for interval in calculo_tiempo['intervals']:
                        fecha_dia = interval['fecha_inicio'].date()
                        if fecha_dia not in intervalos_por_dia:
                            intervalos_por_dia[fecha_dia] = {
                                'fecha_inicio': interval['fecha_inicio'],
                                'fecha_fin': interval['fecha_fin'],
                                'unidades': interval['unidades'],
                                'unidades_restantes': interval.get('unidades_restantes', 0)
                            }
                        else:
                            # Actualizar el intervalo existente
                            intervalos_por_dia[fecha_dia]['fecha_fin'] = interval['fecha_fin']
                            intervalos_por_dia[fecha_dia]['unidades'] += interval['unidades']
                            intervalos_por_dia[fecha_dia]['unidades_restantes'] += interval.get('unidades_restantes', 0)

                    # Crear items agrupados por día
                    for fecha_dia, intervalo_dia in intervalos_por_dia.items():
                        nodo.agregar_intervalo(intervalo_dia)
                        item = {
                            "id": f"item_{proceso['id']}_{fecha_dia.strftime('%Y%m%d')}",
                            "ot_id": f"ot_{ot_id}",
                            "proceso_id": proceso_id,
                            "name": f"{proceso['descripcion']} - {intervalo_dia['unidades']:.0f} de {proceso['cantidad']} unidades",
                            "start_time": intervalo_dia['fecha_inicio'].strftime('%Y-%m-%d %H:%M:%S'),
                            "end_time": intervalo_dia['fecha_fin'].strftime('%Y-%m-%d %H:%M:%S'),
                            "cantidad_total": float(proceso['cantidad']),
                            "cantidad_intervalo": float(intervalo_dia['unidades']),
                            "unidades_restantes": float(intervalo_dia['unidades_restantes']),
                            "estandar": float(proceso['estandar']),
                            "maquina": proceso.get('maquina_descripcion', 'No asignada'),
                            "operador_nombre": proceso.get('operador_nombre', 'No asignado'),
                            "asignado": proceso.get('operador_id') is not None
                        }
                        all_items.append(item)
            
            groups.append(group)

        # Segunda pasada: resolver conflictos de máquina y propagar ajustes
        for maquina_id, procesos in procesos_por_maquina.items():
            # Ordenar todos los procesos de esta máquina por prioridad de OT
            procesos.sort(key=lambda x: x.prioridad)
            
            # El primer proceso (más prioritario) mantiene su fecha
            fecha_maquina_disponible = procesos[0].fecha_fin + timedelta(minutes=30)
            
            # Para los demás procesos, asignar fechas secuencialmente
            for proceso in procesos[1:]:
                if proceso.fecha_inicio < fecha_maquina_disponible:
                    # Necesitamos mover este proceso
                    proceso.actualizar_fechas(fecha_maquina_disponible)
                    # Propagar el cambio a los procesos siguientes de la misma OT
                    proceso.propagar_ajuste(procesos_por_maquina=procesos_por_maquina)
                
                # Actualizar cuando estará disponible la máquina
                fecha_maquina_disponible = proceso.fecha_fin + timedelta(minutes=30)

        # Actualizar los items con las nuevas fechas
        all_items.clear()
        for nodo in nodos_procesos.values():
            for interval in nodo.intervals:
                item = {
                    "id": f"item_{nodo.proceso_data['id']}_{len(all_items)}",
                    "ot_id": f"ot_{nodo.ot_id}",  # Usamos el ot_id guardado en el nodo
                    "proceso_id": nodo.proceso_id,
                    "name": f"{nodo.proceso_data['descripcion']} - {interval['unidades']:.0f} de {nodo.proceso_data['cantidad']} unidades",
                    "start_time": interval['fecha_inicio'].strftime('%Y-%m-%d %H:%M:%S'),
                    "end_time": interval['fecha_fin'].strftime('%Y-%m-%d %H:%M:%S'),
                    "cantidad_total": float(nodo.proceso_data['cantidad']),
                    "cantidad_intervalo": float(interval['unidades']),
                    "unidades_restantes": float(interval.get('unidades_restantes', 0)),
                    "estandar": float(nodo.proceso_data['estandar']),
                    "maquina": nodo.proceso_data.get('maquina_descripcion', 'No asignada'),
                    "operador_nombre": nodo.proceso_data.get('operador_nombre', 'No asignado'),
                    "asignado": nodo.proceso_data.get('operador_id') is not None
                }
                all_items.append(item)

        return {
            "groups": groups,
            "items": all_items
        }

    def _add_fragmented_tasks(self, timeline_data, programa):
        """Añade tareas fragmentadas al timeline"""
        fragmentos = TareaFragmentada.objects.filter(
            programa=programa,
            es_continuacion=True
        ).select_related(
            'tarea_original',
            'tarea_original__proceso',
            'tarea_original__maquina',
            'tarea_original__ruta__orden_trabajo'
        )

        for fragmento in fragmentos:
            item_ruta = fragmento.tarea_original
            if not item_ruta:
                continue

            # Encontrar el grupo correspondiente
            ot_id = item_ruta.ruta.orden_trabajo.id
            grupo = next(
                (g for g in timeline_data["groups"] if g["id"] == f"ot_{ot_id}"),
                None
            )

            if grupo:
                item = {
                    "id": f"frag_{fragmento.id}",
                    "proceso_id": f"proc_{item_ruta.id}",
                    "name": f"{item_ruta.proceso.descripcion} (Continuación)",
                    "start_time": datetime.combine(fragmento.fecha, self.time_calculator.WORKDAY_START).strftime('%Y-%m-%d %H:%M:%S'),
                    "end_time": datetime.combine(fragmento.fecha, self.time_calculator.WORKDAY_END).strftime('%Y-%m-%d %H:%M:%S'),
                    "cantidad_total": float(fragmento.cantidad_asignada),
                    "cantidad_intervalo": float(fragmento.cantidad_asignada),
                    "unidades_restantes": 0,
                    "estandar": float(item_ruta.estandar),
                    "maquina": item_ruta.maquina.descripcion if item_ruta.maquina else "Sin máquina",
                    "es_continuacion": True
                }
                
                timeline_data["items"].append(item)

    def calculate_program_end_date(self, programa, ordenes_trabajo=None):
        """Calcula la fecha de finalización del programa basada en la última tarea proyectada"""
        try:
            print(f"[ProductionScheduler] Iniciando cálculo de fecha fin para programa {programa.id}")
            
            if ordenes_trabajo is None:
                print("[ProductionScheduler] Obteniendo órdenes de trabajo del programa")
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
                                'prioridad': prog_ot.prioridad  # Importante: incluir la prioridad
                            }
                            ot_data['procesos'].append(proceso_data)
                    
                    ordenes_trabajo.append(ot_data)

            print("[ProductionScheduler] Generando timeline data")
            # Generar timeline data para obtener los nodos y sus intervalos ajustados
            timeline_data = self._generate_base_timeline(programa, ordenes_trabajo)
            
            # Si no hay items, usar la fecha de inicio
            if not timeline_data.get('items'):
                return programa.fecha_inicio

            # Encontrar la fecha más tardía entre todos los intervalos
            latest_date = programa.fecha_inicio
            if isinstance(latest_date, date):
                latest_date = datetime.combine(latest_date, self.time_calculator.WORKDAY_START)

            for item in timeline_data['items']:
                try:
                    end_time = datetime.strptime(item['end_time'], '%Y-%m-%d %H:%M:%S')
                    if end_time > latest_date:
                        latest_date = end_time
                except (KeyError, ValueError) as e:
                    continue

            # Asegurarnos que la fecha final sea un día laboral
            if not TimeCalculator.is_working_day(latest_date.date()):
                latest_date = datetime.combine(
                    TimeCalculator.get_next_working_day(latest_date.date()),
                    self.time_calculator.WORKDAY_END
                )
            elif latest_date.time() > TimeCalculator.WORKDAY_END:
                siguiente_dia = TimeCalculator.get_next_working_day(latest_date.date())
                latest_date = datetime.combine(siguiente_dia, TimeCalculator.WORKDAY_END)

            print(f"[ProductionScheduler] Fecha fin calculada: {latest_date.date()}")
            return latest_date.date()

        except Exception as e:
            print(f"[ProductionScheduler] Error calculando fecha fin: {str(e)}")
            return programa.fecha_inicio

    def _get_program_orders(self, programa):
        """Obtiene las órdenes de trabajo del programa"""
        return ProgramaOrdenTrabajo.objects.filter(
            programa=programa
        ).select_related(
            'orden_trabajo',
            'orden_trabajo__ruta_ot'
        ).prefetch_related(
            'orden_trabajo__ruta_ot__items',
            'orden_trabajo__ruta_ot__items__proceso',
            'orden_trabajo__ruta_ot__items__maquina'
        ).order_by('prioridad')

    def _process_order_group(self, ot_data, programa, operador_timeline):
        try:
            # Manejar tanto objetos ProgramaOrdenTrabajo como diccionarios
            if isinstance(ot_data, dict):
                ot_id = ot_data['orden_trabajo']
                ot_codigo = ot_data['orden_trabajo_codigo_ot']
                ot_descripcion = ot_data['orden_trabajo_descripcion_producto_ot']
                procesos = ot_data.get('procesos', [])
            else:
                # Es un objeto ProgramaOrdenTrabajo
                orden_trabajo = ot_data.orden_trabajo
                ot_id = orden_trabajo.id
                ot_codigo = orden_trabajo.codigo_ot
                ot_descripcion = orden_trabajo.descripcion_producto_ot
                procesos = orden_trabajo.ruta_ot.items.all().order_by('item')

            group = {
                "id": f"ot_{ot_id}",
                "orden_trabajo_codigo_ot": ot_codigo,
                "descripcion": ot_descripcion,
                "procesos": []
            }

            # Usar la fecha de inicio del programa como fecha base
            next_available_start = datetime.combine(programa.fecha_inicio, self.time_calculator.WORKDAY_START)

            procesos_data = self._process_order_processes(
                procesos,
                ot_id,
                programa,
                operador_timeline,
                next_available_start
            )

            group['procesos'] = procesos_data['procesos']
            return {
                'group': group,
                'items': procesos_data['items']
            }
        except Exception as e:
            print(f"Error procesando grupo de OT: {str(e)}")
            return None

    def _process_order_processes(self, procesos, ot_id, programa, operador_timeline, next_available_start):
        items = []
        procesos_list = []

        for proceso in procesos:
            # Obtener datos del proceso (código existente)
            if isinstance(proceso, dict):
                proceso_id = f"proc_{proceso['id']}"
                descripcion = proceso.get('descripcion', 'Sin descripción')
                item_num = proceso.get('item', 0)
                estandar = float(proceso.get('estandar', 0))
                cantidad = float(proceso.get('cantidad', 0))
                # Obtener el objeto Maquina completo, no solo el ID
                maquina = Maquina.objects.get(id=proceso.get('maquina_id')) if proceso.get('maquina_id') else None
                prioridad = proceso.get('prioridad')
            else:
                proceso_id = f"proc_{proceso.id}"
                descripcion = proceso.proceso.descripcion
                item_num = proceso.item
                estandar = float(proceso.estandar or 0)
                cantidad = float(proceso.cantidad_pedido or 0)
                maquina = proceso.maquina
                prioridad = None

            procesos_list.append({
                "id": proceso_id,
                "descripcion": descripcion,
                "item": item_num
            })

            if not self._is_valid_process({'estandar': estandar, 'cantidad': cantidad}):
                continue

            # Verificar disponibilidad de máquina
            if maquina:
                verificacion = self.machine_availability.verificar_conflicto(
                    maquina,  # Ahora maquina es un objeto completo
                    next_available_start,
                    next_available_start + timedelta(hours=8),
                    prioridad
                )
                
                if verificacion['tiene_conflicto']:
                    next_available_start = verificacion['fecha_disponible']

            # Calcular fechas
            dates_data = self.time_calculator.calculate_working_days(
                next_available_start,
                cantidad,
                estandar
            )

            for idx, interval in enumerate(dates_data['intervals']):
                item = self._create_timeline_item(
                    proceso,
                    ot_id,
                    proceso_id,
                    interval,
                    idx,
                    asignacion
                )
                items.append(item)

                if asignacion:
                    operador_id = asignacion['operador_id'] if isinstance(asignacion, dict) else asignacion.operador.id
                    operador_timeline[operador_id] = interval['fecha_fin']

            next_available_start = dates_data['next_available_time']
        
        return {
            'procesos': procesos_list,
            'items': items
        }

    def _is_valid_process(self, proceso):
        """Valida si un proceso tiene datos válidos para ser procesado"""
        return (
            proceso.get('estandar', 0) > 0 and
            proceso.get('cantidad', 0) > 0
        )

    def _create_timeline_item(self, proceso, ot_id, proceso_id, interval, idx, asignacion=None):
        """Crea un item individual del timeline"""
        # Manejar tanto diccionarios como objetos ItemRuta
        if isinstance(proceso, dict):
            proceso_id_num = proceso['id']
            descripcion = proceso.get('descripcion', 'Proceso')
            cantidad = float(proceso.get('cantidad', 0))
            estandar = proceso.get('estandar', 0)
        else:
            proceso_id_num = proceso.id
            descripcion = proceso.proceso.descripcion if proceso.proceso else 'Proceso'
            cantidad = float(proceso.cantidad_pedido or 0)
            estandar = proceso.estandar

        item = {
            "id": f'item_{proceso_id_num}_{idx}',
            "ot_id": f"ot_{ot_id}",
            "proceso_id": proceso_id,
            "name": f"{descripcion} - {interval['unidades']:.0f} de {cantidad:.0f} unidades",
            "start_time": interval['fecha_inicio'].strftime('%Y-%m-%d %H:%M:%S'),
            "end_time": interval['fecha_fin'].strftime('%Y-%m-%d %H:%M:%S'),
            "cantidad_total": cantidad,
            "cantidad_intervalo": float(interval['unidades']),
            "unidades_restantes": float(interval['unidades_restantes']),
            "estandar": estandar
        }

        # Añadir información de asignación si existe
        if asignacion:
            if isinstance(asignacion, dict):
                item.update({
                    "asignacion_id": asignacion.get('id'),
                    "operador_id": asignacion.get('operador_id'),
                    "operador_nombre": asignacion.get('operador_nombre'),
                    "asignado": True
                })
            else:
                item.update({
                    "asignacion_id": asignacion.id,
                    "operador_id": asignacion.operador.id,
                    "operador_nombre": asignacion.operador.nombre,
                    "asignado": True
                })
        else:
            item.update({
                "asignacion_id": None,
                "operador_id": None,
                "operador_nombre": None,
                "asignado": False
            })
        
        return item

    def _find_latest_end_date(self, timeline_data):
        """Encuentra la fecha más tardía en el timeline"""
        latest_date = None
        
        if not timeline_data or not timeline_data.get('groups'):
            return None
        
        for group in timeline_data['groups']:
            for item in group['items']:
                try:
                    end_time = datetime.strptime(item['end_time'], '%Y-%m-%d %H:%M:%S')
                    if not latest_date or end_time > latest_date:
                        latest_date = end_time
                except (KeyError, ValueError) as e:
                    print(f"Error procesando fecha fin de item: {str(e)}")
                    continue

        return latest_date.date() if latest_date else None

    def recalculate_order_dates(self, programa_ot, fecha_inicio):
        """
        Recalcula las fechas para una orden específica y sus procesos
        """
        fecha_actual = fecha_inicio
        
        for item_ruta in programa_ot.orden_trabajo.ruta_ot.items.all().order_by('item'):
            if not item_ruta.maquina or not item_ruta.estandar:
                continue
            
            calculo_tiempo = self.time_calculator.calculate_working_days(
                fecha_actual,
                item_ruta.cantidad_pedido,
                item_ruta.estandar
            )
            
            if 'error' not in calculo_tiempo:
                fecha_actual = calculo_tiempo['next_available_time']
                
                # Actualizar asignación si existe
                asignacion = AsignacionOperador.objects.filter(
                    programa=programa_ot.programa,
                    item_ruta=item_ruta
                ).first()
                
                if asignacion:
                    asignacion.fecha_inicio = calculo_tiempo['intervals'][0]['fecha_inicio']
                    asignacion.fecha_fin = fecha_actual
                    asignacion.save()
        
        return fecha_actual
    
    def create_fragmented_tasks(self, programa, ordenes_trabajo):
        try:
            print(f"[ProductionScheduler] Creando tareas fragmentadas para programa {programa.id}")
            
            # Necesitamos asegurarnos de obtener la timeline completa para todos los días
            timeline_data = self._generate_base_timeline(programa, ordenes_trabajo)
            
            # Crear ReporteDiarioPrograma para cada día del programa
            fecha_actual = programa.fecha_inicio
            while fecha_actual <= programa.fecha_fin:
                if TimeCalculator.is_working_day(fecha_actual):
                    ReporteDiarioPrograma.objects.get_or_create(
                        programa=programa,
                        fecha=fecha_actual,
                        defaults={
                            'estado': 'ABIERTO'
                        }
                    )
                fecha_actual += timedelta(days=1)

            # Estructura para agrupar tareas por día e item_ruta
            tareas_agrupadas = {}  # {(fecha, item_ruta_id): {'cantidad': X, 'inicio': time, 'fin': time}}
            
            # Para cada item en la timeline, agrupar por día y proceso
            for item in timeline_data['items']:
                proceso_id = item['proceso_id'].replace('proc_', '')
                item_ruta = ItemRuta.objects.get(id=proceso_id)
                
                # Convertir fecha de inicio y fin a objetos datetime
                start_time = datetime.strptime(item['start_time'], '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(item['end_time'], '%Y-%m-%d %H:%M:%S')
                
                # Crear una entrada para cada día dentro del rango
                current_day = start_time.date()
                
                while current_day <= end_time.date():
                    if not TimeCalculator.is_working_day(current_day):
                        current_day += timedelta(days=1)
                        continue
                    
                    # Calcular cantidad para este día
                    if current_day == start_time.date() and current_day == end_time.date():
                        # El proceso comienza y termina en el mismo día
                        cantidad_dia = float(item['cantidad_intervalo'])
                        hora_inicio = start_time.time()
                        hora_fin = end_time.time()
                    elif current_day == start_time.date():
                        # Primer día del proceso
                        horas_dia = (datetime.combine(current_day, time(17, 45)) - start_time).seconds / 3600
                        cantidad_dia = (horas_dia / 8) * float(item['cantidad_intervalo'])
                        hora_inicio = start_time.time()
                        hora_fin = time(17, 45)
                    elif current_day == end_time.date():
                        # Último día del proceso
                        horas_dia = (end_time - datetime.combine(current_day, time(7, 45))).seconds / 3600
                        cantidad_dia = (horas_dia / 8) * float(item['cantidad_intervalo'])
                        hora_inicio = time(7, 45)
                        hora_fin = end_time.time()
                    else:
                        # Día completo intermedio
                        dias_totales = (end_time.date() - start_time.date()).days + 1
                        cantidad_dia = float(item['cantidad_intervalo']) / dias_totales
                        hora_inicio = time(7, 45)
                        hora_fin = time(17, 45)
                    
                    # Clave para agrupar: (fecha, item_ruta_id)
                    clave_agrupacion = (current_day, item_ruta.id)
                    
                    # Si ya existe una entrada para esta clave, actualizar la cantidad y horas
                    if clave_agrupacion in tareas_agrupadas:
                        tareas_agrupadas[clave_agrupacion]['cantidad'] += cantidad_dia
                        # Ajustar hora de inicio (tomar la más temprana)
                        if hora_inicio < tareas_agrupadas[clave_agrupacion]['inicio'].time():
                            tareas_agrupadas[clave_agrupacion]['inicio'] = datetime.combine(current_day, hora_inicio)
                        # Ajustar hora de fin (tomar la más tardía)
                        if hora_fin > tareas_agrupadas[clave_agrupacion]['fin'].time():
                            tareas_agrupadas[clave_agrupacion]['fin'] = datetime.combine(current_day, hora_fin)
                    else:
                        # Crear nueva entrada
                        tareas_agrupadas[clave_agrupacion] = {
                            'cantidad': cantidad_dia,
                            'inicio': datetime.combine(current_day, hora_inicio),
                            'fin': datetime.combine(current_day, hora_fin),
                            'item_ruta': item_ruta
                        }
                    
                    current_day += timedelta(days=1)
            
            # Ahora crear las tareas fragmentadas agrupadas
            print(f"[ProductionScheduler] Creando {len(tareas_agrupadas)} tareas fragmentadas agrupadas")
            for (fecha, _), datos in tareas_agrupadas.items():
                # Crear o actualizar la tarea fragmentada
                # Solo usamos los campos que sabemos que existen en el modelo
                TareaFragmentada.objects.update_or_create(
                    tarea_original=datos['item_ruta'],
                    programa=programa,
                    fecha=fecha,
                    defaults={
                        'fecha_planificada_inicio': datos['inicio'],
                        'fecha_planificada_fin': datos['fin'],
                        'cantidad_asignada': datos['cantidad'],  # Esta es la cantidad total para el día
                        'cantidad_pendiente_anterior': 0,
                        'cantidad_completada': 0,
                        'es_continuacion': False,
                        'estado': 'PENDIENTE'
                    }
                )
            
            # Verificar cuántas tareas se crearon por día para depuración
            dias_con_tareas = TareaFragmentada.objects.filter(programa=programa).values('fecha').distinct().count()
            print(f"[ProductionScheduler] Tareas fragmentadas creadas en {dias_con_tareas} días diferentes")
            
            # Ver si cada día del programa tiene tareas
            fecha_actual = programa.fecha_inicio
            while fecha_actual <= programa.fecha_fin:
                if TimeCalculator.is_working_day(fecha_actual):
                    count = TareaFragmentada.objects.filter(
                        programa=programa, 
                        fecha=fecha_actual
                    ).count()
                    print(f"[ProductionScheduler] Fecha {fecha_actual}: {count} tareas")
                fecha_actual += timedelta(days=1)
            
            return True
        except Exception as e:
            print(f"[ProductionScheduler] Error en create_fragmented_tasks: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


class ProductionCascadeCalculator:
    def __init__(self, time_calculator):
        self.time_calculator = time_calculator

    def calculate_cascade_times(self, procesos, fecha_inicio):
        """
        Calcula los tiempos en cascada para una serie de procesos
        siguiendo la lógica del Excel
        """
        proceso_timeline = {}
        produccion_acumulada = {}

        for i, proceso in enumerate(procesos):
            proceso_id = f"proc_{proceso['id']}"
            estandar = float(proceso['estandar'])
            cantidad_total = float(proceso['cantidad'])
            
            # Para el primer proceso, usar fecha_inicio directamente
            if i == 0:
                fecha_inicio_proceso = fecha_inicio
            else:
                # Para procesos posteriores, calcular basado en el proceso anterior
                proceso_anterior = procesos[i-1]
                proc_ant_id = f"proc_{proceso_anterior['id']}"
                estandar_anterior = float(proceso_anterior['estandar'])
                
                # Calcular cuántas unidades necesita este proceso para comenzar
                unidades_necesarias = min(estandar, cantidad_total)
                
                # Calcular cuánto tiempo necesita el proceso anterior para producir estas unidades
                horas_necesarias = unidades_necesarias / estandar_anterior
                
                # La fecha de inicio será cuando el proceso anterior haya producido suficiente
                fecha_inicio_proceso = proceso_timeline[proc_ant_id]['inicio'] + timedelta(hours=horas_necesarias)
                
                # Añadir tiempo de setup entre procesos
                fecha_inicio_proceso += timedelta(minutes=30)

            # Calcular tiempo total de este proceso
            tiempo_total = cantidad_total / estandar  # horas totales necesarias
            
            # Calcular fecha fin considerando horario laboral
            calculo_tiempo = self.time_calculator.calculate_working_days(
                fecha_inicio_proceso,
                cantidad_total,
                estandar
            )
            
            if 'error' not in calculo_tiempo:
                fecha_fin_proceso = calculo_tiempo['next_available_time']
            else:
                fecha_fin_proceso = fecha_inicio_proceso + timedelta(hours=tiempo_total)

            proceso_timeline[proceso_id] = {
                'inicio': fecha_inicio_proceso,
                'fin': fecha_fin_proceso,
                'unidades_por_hora': estandar,
                'cantidad_total': cantidad_total,
                'produccion_por_intervalo': []
            }

            # Calcular la producción por intervalos
            if 'error' not in calculo_tiempo:
                for interval in calculo_tiempo['intervals']:
                    proceso_timeline[proceso_id]['produccion_por_intervalo'].append({
                        'fecha_inicio': interval['fecha_inicio'],
                        'fecha_fin': interval['fecha_fin'],
                        'unidades': interval['unidades'],
                        'unidades_restantes': interval.get('unidades_restantes', 0)
                    })

        return proceso_timeline

    def get_production_at_time(self, proceso_info, tiempo):
        """
        Calcula cuánto se ha producido hasta un momento específico
        """
        produccion_total = 0
        
        for intervalo in proceso_info['produccion_por_intervalo']:
            if tiempo < intervalo['fecha_inicio']:
                break
            elif tiempo >= intervalo['fecha_fin']:
                produccion_total += intervalo['unidades']
            else:
                # Calcular producción parcial en el intervalo actual
                tiempo_transcurrido = (tiempo - intervalo['fecha_inicio']).total_seconds() / 3600
                produccion_parcial = tiempo_transcurrido * proceso_info['unidades_por_hora']
                produccion_total += min(produccion_parcial, intervalo['unidades'])
                
        return min(produccion_total, proceso_info['cantidad_total'])