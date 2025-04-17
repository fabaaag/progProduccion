from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from Product.models import Producto, Pieza
import csv
import chardet
import os

class Command(BaseCommand):
    help = 'Importa pesos de productos y piezas desde archivo txt con ruta fija'

    def handle(self, *args, **kwargs):
        path_file = 'W:\\pesos.txt' 
        updated_productos = 0
        updated_piezas = 0
        not_found_count = 0
        errors = []

        # Verificar si el archivo existe
        if not os.path.exists(path_file):
            self.stdout.write(
                self.style.ERROR(f'El archivo no existe en la ruta: {path_file}')
            )
            return

        # Detectar la codificación del archivo
        try:
            with open(path_file, 'rb') as f:
                result = chardet.detect(f.read())
                encoding = result['encoding']

            self.stdout.write(f'Usando codificación: {encoding}')

            with open(path_file, 'r', encoding=encoding) as file:
                reader = csv.reader(file, delimiter=';')
                next(reader)  # Ignorar la primera fila

                for row_number, row in enumerate(reader, start=2):  # start=2 porque ignoramos la primera fila
                    try:
                        # Verificar que la fila tenga suficientes columnas
                        if len(row) < 4:
                            error_msg = f'Fila {row_number}: Formato inválido - faltan columnas'
                            errors.append(error_msg)
                            self.stdout.write(self.style.WARNING(error_msg))
                            continue

                        # Ignorar el primer elemento (0) y el último(@)
                        codigo = row[1].strip()
                        if not codigo:
                            error_msg = f'Fila {row_number}: Código vacío'
                            errors.append(error_msg)
                            self.stdout.write(self.style.WARNING(error_msg))
                            continue

                        # Convertir el peso a float, limpiando espacios
                        try:
                            peso_str = row[2].strip()
                            peso = float(peso_str)
                            if peso <= 0:
                                error_msg = f'Fila {row_number}: Peso debe ser mayor que 0'
                                errors.append(error_msg)
                                self.stdout.write(self.style.WARNING(error_msg))
                                continue
                        except (ValueError, TypeError):
                            error_msg = f'Fila {row_number}: Peso inválido para código {codigo}: {row[2]}'
                            errors.append(error_msg)
                            self.stdout.write(self.style.WARNING(error_msg))
                            continue

                        descripcion = row[3].strip()

                        # Buscar primero en Productos
                        productos = Producto.objects.filter(codigo_producto=codigo)
                        # Buscar también en Piezas
                        piezas = Pieza.objects.filter(codigo_pieza=codigo)

                        updated = False

                        # Actualizar Productos si se encuentran
                        if productos.exists():
                            try:
                                with transaction.atomic():
                                    for producto in productos:
                                        producto.peso_unitario = peso
                                        producto.save(update_fields=['peso_unitario'])
                                updated_productos += 1
                                updated = True
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'Fila {row_number}: Actualizado peso para producto {codigo}: {peso}'
                                    )
                                )
                            except Exception as e:
                                error_msg = f'Fila {row_number}: Error al actualizar producto {codigo}: {str(e)}'
                                errors.append(error_msg)
                                self.stdout.write(self.style.ERROR(error_msg))

                        # Actualizar Piezas si se encuentran
                        if piezas.exists():
                            try:
                                with transaction.atomic():
                                    for pieza in piezas:
                                        pieza.peso_unitario = peso
                                        pieza.save(update_fields=['peso_unitario'])
                                updated_piezas += 1
                                updated = True
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'Fila {row_number}: Actualizado peso para pieza {codigo}: {peso}'
                                    )
                                )
                            except Exception as e:
                                error_msg = f'Fila {row_number}: Error al actualizar pieza {codigo}: {str(e)}'
                                errors.append(error_msg)
                                self.stdout.write(self.style.ERROR(error_msg))

                        if not updated:
                            not_found_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Fila {row_number}: No se encontró producto/pieza para el código: {codigo}'
                                )
                            )

                    except Exception as e:
                        error_msg = f'Fila {row_number}: Error procesando fila: {str(e)}'
                        errors.append(error_msg)
                        self.stdout.write(self.style.ERROR(error_msg))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error leyendo archivo: {str(e)}')
            )
            return

        # Resumen final
        self.stdout.write(
            self.style.SUCCESS(
                f'\nResumen de importación:'
                f'\n- Productos actualizados: {updated_productos}'
                f'\n- Piezas actualizadas: {updated_piezas}'
                f'\n- Códigos no encontrados: {not_found_count}'
                f'\n- Errores: {len(errors)}'
            )
        )

        if errors:
            self.stdout.write('\nDetalles de errores:')
            for error in errors:
                self.stdout.write(self.style.WARNING(f'- {error}'))
