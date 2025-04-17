from django.core.management.base import BaseCommand
from Product.models import FamiliaProducto
import csv

class Command(BaseCommand):
    help = 'Importar familias desde el  famprod.csv'

    def handle(self, *args, **kwargs):
        path_file = 'W:\\famprod.csv'
        encodings_to_try = ['utf-8', 'latin-1']

        for encoding in encodings_to_try:
            try:
                with open(path_file, 'r', encoding=encoding) as file:
                    reader = csv.reader(file, delimiter=';')

                    for row in reader:
                        try:
                            if len(row) < 2:
                                self.stdout.write(self.style.ERROR(f'Fila inválida o incompleta: {row}'))
                                continue

                            codigo_familia = row[0].strip()
                            descripcion = row[1].strip()

                            FamiliaProducto.objects.update_or_create(codigo_familia=codigo_familia, defaults={'descripcion':descripcion})

                            self.stdout.write(self.style.SUCCESS(f'Familia {codigo_familia} procesada.'))

                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'Error procesando la fila {row}: {e}'))
                break
            
            except UnicodeDecodeError:
                continue
        
        self.stdout.write(self.style.SUCCESS('Importacion de familias completada exitósamente.'))