from django.core.management.base import BaseCommand
from JobManagement.models import ProgramaProduccion, ReporteSupervisor
from django.db import transaction
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Crea reportes de supervisor para programas existentes'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        
        # Buscar un superusuario o el primer usuario disponible
        default_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
        
        if not default_user:
            self.stdout.write(self.style.ERROR("No se encontró ningún usuario en el sistema"))
            return
            
        with transaction.atomic():
            # Obtener programas que no tienen reporte
            programas = ProgramaProduccion.objects.all()
            reportes_existentes = ReporteSupervisor.objects.all().values_list('programa_id', flat=True)
            programas_sin_reporte = programas.exclude(id__in=reportes_existentes)
            
            count = programas_sin_reporte.count()
            self.stdout.write(f"Se encontraron {count} programas sin reportes de supervisor")
            
            creados = 0
            for programa in programas_sin_reporte:
                # Usar el usuario predeterminado si no hay información de creación
                supervisor = None
                
                # Ver si podemos determinar el creador del programa
                if hasattr(programa, 'creado_por') and programa.creado_por:
                    supervisor = programa.creado_por
                elif hasattr(programa, 'modificado_por') and programa.modificado_por:
                    supervisor = programa.modificado_por
                else:
                    supervisor = default_user
                
                ReporteSupervisor.objects.create(
                    programa=programa,
                    supervisor=supervisor,
                    estado='ACTIVO'
                )
                creados += 1
            
            self.stdout.write(self.style.SUCCESS(f"Se crearon {creados} reportes de supervisor"))