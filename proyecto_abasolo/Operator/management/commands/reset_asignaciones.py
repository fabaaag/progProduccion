from django.core.management.base import BaseCommand
from django.db import connection
from Operator.models import AsignacionOperador

class Command(BaseCommand):
    help = 'Elimina todas las asignaciones y reinicia la secuencia de IDs'

    def handle(self, *args, **options):
        # Contar asignaciones antes de eliminar
        count_before = AsignacionOperador.objects.count()
        self.stdout.write(f"Encontradas {count_before} asignaciones")
        
        # Eliminar todas las asignaciones
        AsignacionOperador.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Todas las asignaciones han sido eliminadas"))
        
        # Reiniciar la secuencia
        with connection.cursor() as cursor:
            if connection.vendor == 'postgresql':
                cursor.execute("ALTER SEQUENCE operator_asignacionoperador_id_seq RESTART WITH 1;")
                self.stdout.write(self.style.SUCCESS("Secuencia de PostgreSQL reiniciada"))
            elif connection.vendor == 'mysql':
                cursor.execute("ALTER TABLE operator_asignacionoperador AUTO_INCREMENT = 1;")
                self.stdout.write(self.style.SUCCESS("Auto-incremento de MySQL reiniciado"))
            elif connection.vendor == 'sqlite':
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='operator_asignacionoperador';")
                self.stdout.write(self.style.SUCCESS("Secuencia de SQLite reiniciada"))
            else:
                self.stdout.write(self.style.WARNING(f"No se pudo reiniciar la secuencia para {connection.vendor}"))