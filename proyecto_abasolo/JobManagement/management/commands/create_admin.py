from django.core.management.base import BaseCommand
from UserManagement.models import CustomUser
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Crea un usuario administrador'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('password', type=str)
        parser.add_argument('rut', type=str)

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        email = kwargs['email']
        password = kwargs['password']
        rut = kwargs['rut']

        try:
            # Verificar si el usuario ya existe
            if CustomUser.objects.filter(username=username).exists():
                self.stdout.write(self.style.ERROR(f'El usuario {username} ya existe'))
                return

            # Crear el usuario administrador
            admin = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                rut=rut,
                rol='ADMIN',
                is_staff=True,
                is_superuser=True
            )

            # Asegurarse de que existe el grupo Administradores
            admin_group, _ = Group.objects.get_or_create(name='Administradores')
            admin.groups.add(admin_group)

            self.stdout.write(
                self.style.SUCCESS(f'Usuario administrador {username} creado exitosamente')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al crear el administrador: {str(e)}')
            )
