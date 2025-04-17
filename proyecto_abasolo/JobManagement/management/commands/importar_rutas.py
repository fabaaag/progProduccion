from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

from JobManagement.models import Ruta, Proceso, Maquina, RutaPieza
from Product.models import Producto, Pieza

import csv

def get_object_or_none(klass, *args, **kwargs):
    try:
        return klass.objects.get(*args, **kwargs)
    except ObjectDoesNotExist:
        return None
    
class Command(BaseCommand):
    help = 'Imortar datos desde un archivo .txt'

    def handle(self, *args, **kwargs):
        path_file = 'W:\\ruta.txt'
        encodings_to_try = ['utf-8', 'latin-1']

        for encoding in encodings_to_try:
            try:
                with open(path_file, 'r', encoding=encoding) as file:
                    reader =  csv.reader(file, delimiter=';')
                    next(reader)
                    next(reader)

                    for row in reader:
                        try:
                            if len(row) != 5:
                                self.stdout.write(self.style.ERROR(f'Fila inválida: {row}'))
                                continue

                            codigo_producto = row[0]
                            producto = get_object_or_none(Producto, codigo_producto=codigo_producto)
                            pieza = get_object_or_none(Pieza, codigo_pieza=codigo_producto)

                            if not producto and not pieza:
                                print(f'Producto o pieza no encontrados para {row}')
                                continue

                            nro_etapa = int(row[1].strip())
                            
                            codigo_proceso = row[2].strip()
                            proceso, _ =Proceso.objects.get_or_create(codigo_proceso=codigo_proceso)
                            
                            codigo_maquina = row[3].strip()
                            maquina, _ = Maquina.objects.get_or_create(codigo_maquina=codigo_maquina)

                            if row[4].strip() != '':
                                estandar = int(row[4].strip())
                            else:
                                estandar = 0

                            if producto:
                                ruta, creado = Ruta.objects.update_or_create(
                                    producto = producto,
                                    nro_etapa = nro_etapa,
                                    proceso = proceso,
                                    maquina = maquina,
                                    estandar = estandar
                                )
                                if creado:
                                    self.stdout.write(self.style.SUCCESS(f'Ruta creada para el producto: {codigo_producto}'))
                                else:
                                    self.stdout.write(self.style.WARNING(f'Ruta actualizada para el producto: {codigo_producto}'))

                            elif pieza:
                                ruta, creado = RutaPieza.objects.update_or_create(
                                    pieza = pieza,
                                    nro_etapa = nro_etapa,
                                    proceso = proceso,
                                    maquina = maquina,
                                    estandar = estandar
                                )
                                if creado:
                                    self.stdout.write(self.style.SUCCESS(f'Ruta creada para la pieza: {codigo_producto}'))
                                else:
                                    self.stdout.write(self.style.WARNING(f'Ruta actualizada para la pieza: {codigo_producto}'))
                            
                            else:
                                self.stdout.write(self.style.ERROR(f'No se encontró producto ni pieza para el código: {codigo_producto}'))
                                continue
                        except(ValueError, IntegrityError) as e:
                            self.stdout.write(self.style.ERROR(f'Error al procesar la fila: {row}: {str(e)}'))
                            self.stdout.write(self.style.ERROR)
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'Error inesperado al procesar la fila {row}: {str(e)}'))
                break
            except UnicodeDecodeError:
                continue
        self.stdout.write(self.style.SUCCESS(f'Rutas cargadas / actualizadas correctamente.'))