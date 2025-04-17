from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    #Autenticación y perfil de usuario
    path('api/v1/login/', views.LoginView.as_view(), name='api_login'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/profile/', views.ProfileView.as_view(), name='profile'),
    
    #Gestión de usuarios
    path('api/v1/users/', views.UserListView.as_view(), name='user-list'),
    path('api/v1/users/create/', views.UserCreateView.as_view(), name='user-create'),
    path('api/v1/users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('api/v1/users/<int:pk>/toggle-status/', views.UserToggleStatusView.as_view(), name='user-toggle-status'),
]