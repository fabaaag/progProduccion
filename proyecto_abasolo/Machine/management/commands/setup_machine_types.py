from django.core.management.base import BaseCommand
from JobManagement.models import Proceso, Maquina
from Machine.models import TipoMaquina, EstadoMaquina, EstadoOperatividad
import PyPDF2
import re
from collections import defaultdict

class Command(BaseCommand):
    help = 'Configura los tipos de máquinas basados en las siglas de los procesos'

    def extract_process_machines(self, pdf_path):
        process_info = {}
        current_process = None
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                for page in reader.pages:
                    text = page.extract_text()
                    lines = text.split('\n')
                    
                    for line in lines:
                        if not line.strip() or 'Cod. Sigla' in line or 'INFORME' in line:
                            continue
                            
                        # Buscar proceso
                        process_match = re.match(r'(\d{4})\s+(\w+)\s+(.+?)\s{2,}', line)
                        if process_match:
                            process_code = process_match.group(1)
                            process_sigla = process_match.group(2)
                            process_desc = process_match.group(3).strip()
                            current_process = process_code
                            process_info[current_process] = {
                                'sigla': process_sigla,
                                'description': process_desc,
                                'machines': []
                            }
                            
                        # Buscar máquina
                        machine_match = re.search(r'(\d{4})\s+(\w+)\s+(.+?)$', line)
                        if machine_match and current_process:
                            machine_code = machine_match.group(1).zfill(4)
                            process_info[current_process]['machines'].append(machine_code)
                            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al leer el PDF: {str(e)}'))
            
        return process_info

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando configuración de tipos de máquinas...')
        
        # Crear estado operativo por defecto
        estado_operativo, _ = EstadoOperatividad.objects.get_or_create(
            estado='OP',
            defaults={'descripcion': 'Operativa'}
        )
        
        pdf_path = 'C:/Users/desar/Desktop/proyecto/Relacion_proceso-maquina.pdf'
        process_info = self.extract_process_machines(pdf_path)
        
        # Debug: Mostrar todas las máquinas en la base de datos
        self.stdout.write('\nMáquinas en la base de datos:')
        for maquina in Maquina.objects.all():
            self.stdout.write(f'- {maquina.codigo_maquina}: {maquina.descripcion}')
        
        # Crear tipos de máquina basados en las siglas de los procesos
        machine_types = {}
        machine_type_relations = defaultdict(set)
        
        for proc_code, info in process_info.items():
            sigla = info['sigla']
            tipo_maquina, created = TipoMaquina.objects.get_or_create(
                codigo=sigla,
                defaults={
                    'descripcion': f'Máquinas para {info["description"]}'
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Creado nuevo tipo de máquina: {sigla}'))
            
            machine_types[sigla] = tipo_maquina
            
            for machine_code in info['machines']:
                machine_type_relations[machine_code].add(tipo_maquina)
        
        # Actualizar las máquinas
        for machine_code, tipos in machine_type_relations.items():
            try:
                self.stdout.write(f'\nBuscando máquina con código: {machine_code}')
                
                maquina = Maquina.objects.get(codigo_maquina=machine_code)
                
                estado_maquina, _ = EstadoMaquina.objects.get_or_create(
                    maquina=maquina,
                    defaults={
                        'estado_operatividad': estado_operativo,
                        'disponible': True
                    }
                )
                
                # Asignar tipos a la máquina
                estado_maquina.tipos_maquina.set(tipos)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Máquina {machine_code} ({maquina.sigla}) actualizada con '
                        f'{len(tipos)} tipos: {", ".join(t.codigo for t in tipos)}'
                    )
                )
                
            except Maquina.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Máquina {machine_code} no encontrada en la base de datos')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error procesando máquina {machine_code}: {str(e)}')
                )
        
        self.stdout.write(self.style.SUCCESS('Configuración de tipos completada'))