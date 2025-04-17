from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'rut', 'telefono', 'cargo', 'rol', 'activo']
        read_only_fields = ['id', 'username', 'rut']
        
    def update(self, instance, validated_data):
        #Si el RUT no cambió, no lo validamos
        if 'rut' in validated_data:
            validated_data.pop('rut')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta: 
        model = CustomUser
        fields  = ['username', 'password', 'first_name', 'last_name', 'email', 'rut', 'telefono', 'cargo', 'rol', 'activo']
        


    def create(self, validated_data):
        try:
            #Añadimos print para debug
            print("Datos a crear:", validated_data)

            password = validated_data.pop('password')
            user = CustomUser(**validated_data)
            user.set_password(password)
            user.save()
            return user
        
        except Exception as e:
            print("Error en create:", str(e))
            raise serializers.ValidationError(str(e))
        


class UserProfileSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'telefono', 'cargo', 'current_password', 'new_password')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'email': {'required': False},
            'telefono': {'required': False},
            'cargo': {'required': False}
        }

    def validate(self, data):
        # Si se proporciona new_password, current_password es requerido
        if 'new_password' in data and not data.get('current_password'):
            raise serializers.ValidationError(
                {'current_password': 'La contraseña actual es requerida para cambiar la contraseña'}
            )

        # Validar la contraseña actual si se está intentando cambiar la contraseña
        if 'new_password' in data and 'current_password' in data:
            if not self.instance.check_password(data['current_password']):
                raise serializers.ValidationError(
                    {'current_password': 'La contraseña actual es incorrecta'}
                )
            
            # Validar la nueva contraseña
            try:
                validate_password(data['new_password'], self.instance)
            except Exception as e:
                raise serializers.ValidationError({'new_password': list(e)})

        return data

    def update(self, instance, validated_data):
        # Manejar el cambio de contraseña
        if 'new_password' in validated_data:
            instance.set_password(validated_data['new_password'])
            # Eliminar las contraseñas del validated_data para que no se guarden en los campos normales
            validated_data.pop('new_password', None)
            validated_data.pop('current_password', None)

        # Actualizar los demás campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance