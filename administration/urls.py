from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'dashboard', views.AdministrationDashboardViewSet, basename='admin-dashboard')
router.register(r'gestion-membres', views.GestionMembresViewSet, basename='gestion-membres')
router.register(r'rapports', views.RapportsViewSet, basename='rapports')

urlpatterns = [
    path('', include(router.urls)),
]