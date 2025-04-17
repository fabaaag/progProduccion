from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(TipoMaquina)
admin.site.register(EstadoOperatividad)
admin.site.register(EstadoMaquina)
admin.site.register(HistorialEstadoMaquina)
admin.site.register(MantenimientoMaquina)