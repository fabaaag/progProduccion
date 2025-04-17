from rest_framework import viewsets
from .serializers import ClienteSerializer
from .models import Cliente

# Create your views here.
class ClienteView(viewsets.ModelViewSet):
    serializer_class = ClienteSerializer
    queryset = Cliente.objects.all()