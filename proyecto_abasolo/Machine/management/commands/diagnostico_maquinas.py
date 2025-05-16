from django.core.management.base import BaseCommand
from JobManagement.models import Maquina, ItemRuta, ProgramaProduccion, RutaOT
from Machine.models import EstadoMaquina, EstadoOperatividad
from django.db.models import Count, Q
from datetime import datetime, timedelta
import os

class Command(BaseCommand):
    help = 'Realiza un diagnóstico del estado actual de las máquinas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            default='diagnostico_maquinas.txt',
            help='Nombre del archivo de salida'
        )

    def write_to_file(self, file, message, style_func=None):
        # Escribir al archivo y también mostrar en consola
        if style_func:
            self.stdout.write(style_func(message))
        else:
            self.stdout.write(message)
        file.write(message + '\n')

    def handle(self, *args, **options):
        # Crear directorio para reportes si no existe
        output_dir = 'reportes_diagnostico'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f'diagnostico_maquinas_{timestamp}.txt')

        with open(filename, 'w', encoding='utf-8') as f:
            self.write_to_file(f, f"\n=== Diagnóstico de Máquinas ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===\n")
            
            # Estadísticas generales
            total_maquinas = Maquina.objects.count()
            maquinas_con_estado = EstadoMaquina.objects.count()
            self.write_to_file(f, f"Total máquinas: {total_maquinas}")
            self.write_to_file(f, f"Máquinas con estado asignado: {maquinas_con_estado}")
            self.write_to_file(f, f"Máquinas sin estado: {total_maquinas - maquinas_con_estado}\n")

            # Obtener todas las máquinas
            maquinas = Maquina.objects.all().order_by('codigo_maquina')
            
            for maquina in maquinas:
                self.write_to_file(f, f"\n{'='*50}")
                self.write_to_file(f, f"Máquina: {maquina.codigo_maquina} - {maquina.descripcion}")
                self.write_to_file(f, f"Sigla: {maquina.sigla}")
                
                # Verificar estado
                try:
                    estado = EstadoMaquina.objects.get(maquina=maquina)
                    self.write_to_file(f, "\nEstado:")
                    self.write_to_file(f, f"  • Operatividad: {estado.estado_operatividad.get_estado_display()}")
                    self.write_to_file(f, f"  • Capacidad/hora: {estado.capacidad_hora or 'No definida'}")
                    self.write_to_file(f, f"  • Factor eficiencia: {estado.factor_eficiencia}")
                    self.write_to_file(f, f"  • Horario: {estado.hora_inicio_normal} - {estado.hora_fin_normal}")
                    
                    # Verificar tipos de máquina asignados
                    tipos = estado.tipos_maquina.all()
                    if tipos.exists():
                        self.write_to_file(f, "\nTipos de máquina:")
                        for tipo in tipos:
                            self.write_to_file(f, f"  • {tipo.codigo} - {tipo.descripcion}")
                    else:
                        self.write_to_file(f, "\n⚠️ Sin tipos de máquina asignados")
                except EstadoMaquina.DoesNotExist:
                    self.write_to_file(f, "\n⚠️ Sin estado asignado")
                
                # Verificar asignaciones actuales
                fecha_actual = datetime.now().date()
                rutas_ot = RutaOT.objects.filter(
                    items__maquina=maquina
                ).distinct()
                
                programas_activos = ProgramaProduccion.objects.filter(
                    programaordentrabajo__orden_trabajo__in=rutas_ot.values('orden_trabajo'),
                    fecha_fin__gte=fecha_actual
                ).distinct()
                
                items_ruta = ItemRuta.objects.filter(
                    maquina=maquina,
                    ruta__in=rutas_ot,
                    ruta__orden_trabajo__programaordentrabajo__programa__in=programas_activos
                )
                
                self.write_to_file(f, "\nAsignaciones actuales:")
                self.write_to_file(f, f"  • Programas activos: {programas_activos.count()}")
                self.write_to_file(f, f"  • Procesos asignados: {items_ruta.count()}")
                
                if programas_activos.exists():
                    self.write_to_file(f, "\nDetalle por programa:")
                    for programa in programas_activos:
                        items_programa = items_ruta.filter(
                            ruta__orden_trabajo__programaordentrabajo__programa=programa
                        )
                        self.write_to_file(f, f"\n  Programa: {programa.nombre}")
                        self.write_to_file(f, f"  Fecha: {programa.fecha_inicio} - {programa.fecha_fin}")
                        self.write_to_file(f, f"  Procesos: {items_programa.count()}")
                        
                        for item in items_programa:
                            self.write_to_file(f, f"    • {item.proceso.descripcion}")
                            self.write_to_file(f, f"      - Estándar: {item.estandar}")
                            self.write_to_file(f, f"      - Cantidad pedido: {item.cantidad_pedido}")
                            self.write_to_file(f, f"      - Completado: {item.cantidad_terminado_proceso}")
                            
                # Verificar disponibilidad
                from Machine.models import DisponibilidadMaquina
                disponibilidad_hoy = DisponibilidadMaquina.objects.filter(
                    maquina=maquina,
                    fecha=fecha_actual
                ).first()
                
                self.write_to_file(f, "\nDisponibilidad:")
                if disponibilidad_hoy:
                    self.write_to_file(f, f"  • Disponible hoy: {'Sí' if disponibilidad_hoy.disponible else 'No'}")
                    if not disponibilidad_hoy.disponible:
                        self.write_to_file(f, f"  • Motivo: {disponibilidad_hoy.motivo_no_disponible}")
                else:
                    self.write_to_file(f, "  • Sin información de disponibilidad para hoy")

            self.stdout.write(self.style.SUCCESS(f"\nReporte generado exitosamente en: {filename}"))