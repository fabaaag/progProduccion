from django.core.management.base import BaseCommand
from django.db import transaction
from JobManagement.models import ProgramaProduccion, TareaFragmentada, ReporteDiarioPrograma, ProgramaOrdenTrabajo
from JobManagement.services.production_scheduler import ProductionScheduler
from JobManagement.services.time_calculations import TimeCalculator
import logging
import os
from datetime import datetime

class Command(BaseCommand):
    help = 'Genera tareas fragmentadas y reportes diarios para programas existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--programa_id',
            type=int,
            help='ID específico de un programa (opcional)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la regeneración incluso si ya existen tareas'
        )
        parser.add_argument(
            '--log-file',
            type=str,
            help='Archivo para guardar el log detallado (opcional)',
            default='tareas_fragmentadas.log'
        )

    def setup_logging(self, log_file):
        """Configura el logging para el comando"""
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def handle(self, *args, **options):
        # Configurar logging
        log_file = options['log_file']
        self.setup_logging(log_file)
        
        scheduler = ProductionScheduler(TimeCalculator())
        programa_id = options['programa_id']
        force = options['force']
        
        resumen = {
            'programas_procesados': 0,
            'tareas_creadas': 0,
            'reportes_creados': 0,
            'errores': [],  # Ahora guardamos los errores completos
            'programas_con_error': []  # Lista de programas que fallaron
        }

        try:
            if programa_id:
                programas = ProgramaProduccion.objects.filter(id=programa_id)
                mensaje = f"Procesando programa específico ID: {programa_id}"
            else:
                programas = ProgramaProduccion.objects.all()
                mensaje = f"Procesando {programas.count()} programas"
            
            self.logger.info(mensaje)
            self.stdout.write(mensaje)

            for programa in programas:
                try:
                    with transaction.atomic():
                        mensaje_programa = f"Procesando programa {programa.id} - {programa.nombre}"
                        self.logger.info(mensaje_programa)
                        self.stdout.write(mensaje_programa)

                        # Verificar si ya existen tareas fragmentadas
                        tareas_existentes = TareaFragmentada.objects.filter(programa=programa).exists()
                        if tareas_existentes:
                            if force:
                                # Registrar cantidad de registros eliminados
                                tareas_count = TareaFragmentada.objects.filter(programa=programa).count()
                                reportes_count = ReporteDiarioPrograma.objects.filter(programa=programa).count()
                                
                                TareaFragmentada.objects.filter(programa=programa).delete()
                                ReporteDiarioPrograma.objects.filter(programa=programa).delete()
                                
                                self.logger.info(f"Eliminados {tareas_count} tareas y {reportes_count} reportes existentes")
                            else:
                                mensaje_skip = f"Programa {programa.id} omitido (ya tiene tareas)"
                                self.logger.info(mensaje_skip)
                                continue

                        # Obtener y registrar información de las OTs
                        programa_ots = ProgramaOrdenTrabajo.objects.filter(programa=programa)
                        self.logger.info(f"Procesando {programa_ots.count()} órdenes de trabajo")

                        ordenes_trabajo = []
                        for pot in programa_ots:
                            ot = pot.orden_trabajo
                            self.logger.info(f"Procesando OT: {ot.codigo_ot}")

                            if not ot.ruta_ot:
                                self.logger.warning(f"OT {ot.codigo_ot} sin ruta definida")
                                continue

                            procesos_validos = []
                            procesos_invalidos = []
                            
                            for item in ot.ruta_ot.items.all().order_by('item'):
                                if not item.estandar or not item.cantidad_pedido:
                                    procesos_invalidos.append({
                                        'id': item.id,
                                        'estandar': item.estandar,
                                        'cantidad': item.cantidad_pedido
                                    })
                                    continue
                                
                                proceso_data = {
                                    'id': item.id,
                                    'item': item.item,
                                    'descripcion': item.proceso.descripcion if item.proceso else None,
                                    'maquina_id': item.maquina.id if item.maquina else None,
                                    'cantidad': item.cantidad_pedido,
                                    'estandar': item.estandar,
                                    'prioridad': pot.prioridad
                                }
                                procesos_validos.append(proceso_data)

                            if procesos_invalidos:
                                self.logger.warning(
                                    f"OT {ot.codigo_ot} tiene {len(procesos_invalidos)} procesos inválidos: "
                                    f"{procesos_invalidos}"
                                )

                            if procesos_validos:
                                ordenes_trabajo.append({
                                    'orden_trabajo': ot.id,
                                    'orden_trabajo_codigo_ot': ot.codigo_ot,
                                    'orden_trabajo_descripcion_producto_ot': ot.descripcion_producto_ot,
                                    'procesos': procesos_validos
                                })

                        # Crear nuevas tareas fragmentadas
                        if scheduler.create_fragmented_tasks(programa, ordenes_trabajo):
                            resumen['programas_procesados'] += 1
                            nuevas_tareas = TareaFragmentada.objects.filter(programa=programa).count()
                            nuevos_reportes = ReporteDiarioPrograma.objects.filter(programa=programa).count()
                            
                            resumen['tareas_creadas'] += nuevas_tareas
                            resumen['reportes_creados'] += nuevos_reportes
                            
                            self.logger.info(
                                f"Programa {programa.id} procesado exitosamente: "
                                f"{nuevas_tareas} tareas, {nuevos_reportes} reportes"
                            )
                        else:
                            error_msg = f"Error al crear tareas fragmentadas para programa {programa.id}"
                            resumen['errores'].append(error_msg)
                            resumen['programas_con_error'].append(programa.id)
                            self.logger.error(error_msg)

                except Exception as e:
                    error_msg = f"Error procesando programa {programa.id}: {str(e)}"
                    resumen['errores'].append(error_msg)
                    resumen['programas_con_error'].append(programa.id)
                    self.logger.error(error_msg, exc_info=True)

            # Mostrar y registrar resumen
            self.logger.info("\nResumen de la operación:")
            self.logger.info(f"Programas procesados: {resumen['programas_procesados']}")
            self.logger.info(f"Tareas fragmentadas creadas: {resumen['tareas_creadas']}")
            self.logger.info(f"Reportes diarios creados: {resumen['reportes_creados']}")
            self.logger.info(f"Errores encontrados: {len(resumen['errores'])}")
            
            if resumen['errores']:
                self.logger.error("\nDetalle de errores:")
                for error in resumen['errores']:
                    self.logger.error(error)
                
                self.logger.error("\nProgramas con error:")
                self.logger.error(f"IDs: {', '.join(map(str, resumen['programas_con_error']))}")

            # Mostrar ubicación del archivo de log
            self.stdout.write(f"\nLog detallado guardado en: {os.path.abspath(log_file)}")

        except Exception as e:
            error_general = f"Error general: {str(e)}"
            self.logger.error(error_general, exc_info=True)
            self.stdout.write(self.style.ERROR(error_general))
