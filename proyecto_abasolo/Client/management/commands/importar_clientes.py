from django.core.management.base import BaseCommand
from Client.models import Cliente
from django.db import transaction, IntegrityError
import chardet

class Command(BaseCommand):
    help = 'Importar datos desde clientes.txt'

    def handle(self, *args, **kwargs):
        path_file = 'W:\\clientes.txt'
        encodings_to_try = ['utf-8', 'latin-1']

        with open(path_file, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            self.stdout.write(self.style.SUCCESS(f'Codificación detectada: {encoding}'))
            encodings_to_try.insert(0, encoding)

        try:
            file_opened = False

            for encoding in encodings_to_try:
                try:
                    with open(path_file, 'r', encoding=encoding) as file:
                        self.stdout.write(self.style.SUCCESS(f'Archivo abierto con codificación: {encoding}'))
                        file_opened = True

                        for line_number, line in enumerate(file, start=1):
                            try:
                                data = line.strip().split(';')

                                if len(data) != 5:
                                    self.stdout.write(self.style.ERROR(f'Formato inválido en la línea {line_number}:{line}'))
                                    continue

                                codigo_cliente = data[1].strip()
                                nombre = data[2].strip()
                                vip = True if data[3] == '1' else False
                                apodo = data[4].strip()

                                with transaction.atomic():
                                    cliente, created = Cliente.objects.update_or_create(
                                        codigo_cliente = codigo_cliente,
                                        defaults={
                                            'nombre':nombre,
                                            'vip':vip,
                                            'apodo':apodo
                                        }
                                    )

                                if created:
                                    self.stdout.write(self.style.SUCCESS(f'Cliente: {nombre} creado con éxito.'))

                                else:
                                    self.stdout.write(self.style.WARNING(f'Cliente: {nombre} ya existe.'))

                            except IntegrityError as e:
                                self.stdout.write(self.style.ERROR(f'Error en la integridad en la linea {line_number}: {e}'))
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f'Error al procesar la línea {line}: {e}'))
                            
                    break
                except UnicodeDecodeError:
                    self.stdout.write(self.style.WARNING(f"Fallo al abrir con codificación {encoding}, intentando otra..."))
                    continue
            
            if not file_opened:
                self.stdout.write(self.style.ERROR(f'No se pudo abrir el archivo {path_file} con ninguna codificación especificada.'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'El archivo {path_file} no fue encontrado.'))
        
        except IOError as e:
            self.stdout.write(self.style.ERROR(f'Error al abrir el archivo: {e}'))
