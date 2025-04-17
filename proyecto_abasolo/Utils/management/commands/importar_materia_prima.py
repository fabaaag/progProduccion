from django.core.management.base import BaseCommand
from Product.models import MeasurementUnit, MateriaPrima
import csv

class Command(BaseCommand):
    help = 'Importar datos desde el archivo mprima.txt'

    def handle(self, *args, **kwargs):
        path_file = 'W:\\mprima.txt'
        encodings_to_try = ['utf-8', 'latin-1']

        for encoding in encodings_to_try:
            try:
                with open(path_file, 'r', encoding=encoding) as file:
                    reader = csv.reader(file, delimiter="@")

                    for row in reader:
                        try:
                            if len(row) != 3:
                                self.stdout.write(self.style.ERROR(f'Fila inválida: {row}'))
                                continue

                            codigo_mprima = row[0].strip()
                            nombre = row[1].strip()
                            unidad_medida_codigo = row[2].strip()

                            unidad_medida, _ = MeasurementUnit.objects.get_or_create(codigo_und_medida=unidad_medida_codigo)

                            materia_prima, created = MateriaPrima.objects.update_or_create(
                                codigo = codigo_mprima,
                                defaults={
                                    'nombre': nombre,
                                    'unidad_medida': unidad_medida,
                                }
                            )
                            
                            if created:
                                self.stdout.write(self.style.SUCCESS(f'Materia Prima {nombre} creada.'))
                            else:
                                self.stdout.write(self.style.SUCCESS(f'Materia Prima {nombre} actualizada.'))
                        
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'Error en la fila {row}:  {str(e)}'))
                    break
            except UnicodeDecodeError:
                continue
        
        self.stdout.write(self.style.SUCCESS("Materias primas cargadas/actualizadas exitósamente."))