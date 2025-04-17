from django.core.management.base import BaseCommand
from Machine.models import TipoMaquina, EstadoMaquina, EstadoOperatividad
from JobManagement.models import Proceso
from django.db import connection

class Command(BaseCommand):
    help = 'Reset completo de los modelos de tipos de máquinas y sus relaciones'

    def table_exists(self, table_name):
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM sqlite_master 
                WHERE type='table' AND name='{table_name}';
            """)
            return cursor.fetchone()[0] > 0

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando reset completo de datos...'))

        try:
            # 1. Verificar existencia de tablas
            tables = {
                'proceso_tipos': 'JobManagement_proceso_tipos_maquina_compatibles',
                'estado_tipos': 'Machine_estadomaquina_tipos_maquina',
                'tipo_maquina': 'Machine_tipomaquina',
                'estado_maquina': 'Machine_estadomaquina'
            }

            existing_tables = {
                name: self.table_exists(table)
                for name, table in tables.items()
            }

            # 2. Limpiar en orden correcto
            if existing_tables['proceso_tipos']:
                self.stdout.write('Limpiando relaciones proceso-tipo...')
                with connection.cursor() as cursor:
                    cursor.execute(f'DELETE FROM {tables["proceso_tipos"]};')
                self.stdout.write(self.style.SUCCESS('✓ Relaciones proceso-tipo eliminadas'))

            if existing_tables['estado_tipos']:
                self.stdout.write('Limpiando relaciones estado-tipo...')
                with connection.cursor() as cursor:
                    cursor.execute(f'DELETE FROM {tables["estado_tipos"]};')
                self.stdout.write(self.style.SUCCESS('✓ Relaciones estado-tipo eliminadas'))

            if existing_tables['estado_maquina']:
                self.stdout.write('Limpiando estados de máquina...')
                EstadoMaquina.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('✓ Estados de máquina eliminados'))

            if existing_tables['tipo_maquina']:
                self.stdout.write('Limpiando tipos de máquina...')
                TipoMaquina.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('✓ Tipos de máquina eliminados'))

            # 3. Resumen final
            self.stdout.write('\nEstado final de las tablas:')
            for name, exists in existing_tables.items():
                status = '✓ Limpiada' if exists else '⚠ No existía'
                self.stdout.write(f'{name}: {status}')

            self.stdout.write(self.style.SUCCESS('\nReset completado exitosamente'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\nError durante el reset: {str(e)}')
            )