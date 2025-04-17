from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import UserSerializer, UserCreateSerializer, UserProfileSerializer
from .models import CustomUser
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate


class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.rol == 'ADMIN':
            return Response(
                {'error': 'No tiene permisos para realizar esta acción'},
                status=status.HTTP_403_FORBIDDEN
            )
        users = CustomUser.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

class UserCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.rol == 'ADMIN':
            return Response(
                {'error': 'No tiene permisos para realizar esta acción'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            serializer = UserCreateSerializer(data=request.data)
            if serializer.is_valid():
                #Debug
                print("Datos validados: ", serializer.validated_data)

                user = serializer.save()
                print("Usuario creado: ", user)

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            print("Errores de validación: ", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            print("Error al crear usuario: ", str(e))
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(CustomUser, pk=pk)
    
    def get(self, request, pk):
        user = self.get_object(pk)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        if not request.user.rol == 'ADMIN':
            return Response(
                {'error': 'No tienes permisos para realizar esta acción'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object(pk)

        #Removemos el rut de los datos si existe
        data = request.data.copy()
        if 'rut' in data:
            del data['rut']

        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserToggleStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not request.user.rol == 'ADMIN':
            return Response(
                {'error': 'No tienes permisos para realizar esta acción'},
                status=status.HTTP_403_FORBIDDEN
            )
        user = get_object_or_404(CustomUser, pk=pk)
        user.activo = not user.activo
        user.save()

        return Response({
            'id': user.id,
            'activo': user.activo
        })

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user is not None and user.is_active:
            refresh = RefreshToken.for_user(user)
            return Response({
                'token': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })
        return Response(
            {'error': 'Credenciales inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
#Vista de perfil
class ProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get(self, request):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = self.serializer_class(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            
            # Si se cambió la contraseña, actualizar el token
            if 'new_password' in request.data:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'token': str(refresh.access_token),
                    'refresh': str(refresh),
                    'message': 'Perfil actualizado exitosamente'
                })
            
            return Response({
                'message': 'Perfil actualizado exitosamente',
                **serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

