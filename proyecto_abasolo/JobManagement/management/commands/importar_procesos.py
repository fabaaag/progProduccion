from django.core.management.base import BaseCommand
from JobManagement.models import Proceso, EmpresaOT
import csv

class Command(BaseCommand):
    help = 'Importar datos desde un archivo .txt'

    def handle(self, *args, **kwargs):
        path_file = ['W:\\procesos_ind.txt']
        empresas_id = ['0', '2']
        encodings_to_try = ['utf-8', 'latin-1']

        for index, item in enumerate(path_file):
            for encoding in encodings_to_try:
                try:
                    with open(item, 'r', encoding=encoding) as file:
                        reader = csv.reader(file, delimiter='@')
                        next(reader)
                        next(reader)

                        for row in reader:
                            try:
                                if len(row) != 4:
                                    self.stdout.write(self.style.ERROR(f'Fila inválida; {row}'))
                                    continue

                                codigo_proceso = row[0].strip()
                                sigla = row[1].strip()
                                descripcion = row[2].strip()

                                try:
                                    carga = float(row[3].strip())
                                except ValueError:
                                    self.stdout.write(self.style.ERROR(f'Error al convertir la carga en la fila: {row}'))

                                codigo_empresa = empresas_id[index]
                                empresa, _ = EmpresaOT.objects.get_or_create(codigo_empresa=codigo_empresa)
                                print(empresa.nombre)

                                # Primero verificamos si existe el proceso con el mismo código pero en otra empresa
                                try:
                                    # Primero verificamos si existe el proceso con el mismo código pero en otra empresa
                                    proceso_existente = Proceso.objects.filter(
                                        codigo_proceso=codigo_proceso
                                    ).exclude(empresa=empresa).exists()

                                    if proceso_existente:
                                        # Si existe en otra empresa, creamos uno nuevo agregando un sufijo al código
                                        nuevo_codigo = f"{codigo_proceso}"
                                        proceso = Proceso.objects.create(
                                            codigo_proceso=nuevo_codigo,
                                            empresa=empresa,
                                            sigla=sigla,
                                            descripcion=descripcion.strip(),  # Eliminamos espacios en blanco extras
                                            carga=carga
                                        )
                                        print(f"Proceso {codigo_proceso} ya existe en otra empresa. Creado nuevo proceso con código {nuevo_codigo}")
                                    else:
                                        # Si no existe o existe en la misma empresa, intentamos obtenerlo primero
                                        proceso_actual = Proceso.objects.filter(
                                            codigo_proceso=codigo_proceso,
                                            empresa=empresa
                                        ).first()

                                        if proceso_actual:
                                            # Si existe, actualizamos
                                            proceso_actual.sigla = sigla
                                            proceso_actual.descripcion = descripcion.strip()
                                            proceso_actual.carga = carga
                                            proceso_actual.save()
                                            proceso = proceso_actual
                                            print(f"Proceso {codigo_proceso} actualizado.")
                                        else:
                                            # Si no existe, creamos uno nuevo
                                            proceso = Proceso.objects.create(
                                                codigo_proceso=codigo_proceso,
                                                empresa=empresa,
                                                sigla=sigla,
                                                descripcion=descripcion.strip(),
                                                carga=carga
                                            )
                                            print(f"Proceso {codigo_proceso} creado.")

                                except Exception as e:
                                    print(f"Error en la fila {[codigo_proceso, sigla, descripcion, carga]}: {str(e)}")
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f'Error en la fila {row}: {str(e)}'))
                    break
                
                except UnicodeDecodeError:
                    continue
        self.stdout.write(self.style.SUCCESS('Procesos creados / actualizados correctamente.'))
        