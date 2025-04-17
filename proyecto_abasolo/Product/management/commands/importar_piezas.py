from django.core.management.base import BaseCommand
from Product.models import Pieza, MeasurementUnit, FamiliaProducto, SubfamiliaProducto
import csv

class Command(BaseCommand):
    help = 'Importar datos desde un archivo .txt'

    def handle(self, *args, **kwargs):
        path_file = 'W:\\mae_piezas.txt'
        encodings_to_try = ['utf-8', 'latin-1']

        for encoding in encodings_to_try:
            try:
                with open(path_file, 'r', encoding=encoding) as file:
                    reader = csv.reader(file, delimiter=';')
                    next(reader)

                    for row in reader:
                        try:
                            if len(row) != 4: 
                                self.stdout.write(self.style.ERROR(f'Fila inválida: {row}'))
                                continue

                            codigo_pieza = row[0].strip()
                            descripcion = row[1].strip()
                            unidad_medida_codigo = row[2].strip()

                            try:
                                peso = float(row[3].strip())
                            except ValueError:
                                self.stdout.write(self.style.ERROR(f'Error al convertir el peso en la fila: {row}'))
                                continue

                            unidad_medida, _ = MeasurementUnit.objects.get_or_create(codigo_und_medida=unidad_medida_codigo)

                            codigo_familia = codigo_pieza[:2]
                            familia_producto, _ = FamiliaProducto.objects.get_or_create(codigo_familia=codigo_familia)

                            codigo_subfamilia = codigo_pieza[:5]
                            subfamilia_producto, _ = SubfamiliaProducto.objects.get_or_create(codigo_subfamilia=codigo_subfamilia, familia_producto=familia_producto)

                            pieza, creado = Pieza.objects.update_or_create(
                                codigo_pieza=codigo_pieza,
                                defaults={
                                    'descripcion': descripcion,
                                    'und_medida': unidad_medida,
                                    'peso_unitario': peso,
                                    'familia_producto': familia_producto,
                                    'subfamilia_producto': subfamilia_producto
                                }
                            )

                            if creado:
                                self.stdout.write(self.style.SUCCESS(f'Pieza {codigo_pieza} creada.'))
                            else:
                                self.stdout.write(self.style.SUCCESS(f'Pieza {codigo_pieza} actualizada.'))

                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'Error en la fila {row}: {str(e)}'))
                break
            except UnicodeDecodeError:
                continue

        self.stdout.write(self.style.SUCCESS('Piezas cargadas/actualizadas correctamente.'))