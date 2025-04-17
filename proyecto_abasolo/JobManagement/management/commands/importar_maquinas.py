from django.core.management.base import BaseCommand
from JobManagement.models import Maquina, EmpresaOT
import csv

class Command(BaseCommand):
    help = 'Importar datos desde un archivo .txt'
    
    def handle(self, *args, **kwargs):
        path_file = ['W:\\maquina_indaval.txt']
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
                                if len(row) != 6:
                                    self.stdout.write(self.style.ERROR(f'Fila inválida: {row}'))
                                    continue
                                
                                codigo_maquina = row[0].strip()
                                sigla = row[1].strip()
                                descripcion = row[2].strip()
                                
                                try:
                                    carga = float(row[4].strip())
                                except ValueError:
                                    self.stdout.write(self.style.ERROR(f'Error al convertir la carga en la fila: {row}'))

                                golpes = int(row[5].strip())

                                
                                codigo_empresa = empresas_id[index]
                                empresa, _ = EmpresaOT.objects.get_or_create(codigo_empresa=codigo_empresa)
                                print(empresa.nombre)

                                maquina, creado = Maquina.objects.update_or_create(
                                    codigo_maquina=codigo_maquina,
                                    defaults={
                                        'sigla': sigla,
                                        'descripcion': descripcion,
                                        'carga': carga,
                                        'golpes': golpes,
                                        'empresa': empresa,
                                    }
                                )

                                if creado:
                                    self.stdout.write(self.style.SUCCESS(f'Maquina {codigo_maquina} creada.'))
                                else:
                                    self.stdout.write(self.style.SUCCESS(f'Maquina {codigo_maquina} actualizada.'))
                            
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f'Error en la fila {row}: {str(e)}'))
                    break
                except UnicodeDecodeError:
                    continue
        self.stdout.write(self.style.SUCCESS('Maquinas cargadas / actualizadas correctamente.'))

        