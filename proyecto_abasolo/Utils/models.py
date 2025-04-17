from django.db import models

# Create your models here.

class MeasurementUnit(models.Model):
    nombre = models.CharField(max_length=50)
    codigo_und_medida = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.codigo_und_medida or 'Unnamed'
    
class MateriaPrima(models.Model):
    codigo = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=255)
    unidad_medida = models.ForeignKey(MeasurementUnit, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'