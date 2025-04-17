from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from Product.models import MeasurementUnit, MateriaPrima, TipoProducto, Producto, Pieza, FichaTecnica, TerminacionFicha, FamiliaProducto, SubfamiliaProducto
from django.core.exceptions import ObjectDoesNotExist
import csv, re

def get_object_or_none(klass, *args, **kwargs):
    try:
        return klass.objects.get(*args, **kwargs)
    except ObjectDoesNotExist:
        return None
    
class Command(BaseCommand):
    help = 'Importar fichas técnicas desde un archivo .txt'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Actualizar fichas existentes')
        parser.add_argument('--file', type=str, default='W:\\ficha.txt', help='Ruta del archivo a importar')

    def handle(self, *args, **kwargs):
        path_file = kwargs.get('file', 'W:\\ficha.txt')
        force_update = kwargs.get('force', False)
        encodings_to_try = ['utf-8', 'latin-1']

        # Contadores para estadísticas
        total_filas = 0
        productos_actualizados = 0
        piezas_actualizadas = 0
        productos_no_encontrados = 0
        errores_conversion = 0
        fichas_existentes = 0
        errores_integridad = 0
        errores_otros = 0

        for encoding in encodings_to_try:
            try:
                with open(path_file, 'r', newline='', encoding=encoding) as file:
                    reader = csv.reader(file, delimiter='@')
                    # Saltamos las dos primeras líneas (encabezados)
                    next(reader)
                    next(reader)

                    for row in reader:
                        total_filas += 1
                        try:
                            if len(row) < 14:
                                self.stdout.write(self.style.WARNING(f'Fila {total_filas}: Número insuficiente de campos ({len(row)}), se esperaban al menos 14'))
                                continue

                            codigo_producto = row[0].strip()
                            
                            # Buscar producto o pieza
                            producto = get_object_or_none(Producto, codigo_producto=codigo_producto)
                            pieza = get_object_or_none(Pieza, codigo_pieza=codigo_producto)

                            if not producto and not pieza:
                                self.stdout.write(self.style.WARNING(f'Fila {total_filas}: Producto/pieza no encontrados para código: {codigo_producto}'))
                                productos_no_encontrados += 1
                                continue

                            # Si ya existe una ficha y no estamos forzando la actualización, saltamos
                            if producto and producto.ficha_tecnica is not None and not force_update:
                                self.stdout.write(self.style.SUCCESS(f'Fila {total_filas}: Ficha técnica ya existe para el producto: {codigo_producto}'))
                                fichas_existentes += 1
                                continue

                            if pieza and pieza.ficha_tecnica is not None and not force_update:
                                self.stdout.write(self.style.SUCCESS(f'Fila {total_filas}: Ficha técnica ya existe para la pieza: {codigo_producto}'))
                                fichas_existentes += 1
                                continue

                            # Si necesitamos actualizar una ficha existente
                            if force_update:
                                if producto and producto.ficha_tecnica:
                                    ficha_tecnica = producto.ficha_tecnica
                                elif pieza and pieza.ficha_tecnica:
                                    ficha_tecnica = pieza.ficha_tecnica
                                else:
                                    ficha_tecnica = FichaTecnica()
                            else:
                                ficha_tecnica = FichaTecnica()

                            # Procesamiento de datos
                            codigo_tipo_producto = row[1].strip()
                            tipo_producto, created = TipoProducto.objects.get_or_create(
                                codigo=codigo_tipo_producto,
                                defaults={'nombre': codigo_tipo_producto}
                            )

                            texto_largo_hilo = re.sub(r'\s+', ' ', row[2].strip())

                            try:
                                largo_hilo = float(row[3].strip().replace(',', '.'))
                            except ValueError as e:
                                self.stdout.write(self.style.ERROR(f'Fila {total_filas}: Error al convertir largo hilo: {row[3]} - {str(e)}'))
                                errores_conversion += 1
                                continue

                            try:
                                hilos_por_pulgada = int(row[4].strip())
                            except ValueError as e:
                                self.stdout.write(self.style.ERROR(f'Fila {total_filas}: Error al convertir hilos por pulgada: {row[4]} - {str(e)}'))
                                errores_conversion += 1
                                continue

                            try:
                                peso_producto = float(row[5].strip().replace(',', '.'))
                            except ValueError as e:
                                self.stdout.write(self.style.ERROR(f'Fila {total_filas}: Error al convertir peso producto: {row[5]} - {str(e)}'))
                                errores_conversion += 1
                                continue

                            plano_ficha_path = row[6].strip()
                            calibra_ficha = re.sub(r'\s+', ' ', row[7].strip())
                            observacion_ficha = re.sub(r'\s+', ' ', row[8].strip())
                            term_ficha = row[9].strip()

                            codigo_materia_prima = row[10].strip()
                            if codigo_materia_prima:
                                materia_prima, created = MateriaPrima.objects.get_or_create(
                                    codigo=codigo_materia_prima,
                                    defaults={'descripcion': codigo_materia_prima}
                                )
                            else:
                                materia_prima = None

                            try:
                                largo_cortar = float(row[11].strip().replace(',', '.'))
                            except ValueError as e:
                                self.stdout.write(self.style.ERROR(f'Fila {total_filas}: Error al convertir largo cortar: {row[11]} - {str(e)}'))
                                errores_conversion += 1
                                continue

                            observacion_mprima = re.sub(r'\s+', ' ', row[12].strip())
                            
                            try:
                                estandar_ficha = int(row[13].strip() if row[13].strip() else '0')
                            except ValueError as e:
                                self.stdout.write(self.style.ERROR(f'Fila {total_filas}: Error al convertir estandar ficha: {row[13]} - {str(e)}'))
                                estandar_ficha = 0

                            terminacion_ficha = None
                            if term_ficha:
                                terminacion_ficha, created = TerminacionFicha.objects.get_or_create(
                                    codigo=term_ficha,
                                    defaults={'nombre': term_ficha}
                                )

                            # Asignar valores a la ficha técnica
                            ficha_tecnica.tipo_producto = tipo_producto
                            ficha_tecnica.texto_largo_hilo = texto_largo_hilo
                            ficha_tecnica.largo_hilo = largo_hilo
                            ficha_tecnica.hilos_por_pulgada = hilos_por_pulgada
                            ficha_tecnica.peso_producto = peso_producto
                            ficha_tecnica.plano_ficha_path = plano_ficha_path
                            ficha_tecnica.calibra_ficha = calibra_ficha
                            ficha_tecnica.observacion_ficha = observacion_ficha
                            ficha_tecnica.terminacion_ficha = terminacion_ficha
                            ficha_tecnica.materia_prima = materia_prima
                            ficha_tecnica.largo_cortar = largo_cortar
                            ficha_tecnica.observacion_mprima = observacion_mprima
                            ficha_tecnica.estandar_ficha = str(estandar_ficha)

                            # Guardar todo en una transacción para evitar datos parciales
                            with transaction.atomic():
                                ficha_tecnica.save()

                                if producto:
                                    producto.ficha_tecnica = ficha_tecnica
                                    producto.save()
                                    self.stdout.write(self.style.SUCCESS(f'Fila {total_filas}: Ficha asignada a producto: {producto.codigo_producto}'))
                                    productos_actualizados += 1
                                elif pieza:
                                    pieza.ficha_tecnica = ficha_tecnica
                                    pieza.save()
                                    self.stdout.write(self.style.SUCCESS(f'Fila {total_filas}: Ficha asignada a Pieza: {pieza.codigo_pieza}'))
                                    piezas_actualizadas += 1

                        except IntegrityError as e:
                            self.stdout.write(self.style.ERROR(f'Fila {total_filas}: Error de integridad en la base de datos: {str(e)}'))
                            errores_integridad += 1
                            continue

                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'Fila {total_filas}: Error inesperado: {str(e)}'))
                            errores_otros += 1
                            continue

                # Imprimir estadísticas finales
                self.stdout.write(self.style.SUCCESS(f'\nImportación finalizada. Estadísticas:'))
                self.stdout.write(f'Total de filas procesadas: {total_filas}')
                self.stdout.write(f'Productos actualizados: {productos_actualizados}')
                self.stdout.write(f'Piezas actualizadas: {piezas_actualizadas}')
                self.stdout.write(f'Fichas ya existentes: {fichas_existentes}')
                self.stdout.write(f'Productos/piezas no encontrados: {productos_no_encontrados}')
                self.stdout.write(f'Errores de conversión: {errores_conversion}')
                self.stdout.write(f'Errores de integridad: {errores_integridad}')
                self.stdout.write(f'Otros errores: {errores_otros}')
                
                break  # Salir del bucle de encodings si el archivo se procesó correctamente
            except UnicodeDecodeError:
                continue  # Probar con el siguiente encoding
            except FileNotFoundError:
                self.stdout.write(self.style.ERROR(f'El archivo {path_file} no fue encontrado.'))
                break