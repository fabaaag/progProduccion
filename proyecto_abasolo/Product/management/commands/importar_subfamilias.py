from django.core.management.base import BaseCommand
from Product.models import SubfamiliaProducto, FamiliaProducto
import csv

class Command(BaseCommand):
    help = 'Importar subfamilias desde el archivo subgrupos.csv'

    def handle(self, *args, **kwargs):
        path_file = 'W:\\subgrupos.csv'
        encodings_to_try = ['utf-8', 'latin-1']

        for encoding in encodings_to_try:
            try:
                with open(path_file, 'r', encoding=encoding) as file:
                    reader = csv.reader(file, delimiter=';')

                    for row in reader:
                        try:
                            if len(row) != 3:
                                self.stdout.write(self.style.ERROR(f'Fila inválida: {row}'))
                                continue

                            codigo_subfamilia = row[0].strip()
                            descripcion = row[1].strip()

                            #Extraer el codigo de familia de los primeros dos digitos del codigo subfamilia
                            codigo_familia = codigo_subfamilia[:2]

                            familia, _ = FamiliaProducto.objects.get_or_create(codigo_familia=codigo_familia)

                            #Actualiza o crea la subfamilia
                            subfamilia, created = SubfamiliaProducto.objects.update_or_create(
                                codigo_subfamilia=codigo_subfamilia,
                                defaults={
                                    'descripcion': descripcion,
                                    'familia_producto': familia,
                                }
                            )

                            if created:
                                self.stdout.write(self.style.SUCCESS(f'Subfamilia {codigo_subfamilia} creada.'))
                            else:
                                self.stdout.write(self.style.SUCCESS(f'Subfamilia {codigo_subfamilia} actualizada.'))

                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'Error en la fila {row}: {str(e)}'))
                break
            
            except UnicodeDecodeError:
                continue

        self.stdout.write(self.style.SUCCESS('Subfamilias cargadas o actualizadas exitosamente.'))
        