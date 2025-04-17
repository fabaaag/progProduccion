from django.core.management.base import BaseCommand
from JobManagement.models import OrdenTrabajo, ProgramaOrdenTrabajo

class Command(BaseCommand):
    help = 'Verifica el estado de asignación de las órdenes de trabajo'

    def handle(self, *args, **kwargs):
        #Obtener todas las ordenes
        all_orders = OrdenTrabajo.objects.all()
        self.stdout.write(f"Total de órdenes: {all_orders.count()}")

        #Obtener órdenes asignadas
        assigned_orders = OrdenTrabajo.objects.filter(
            id__in=ProgramaOrdenTrabajo.objects.values_list('orden_trabajo_id', flat=True)
        )
        self.stdout.write(f"Órdenes asignadas: {assigned_orders.count()}")
        
        #Obtener órdenes no asignadas
        unassigned_orders = OrdenTrabajo.objects.exclude(
            id__in=ProgramaOrdenTrabajo.objects.values_list('orden_trabajo_id', flat=True)
        )
        self.stdout.write(f"Órdenes no asignadas: {unassigned_orders.count()}")

        #Mostrar detalles de cada orden
        self.stdout.write("\nDetalles de órdenes asignadas:")
        for orden in assigned_orders:
            programas = ProgramaOrdenTrabajo.objects.filter(orden_trabajo=orden)
            self.stdout.write(f"OT {orden.codigo_ot} - Asignada a programa: {[p.programa.id for p in programas]}")

        self.stdout.write("\nDetalles de órdenes no programadas:")
        for orden in unassigned_orders:
            self.stdout.write(f"OT {orden.codigo_ot} - No asignada")