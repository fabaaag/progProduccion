from django.core.management.base import BaseCommand
from JobManagement.models import ProgramaOrdenTrabajo, ProgramaProduccion

class Command(BaseCommand):
    help = 'Limpia las relaciones huérfanas en ProgramaOrdenTrabajo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry_run',
            action='store_true',
            help='Muestra qué se eliminaría sin realizar cambios',
        )

    def handle(self, *args, **kwargs):
        relaciones_huerfanas = ProgramaOrdenTrabajo.objects.filter(programa__isnull=True)

        self.stdout.write(
            self.style.WARNING(f"Encontradas {relaciones_huerfanas.count()} relaciones huérfanas")
        )

        if kwargs['dry_run']:
            self.stdout.write(self.style.NOTICE("Modo dry-run activado - No se realizarán cambios"))
            for relacion in relaciones_huerfanas:
                self.stdout.write(
                    f"Se eliminaría relación huérfana para OT: {relacion.orden_trabajo.codigo_ot}"
                )
        else:
            for relacion in relaciones_huerfanas:
                self.stdout.write(
                    f"Eliminando relación huérfana para OT: {relacion.orden_trabajo.codigo_ot}"
                )
                relacion.delete()
        self.stdout.write(self.style.SUCCESS("Proceso completado"))
