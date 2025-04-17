from django.db import migrations

def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')

    #Crear grupos si no existen
    groups = ['ADMIN', 'SUPERVISOR', 'OPERADOR']
    for group_name in groups:
        Group.objects.get_or_create(name=group_name)

class Migration(migrations.Migration):
    dependencies = [
        ('UserManagement', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups),
    ]