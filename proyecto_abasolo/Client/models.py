from django.db import models

# Create your models here.

class Cliente(models.Model):
    codigo_cliente = models.CharField(unique=True, max_length=10, blank=False, null=True)
    nombre = models.CharField(max_length=50, blank=False, null=False)
    vip = models.BooleanField(default=False)
    apodo = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['codigo_cliente']),
            models.Index(fields=['apodo']),
        ]
        unique_together = [('codigo_cliente', 'nombre', 'apodo')]

    def __str__(self):
        return self.nombre