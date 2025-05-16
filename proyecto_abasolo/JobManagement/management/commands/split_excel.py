from django.core.management.base import BaseCommand
import pandas as pd
import os
from datetime import datetime
from django.conf import settings

class Command(BaseCommand):
    help = 'Divide un archivo Excel de programación en múltiples archivos CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            'ruta_excel',
            type=str,
            help='Ruta al archivo Excel que se desea procesar'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='excel_exports',
            help='Directorio donde se guardarán los archivos CSV'
        )

    def handle(self, *args, **options):
        try:
            # Obtener la ruta base del proyecto
            base_dir = settings.BASE_DIR
            
            # Construir rutas absolutas
            ruta_excel = os.path.abspath(os.path.join(base_dir, '..', options['ruta_excel']))
            output_dir = os.path.abspath(os.path.join(base_dir, options['output_dir']))
            
            # Verificar si el archivo existe
            if not os.path.exists(ruta_excel):
                self.stdout.write(
                    self.style.ERROR(f'El archivo no existe en la ruta: {ruta_excel}')
                )
                self.stdout.write(
                    self.style.WARNING('Por favor, verifica la ruta del archivo Excel')
                )
                return

            # Crear directorio de salida si no existe
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.stdout.write(
                    self.style.SUCCESS(f'Directorio creado: {output_dir}')
                )

            # Timestamp para el subdirectorio
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_dir = os.path.join(output_dir, f'export_{timestamp}')
            os.makedirs(export_dir)

            # Mostrar información de las rutas
            self.stdout.write(
                self.style.WARNING(f'Procesando archivo: {ruta_excel}')
            )
            self.stdout.write(
                self.style.WARNING(f'Directorio de salida: {export_dir}')
            )

            # Leer el archivo Excel
            excel_file = pd.ExcelFile(ruta_excel)
            hojas = [hoja for hoja in excel_file.sheet_names 
                    if hoja not in ['PROD-KGS', 'STD', 'VIP']]

            for hoja in hojas:
                try:
                    df = pd.read_excel(ruta_excel, sheet_name=hoja)
                    nombre_archivo = f"{hoja.replace(' ', '_').replace('/', '_')}.csv"
                    ruta_archivo = os.path.join(export_dir, nombre_archivo)
                    df.to_csv(ruta_archivo, index=False, encoding='utf-8')
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Hoja "{hoja}" exportada como: {nombre_archivo}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error al procesar la hoja "{hoja}": {str(e)}')
                    )

            self.stdout.write(
                self.style.SUCCESS(f'Proceso completado. Archivos guardados en: {export_dir}')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error en el proceso: {str(e)}')
            )