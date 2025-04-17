from django.urls import path, include
from rest_framework import routers
from Client import views

router = routers.DefaultRouter()
router.register(r'clientes', views.ClienteView, 'clientes')

urlpatterns = [
    path("api/v1/", include(router.urls)),
]
