from django.core.management import BaseCommand
from JobManagement.models import Proceso, Maquina 
from Machine.models import TipoMaquina, EstadoMaquina
import PyPDF2
import re
from django.db.models import Q

class Command(BaseCommand):
    help = 'Actualiza las relaciones entre proceso-maquina basado en el PDF'

    def find_machine(self, machine_code, machine_description):
        """
        Busca una máquina por código o descripción similar
        """
        # Primero intentar por código exacto
        machine = Maquina.objects.filter(codigo_maquina=machine_code).first()
        if machine:
            return machine, 'código'

        # Si no se encuentra, buscar por descripción similar
        clean_description = machine_description.strip().upper()
        
        machines = Maquina.objects.filter(
            Q(descripcion__icontains=clean_description) |
            Q(sigla__icontains=clean_description)
        )

        if machines.exists():
            if machines.count() > 1:
                self.stdout.write(
                    self.style.WARNING(
                        f'Múltiples coincidencias para "{clean_description}": '
                        f'{", ".join([f"{m.codigo_maquina}: {m.descripcion}" for m in machines])}'
                    )
                )
                return None, 'múltiples coincidencias'
            return machines.first(), 'descripción'

        return None, 'no encontrada'

    def extract_relations_from_pdf(self, pdf_path):
        relations = {}
        current_process = None
        process_siglas = {}  # Nuevo: Almacenar las siglas de los procesos

        try: 
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)

                for page in reader.pages:
                    text = page.extract_text()
                    lines = text.split('\n')

                    for line in lines:
                        if not line.strip() or 'Cod. Sigla' in line or 'INFORME' in line:
                            continue

                        # Buscar proceso y su sigla
                        process_match = re.match(r'(\d{4})\s+(\w+)\s+(.+?)\s{2,}', line)
                        if process_match:
                            process_code = process_match.group(1)
                            process_sigla = process_match.group(2)  # Capturar la sigla
                            current_process = process_code
                            relations[current_process] = []
                            process_siglas[current_process] = process_sigla

                        # Buscar máquina
                        machine_match = re.search(r'(\d{4})\s+(\w+)\s+(.+?)$', line)
                        if machine_match and current_process:
                            machine_code = machine_match.group(1)
                            relations[current_process].append(machine_code)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al leer el PDF: {str(e)}'))
        
        return relations, process_siglas

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando actualización de relaciones proceso-máquina...')
        
        pdf_path = 'C:/Users/desar/Desktop/proyecto/Relacion_proceso-maquina.pdf'
        relations, process_siglas = self.extract_relations_from_pdf(pdf_path)
        
        stats = {
            'código': 0,
            'descripción': 0,
            'no encontrada': 0,
            'múltiples coincidencias': 0
        }
        
        machine_mapping = {}
        
        for proceso_code, maquinas_codes in relations.items():
            try:
                proceso = Proceso.objects.get(codigo_proceso=proceso_code)
                proceso_sigla = process_siglas[proceso_code]
                self.stdout.write(f'\nActualizando proceso {proceso_code} - {proceso.descripcion}')
                
                # Obtener o crear el tipo de máquina correspondiente a la sigla del proceso
                tipo_maquina, created = TipoMaquina.objects.get_or_create(
                    codigo=proceso_sigla,
                    defaults={'descripcion': f'Máquinas para {proceso.descripcion}'}
                )
                
                # Asignar el tipo de máquina al proceso
                proceso.tipos_maquina_compatibles.set([tipo_maquina])
                
                # Actualizar las máquinas asociadas
                for maquina_code in maquinas_codes:
                    if maquina_code in machine_mapping:
                        maquina = machine_mapping[maquina_code]
                    else:
                        maquina, found_by = self.find_machine(maquina_code, maquina_code)
                        stats[found_by] += 1
                        machine_mapping[maquina_code] = maquina
                    
                    if maquina and hasattr(maquina, 'estado'):
                        # Asignar el tipo de máquina a la máquina
                        maquina.estado.tipos_maquina.add(tipo_maquina)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f' - Máquina actualizada: {maquina.codigo_maquina} - '
                                f'Tipo: {tipo_maquina.codigo}'
                            )
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f' -> Proceso {proceso_code} actualizado con tipo de máquina: {tipo_maquina.codigo}'
                    )
                )
                
            except Proceso.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Proceso {proceso_code} no encontrado')
                )

        # Mostrar estadísticas finales
        self.stdout.write('\nEstadísticas de búsqueda de máquinas:')
        for method, count in stats.items():
            self.stdout.write(f'- Encontradas por {method}: {count}')