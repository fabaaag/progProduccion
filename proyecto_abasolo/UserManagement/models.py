from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.core.validators import RegexValidator

# Create your models here.

class CustomUser(AbstractUser):
    ROLES = [
        ('ADMIN', 'Administrador'),
        ('SUPERVISOR', 'Supervisor'),
        ('OPERADOR', 'Operador'),
    ]

    rut = models.CharField(
        max_length=12,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{1,2}\.\d{3}\.\d{3}[-][0-9kK]{1}$',
                message='Formato de RUT inválido. Debe ser XX.XXX.XXX-X'
            )
        ]
    )

    rol = models.CharField(max_length=20, choices=ROLES, default='OPERADOR')
    telefono = models.CharField(max_length=15, blank=True, null=True)
    cargo = models.CharField(max_length=100, blank=True, null=True)
    activo = models.BooleanField(default=True)
    ultima_conexion = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        related_name='usuarios_creados'
    )
    
    class Meta: 
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.get_full_name()} - ({self.get_rol_display()})"
    
    @property
    def is_admin(self):
        return self.rol == 'ADMIN'
    
    @property 
    def is_supervisor(self):
        return self.rol == 'SUPERVISOR'
    
    @property 
    def is_operador(self):
        return self.rol == 'OPERADOR'

    def save(self, *args, **kwargs):
        #Asignar permisos basados en el rol
        creating = not self.pk
        super().save(*args, **kwargs)

        if creating:
            try: 
                if self.rol == 'ADMIN':
                    group = Group.objects.get_or_create(name='Administradores')[0]
                elif self.rol == 'SUPERVISOR':
                    group = Group.objects.get_or_create(name='Supervisores')[0]
                elif self.rol== 'OPERADOR':
                    group = Group.objects.get_or_create(name='Operadores')[0]

                self.groups.add(group)

            except Exception as e:
                print(f"Error al asignar grupo: {e}")