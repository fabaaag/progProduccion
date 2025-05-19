from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta, date
from .time_calculations import TimeCalculator
from JobManagement.models import ItemRuta, ProgramaOrdenTrabajo
import logging
import os
from pathlib import Path

class MachineAvailabilityService:
    def __init__(self):
        self.time_calculator = TimeCalculator()
        self.setup_logger()

    def setup_logger(self):
        """Configura el logger para el servicio"""
        # Deshabilitado temporalmente para ahorrar espacio
        self.logger = logging.getLogger('machine_availability')
        self.logger.addHandler(logging.NullHandler())
        
        # # Crear directorio para logs si no existe
        # log_dir = Path('logs/availability_checks')
        # log_dir.mkdir(parents=True, exist_ok=True)

        # # Crear un logger específico para este servicio
        # self.logger = logging.getLogger('machine_availability')
        # self.logger.setLevel(logging.DEBUG)

        # # Crear un nuevo archivo de log con timestamp
        # timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # log_file = log_dir / f'availability_check_{timestamp}.log'
        
        # # Configurar el handler para archivo
        # file_handler = logging.FileHandler(log_file, mode='w')
        # file_handler.setLevel(logging.DEBUG)
        
        # # Definir el formato del log
        # formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        # file_handler.setFormatter(formatter)
        
        # # Agregar el handler al logger
        # self.logger.addHandler(file_handler)

    def obtener_intervalos_maquina(self, maquina, fecha_inicio, fecha_fin):
        """Obtiene los intervalos de uso existentes para una máquina"""
        self.logger.info(f"\nObteniendo intervalos para máquina {maquina.codigo_maquina}")
        self.logger.info(f"Rango: {fecha_inicio} - {fecha_fin}")
        
        intervalos = []
        
        # Obtener intervalos existentes de la base de datos
        asignaciones = ItemRuta.objects.filter(
            maquina=maquina,
            ruta__orden_trabajo__programaordentrabajo__isnull=False
        ).select_related(
            'ruta',
            'ruta__orden_trabajo',
            'proceso'
        ).prefetch_related(
            'ruta__orden_trabajo__programaordentrabajo_set'
        )

        for asignacion in asignaciones:
            programa_ot = asignacion.ruta.orden_trabajo.programaordentrabajo_set.first()
            if not programa_ot:
                continue

            # Calcular el intervalo específico para este proceso
            calculo_tiempo = self.time_calculator.calculate_working_days(
                programa_ot.programa.fecha_inicio,
                asignacion.cantidad_pedido,
                asignacion.estandar
            )

            if 'error' not in calculo_tiempo and calculo_tiempo['intervals']:
                for intervalo in calculo_tiempo['intervals']:
                    intervalos.append({
                        'inicio': intervalo['fecha_inicio'],
                        'fin': intervalo['fecha_fin'],
                        'ot': asignacion.ruta.orden_trabajo.codigo_ot,
                        'proceso': asignacion.proceso,
                        'prioridad': programa_ot.prioridad,
                        'item_ruta': asignacion
                    })

        return sorted(intervalos, key=lambda x: (x['inicio'], x['prioridad']))

    def verificar_conflicto(self, maquina, fecha_inicio, fecha_fin, prioridad_actual):
        """Verifica si hay conflicto y retorna información del conflicto"""
        self.logger.info(f"\nVerificando conflictos para máquina {maquina.codigo_maquina}")
        self.logger.info(f"Intervalo a verificar: {fecha_inicio} - {fecha_fin}")
        self.logger.info(f"Prioridad actual: {prioridad_actual}")

        intervalos = self.obtener_intervalos_maquina(maquina, fecha_inicio, fecha_fin)
        
        for intervalo in intervalos:
            if (fecha_inicio < intervalo['fin'] and fecha_fin > intervalo['inicio']):
                self.logger.warning(f"Conflicto detectado con OT {intervalo['ot']}")
                self.logger.warning(f"Prioridad del conflicto: {intervalo['prioridad']}")
                
                return {
                    'tiene_conflicto': True,
                    'con_mayor_prioridad': intervalo['prioridad'] <= prioridad_actual,
                    'fecha_disponible': intervalo['fin'] + timedelta(minutes=30),
                    'intervalo_conflicto': intervalo
                }
        
        self.logger.info("No se detectaron conflictos")
        return {
            'tiene_conflicto': False,
            'fecha_disponible': fecha_inicio
        }

    def obtener_ajustes_necesarios(self, programa):
        """Obtiene los ajustes necesarios para un programa"""
        self.logger.info(f"\nObteniendo ajustes para programa {programa.id}")
        
        ajustes = []
        ordenes = ProgramaOrdenTrabajo.objects.filter(
            programa=programa
        ).select_related(
            'orden_trabajo',
            'orden_trabajo__ruta_ot'
        ).prefetch_related(
            'orden_trabajo__ruta_ot__items__maquina',
            'orden_trabajo__ruta_ot__items__proceso'
        ).order_by('prioridad')

        for prog_ot in ordenes:
            fecha_actual = programa.fecha_inicio
            
            for item_ruta in prog_ot.orden_trabajo.ruta_ot.items.all().order_by('item'):
                if not item_ruta.maquina or not item_ruta.estandar:
                    continue

                # Calcular duración del proceso
                calculo_tiempo = self.time_calculator.calculate_working_days(
                    fecha_actual,
                    item_ruta.cantidad_pedido,
                    item_ruta.estandar
                )

                if 'error' in calculo_tiempo:
                    continue

                fecha_fin = calculo_tiempo['next_available_time']
                
                # Verificar conflictos
                verificacion = self.verificar_conflicto(
                    item_ruta.maquina,
                    fecha_actual,
                    fecha_fin,
                    prog_ot.prioridad
                )

                if verificacion['tiene_conflicto']:
                    ajustes.append({
                        'item_ruta': item_ruta,
                        'fecha_original': fecha_actual,
                        'fecha_ajustada': verificacion['fecha_disponible'],
                        'maquina': item_ruta.maquina,
                        'proceso': item_ruta.proceso,
                        'orden_trabajo': prog_ot.orden_trabajo.codigo_ot,
                        'prioridad': prog_ot.prioridad
                    })

                fecha_actual = verificacion['fecha_disponible']

        return ajustes

    def verificar_disponibilidad_maquina(self, maquina, fecha_inicio, fecha_fin, programa_actual=None, item_ruta_actual=None, prioridad_actual=None):
        """
        Verifica si una máquina está disponible en el rango de fechas especificado
        """
        TIEMPO_SETUP = timedelta(minutes=30)
        
        self.logger.info(f"\n{'='*50}")
        self.logger.info(f"Verificando disponibilidad de máquina {maquina.codigo_maquina}")
        self.logger.info(f"Rango solicitado: {fecha_inicio} - {fecha_fin}")
        self.logger.info(f"Prioridad actual: {prioridad_actual}")

        # Asegurar que las fechas sean datetime
        if isinstance(fecha_inicio, date):
            fecha_inicio = datetime.combine(fecha_inicio, TimeCalculator.WORKDAY_START)
        elif not isinstance(fecha_inicio, datetime):
            fecha_inicio = datetime.combine(datetime.strptime(str(fecha_inicio), "%Y-%m-%d").date(), TimeCalculator.WORKDAY_START)

        if isinstance(fecha_fin, date):
            fecha_fin = datetime.combine(fecha_fin, TimeCalculator.WORKDAY_END)
        elif not isinstance(fecha_fin, datetime):
            fecha_fin = datetime.combine(datetime.strptime(str(fecha_fin), "%Y-%m-%d").date(), TimeCalculator.WORKDAY_END)

        # Obtener todas las asignaciones ordenadas por fecha y prioridad
        asignaciones = ItemRuta.objects.filter(
            maquina=maquina,
            ruta__orden_trabajo__programaordentrabajo__isnull=False
        ).select_related(
            'ruta',
            'ruta__orden_trabajo',
            'proceso'
        ).prefetch_related(
            'ruta__orden_trabajo__programaordentrabajo_set'
        )

        if item_ruta_actual:
            asignaciones = asignaciones.exclude(id=item_ruta_actual.id)

        intervalos_ocupados = []
        for asignacion in asignaciones:
            programa_ot = asignacion.ruta.orden_trabajo.programaordentrabajo_set.first()
            if not programa_ot:
                continue

            # Obtener la prioridad de la OT
            prioridad_ot = programa_ot.prioridad
            
            programa = programa_ot.programa
            if not programa.fecha_inicio:
                continue

            calculo_tiempo = self.time_calculator.calculate_working_days(
                programa.fecha_inicio,
                asignacion.cantidad_pedido,
                asignacion.estandar if asignacion.estandar else 0
            )

            if 'error' not in calculo_tiempo and calculo_tiempo['intervals']:
                inicio = calculo_tiempo['intervals'][0]['fecha_inicio']
                fin = calculo_tiempo['next_available_time']
                
                self.logger.info(f"\nProceso encontrado:")
                self.logger.info(f"OT: {asignacion.ruta.orden_trabajo.codigo_ot}")
                self.logger.info(f"Proceso: {asignacion.proceso.descripcion}")
                self.logger.info(f"Prioridad: {prioridad_ot}")
                self.logger.info(f"Ocupación: {inicio} - {fin}")
                
                inicio_con_setup = inicio - TIEMPO_SETUP
                fin_con_setup = fin + TIEMPO_SETUP
                
                intervalos_ocupados.append({
                    'inicio': inicio_con_setup,
                    'fin': fin_con_setup,
                    'ot': asignacion.ruta.orden_trabajo.codigo_ot,
                    'proceso': asignacion.proceso.descripcion,
                    'prioridad': prioridad_ot,
                    'item_ruta': asignacion
                })

        # Ordenar intervalos por fecha de inicio y prioridad
        intervalos_ocupados.sort(key=lambda x: (x['inicio'], x['prioridad']))

        # Verificar conflictos considerando prioridades
        for intervalo in intervalos_ocupados:
            if fecha_inicio < intervalo['fin'] and fecha_fin > intervalo['inicio']:
                # Siempre detectar el conflicto, independientemente de la prioridad
                self.logger.warning(f"\n¡CONFLICTO DETECTADO!")
                self.logger.warning(f"Intervalo solicitado: {fecha_inicio} - {fecha_fin}")
                self.logger.warning(f"Conflicto con OT {intervalo['ot']} (Prioridad: {intervalo['prioridad']})")
                
                # Si la tarea actual tiene mayor prioridad, mover la tarea conflictiva
                if prioridad_actual is not None and prioridad_actual < intervalo['prioridad']:
                    self.logger.info(f"La tarea actual tiene mayor prioridad, ajustando tarea conflictiva")
                    # Mover la tarea conflictiva
                    nueva_fecha = fecha_fin + TIEMPO_SETUP
                    return False, nueva_fecha, intervalo['item_ruta']
                else:
                    # Mover la tarea actual
                    nueva_fecha = intervalo['fin'] + TIEMPO_SETUP
                    return False, nueva_fecha, None

        self.logger.info("\nNo se detectaron conflictos")
        return True, fecha_inicio, None

    def _procesar_asignacion(self, asignacion, intervalos_ocupados, es_programa_actual=False):
        """Helper para procesar una asignación y agregar sus intervalos"""
        programa_ot = asignacion.ruta.orden_trabajo.programaordentrabajo_set.first()
        if not programa_ot:
            return

        programa = programa_ot.programa
        if not programa.fecha_inicio:
            return

        # Calcular el intervalo específico para este proceso
        calculo_tiempo = self.time_calculator.calculate_working_days(
            programa.fecha_inicio,
            asignacion.cantidad_pedido,
            asignacion.estandar if asignacion.estandar else 0
        )

        if 'error' not in calculo_tiempo and calculo_tiempo['intervals']:
            inicio_proceso = calculo_tiempo['intervals'][0]['fecha_inicio']
            fin_proceso = calculo_tiempo['next_available_time']
            
            self.logger.info(f"\nProceso: {asignacion.proceso.descripcion}")
            self.logger.info(f"OT: {asignacion.ruta.orden_trabajo.codigo_ot}")
            self.logger.info(f"Ocupación: {inicio_proceso} - {fin_proceso}")
            if es_programa_actual:
                self.logger.info("(Asignación del programa actual)")
            
            intervalos_ocupados.append((inicio_proceso, fin_proceso))

    def ajustar_fechas_programa(self, programa):
        """Ajusta las fechas del programa considerando la disponibilidad de máquinas"""
        self.logger.info(f"\n{'='*50}")
        self.logger.info(f"INICIO DE VERIFICACIÓN - Programa {programa.id}")
        
        fecha_actual = programa.fecha_inicio
        if isinstance(fecha_actual, date):
            fecha_actual = datetime.combine(fecha_actual, self.time_calculator.WORKDAY_START)
        
        fecha_fin_programa = fecha_actual
        ajustes_necesarios = {}
        maquinas_timeline = {}
        ot_timeline = {}
        
        ordenes = ProgramaOrdenTrabajo.objects.filter(
            programa=programa
        ).select_related(
            'orden_trabajo',
            'orden_trabajo__ruta_ot'
        ).prefetch_related(
            'orden_trabajo__ruta_ot__items__maquina',
            'orden_trabajo__ruta_ot__items__proceso'
        ).order_by('prioridad')

        for prog_ot in ordenes:
            ot_fecha_inicial = programa.fecha_inicio
            if isinstance(ot_fecha_inicial, date):
                ot_fecha_inicial = datetime.combine(ot_fecha_inicial, self.time_calculator.WORKDAY_START)
            
            # Obtener todos los procesos de la OT ordenados por item
            procesos_ot = list(prog_ot.orden_trabajo.ruta_ot.items.all().order_by('item'))
            proceso_fechas = {}  # Diccionario para mantener las fechas de cada proceso
            
            for i, item_ruta in enumerate(procesos_ot):
                if not item_ruta.maquina or not item_ruta.estandar:
                    continue

                # La fecha de inicio debe considerar:
                # 1. La fecha del proceso anterior si existe
                # 2. La última fecha conocida de la máquina
                fecha_inicio = ot_fecha_inicial
                if i > 0:  # Si hay proceso anterior
                    proceso_anterior = procesos_ot[i-1]
                    if proceso_anterior.id in proceso_fechas:
                        fecha_inicio = proceso_fechas[proceso_anterior.id]

                # También considerar la disponibilidad de la máquina
                if item_ruta.maquina.id in maquinas_timeline:
                    fecha_inicio = max(fecha_inicio, maquinas_timeline[item_ruta.maquina.id])

                fecha_inicio = fecha_inicio + timedelta(minutes=30)  # Setup time

                calculo_tiempo = self.time_calculator.calculate_working_days(
                    fecha_inicio,
                    item_ruta.cantidad_pedido,
                    item_ruta.estandar
                )

                if 'error' in calculo_tiempo:
                    continue

                fecha_fin_estimada = calculo_tiempo['next_available_time']
                if isinstance(fecha_fin_estimada, date):
                    fecha_fin_estimada = datetime.combine(fecha_fin_estimada, self.time_calculator.WORKDAY_END)
                
                disponible, proxima_fecha, _ = self.verificar_disponibilidad_maquina(
                    item_ruta.maquina,
                    fecha_inicio,
                    fecha_fin_estimada,
                    programa,
                    item_ruta,
                    prog_ot.prioridad
                )

                if not disponible:
                    key = f"{item_ruta.id}"
                    if key not in ajustes_necesarios:
                        if isinstance(proxima_fecha, date):
                            proxima_fecha = datetime.combine(proxima_fecha, self.time_calculator.WORKDAY_START)
                        
                        ajustes_necesarios[key] = {
                            'item_ruta': item_ruta,
                            'fecha_original': fecha_inicio,
                            'fecha_ajustada': proxima_fecha,
                            'maquina': item_ruta.maquina,
                            'proceso': item_ruta.proceso,
                            'orden_trabajo': prog_ot.orden_trabajo.codigo_ot,
                            'prioridad': prog_ot.prioridad
                        }
                        
                        # Recalcular con la nueva fecha
                        calculo_tiempo = self.time_calculator.calculate_working_days(
                            proxima_fecha,
                            item_ruta.cantidad_pedido,
                            item_ruta.estandar
                        )
                        fecha_fin_estimada = calculo_tiempo['next_available_time']

                # Actualizar las fechas para este proceso
                proceso_fechas[item_ruta.id] = fecha_fin_estimada + timedelta(minutes=30)
                
                # Actualizar timeline de máquina
                maquinas_timeline[item_ruta.maquina.id] = fecha_fin_estimada + timedelta(minutes=30)

                # Actualizar fecha fin del programa si es necesario
                if fecha_fin_estimada > fecha_fin_programa:
                    fecha_fin_programa = fecha_fin_estimada

                # Propagar el ajuste a todos los procesos posteriores de la misma OT
                for proceso_posterior in procesos_ot[i+1:]:
                    if proceso_posterior.id not in proceso_fechas:
                        proceso_fechas[proceso_posterior.id] = fecha_fin_estimada + timedelta(minutes=30)

        if isinstance(fecha_fin_programa, date):
            fecha_fin_programa = datetime.combine(fecha_fin_programa, self.time_calculator.WORKDAY_END)

        return fecha_fin_programa, list(ajustes_necesarios.values())

    def calcular_carga_maquina(self, maquina, programa):
        """Calcula la carga real de una máquina para un programa específico"""
        carga_total = 0
        desglose_ots = []
        
        # Obtener todas las tareas de la máquina en este programa
        items_ruta = ItemRuta.objects.filter(
            maquina=maquina,
            ruta__orden_trabajo__programaordentrabajo__programa=programa
        ).select_related(
            'ruta__orden_trabajo',
            'proceso'
        )

        for item in items_ruta:
            # Cálculo real del tiempo basado en cantidad y estándar
            if item.estandar and item.estandar > 0:
                horas_proceso = item.cantidad_pedido / item.estandar
                
                desglose_ots.append({
                    'ot_codigo': item.ruta.orden_trabajo.codigo_ot,  # Cambiar 'ot' a 'ot_codigo'
                    'proceso': item.proceso.descripcion if item.proceso else 'Sin proceso',
                    'tiempo_estimado': round(horas_proceso, 2)  # Cambiar 'horas' a 'tiempo_estimado'
                })
                
                carga_total += horas_proceso

        return {
            'carga_total': round(carga_total, 2),
            'desglose': desglose_ots
        }
