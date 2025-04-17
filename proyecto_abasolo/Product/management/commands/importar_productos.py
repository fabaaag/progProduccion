from django.core.management.base import BaseCommand
from django.utils.encoding import force_bytes
from Product.models import *
import csv

class Command(BaseCommand):
    help = 'Importar datos desde un archivo.txt'

    def handle(self, *args, **kwargs):
        path_file = 'W:\\mae_prod.txt'
        encodings_to_try = ['utf-8', 'latin-1']


        for encoding in encodings_to_try:
            try: 
                with open(path_file, 'r', encoding=encoding) as file:
                    reader = csv.reader(file, delimiter=';')
                    next(reader)

                    for row in reader:
                        try:
                            if len(row) != 5:
                                self.stdout.write(self.style.ERROR(f'Fila inválida: {row}'))
                                continue

                            codigo_producto = row[0].strip()
                            descripcion = row[1].strip()
                            unidad_medida_codigo = row[2].strip()

                            try:
                                peso = float(row[3].strip())
                            except ValueError:
                                self.stdout.write(self.style.ERROR(f'Error al convertir el peso en la fila: {row}'))

                            try:
                                armado = bool(int(row[4].strip()))
                            except ValueError:
                                self.stdout.write(self.style.ERROR(f'Error al convertir el valor de armado en la fila: {row}'))
                                continue

                            unidad_medida, _ = MeasurementUnit.objects.get_or_create(codigo_und_medida=unidad_medida_codigo)

                            codigo_familia = codigo_producto[:2]
                            familia_producto, _ = FamiliaProducto.objects.get_or_create(codigo_familia=codigo_familia)

                            codigo_subfamilia = codigo_producto[:5]
                            subfamilia_producto, _ = SubfamiliaProducto.objects.get_or_create(codigo_subfamilia=codigo_subfamilia, familia_producto=familia_producto)

                            producto, creado = Producto.objects.update_or_create(
                                codigo_producto=codigo_producto,
                                defaults={
                                    'descripcion':descripcion,
                                    'und_medida': unidad_medida,
                                    'peso_unitario': peso,
                                    'armado': armado,
                                    'familia_producto': familia_producto,
                                    'subfamilia_producto': subfamilia_producto
                                }
                            )

                            if creado:
                                self.stdout.write(self.style.SUCCESS(f'Producto {codigo_producto} creado.'))
                            else:
                                self.stdout.write(self.style.SUCCESS(f'Producto {codigo_producto} actualizado.'))
                        
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'Error en la fila {row}: {str(e)}'))
                break
                
            except UnicodeDecodeError:
                continue

        self.stdout.write(self.style.SUCCESS('Productos cargados o actualizados exitosamente.'))
