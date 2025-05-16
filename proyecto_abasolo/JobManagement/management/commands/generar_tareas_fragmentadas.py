from django.core.management.base import BaseCommand
from django.db import transaction
from JobManagement.models import ProgramaProduccion, TareaFragmentada, ReporteDiarioPrograma, ProgramaOrdenTrabajo
from JobManagement.services.production_scheduler import ProductionScheduler
from JobManagement.services.time_calculations import TimeCalculator

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

    def handle(self, *args, **options):
        scheduler = ProductionScheduler(TimeCalculator())
        programa_id = options['programa_id']
        force = options['force']
        
        resumen = {
            'programas_procesados': 0,
            'tareas_creadas': 0,
            'reportes_creados': 0,
            'errores': 0
        }

        try:
            if programa_id:
                programas = ProgramaProduccion.objects.filter(id=programa_id)
                if not programas.exists():
                    self.stdout.write(
                        self.style.ERROR(f"No se encontró el programa con ID {programa_id}")
                    )
                    return
            else:
                programas = ProgramaProduccion.objects.all()
                self.stdout.write(f"Se procesarán {programas.count()} programas")

            for programa in programas:
                try:
                    with transaction.atomic():
                        self.stdout.write(f"Procesando programa {programa.id} - {programa.nombre}")

                        # Verificar si ya existen tareas fragmentadas
                        tareas_existentes = TareaFragmentada.objects.filter(programa=programa).exists()
                        if tareas_existentes and not force:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"El programa {programa.id} ya tiene tareas fragmentadas. "
                                    "Use --force para regenerar"
                                )
                            )
                            continue

                        # Obtener las órdenes de trabajo usando ProgramaOrdenTrabajo
                        programa_ots = ProgramaOrdenTrabajo.objects.filter(
                            programa=programa
                        ).select_related(
                            'orden_trabajo',
                            'orden_trabajo__ruta_ot'
                        ).prefetch_related(
                            'orden_trabajo__ruta_ot__items',
                            'orden_trabajo__ruta_ot__items__proceso',
                            'orden_trabajo__ruta_ot__items__maquina'
                        )

                        ordenes_trabajo = []
                        for pot in programa_ots:
                            ot = pot.orden_trabajo
                            self.stdout.write(f"  Procesando OT: {ot.codigo_ot}")

                            ot_data = {
                                'orden_trabajo': ot.id,
                                'orden_trabajo_codigo_ot': ot.codigo_ot,
                                'orden_trabajo_descripcion_producto_ot': ot.descripcion_producto_ot,
                                'procesos': []
                            }

                            if ot.ruta_ot:
                                for item in ot.ruta_ot.items.all().order_by('item'):
                                    if not item.estandar or not item.cantidad_pedido:
                                        self.stdout.write(
                                            self.style.WARNING(
                                                f"    Proceso {item.id} sin estándar o cantidad"
                                            )
                                        )
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
                                    ot_data['procesos'].append(proceso_data)
                                    self.stdout.write(f"    Proceso {item.id} preparado")

                            ordenes_trabajo.append(ot_data)

                        # Si es force, eliminar tareas y reportes existentes
                        if force and tareas_existentes:
                            TareaFragmentada.objects.filter(programa=programa).delete()
                            ReporteDiarioPrograma.objects.filter(programa=programa).delete()
                            self.stdout.write("  Datos existentes eliminados")

                        # Crear nuevas tareas fragmentadas
                        if scheduler.create_fragmented_tasks(programa, ordenes_trabajo):
                            resumen['programas_procesados'] += 1
                            resumen['tareas_creadas'] += TareaFragmentada.objects.filter(programa=programa).count()
                            resumen['reportes_creados'] += ReporteDiarioPrograma.objects.filter(programa=programa).count()
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Tareas fragmentadas creadas exitosamente para programa {programa.id}"
                                )
                            )
                        else:
                            resumen['errores'] += 1
                            self.stdout.write(
                                self.style.ERROR(
                                    f"Error al crear tareas fragmentadas para programa {programa.id}"
                                )
                            )

                except Exception as e:
                    resumen['errores'] += 1
                    self.stdout.write(
                        self.style.ERROR(f"Error procesando programa {programa.id}: {str(e)}")
                    )

            # Mostrar resumen
            self.stdout.write("\nResumen de la operación:")
            self.stdout.write(f"Programas procesados: {resumen['programas_procesados']}")
            self.stdout.write(f"Tareas fragmentadas creadas: {resumen['tareas_creadas']}")
            self.stdout.write(f"Reportes diarios creados: {resumen['reportes_creados']}")
            self.stdout.write(f"Errores encontrados: {resumen['errores']}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error general: {str(e)}"))
