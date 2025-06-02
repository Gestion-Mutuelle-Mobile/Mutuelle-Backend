from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters import rest_framework as filters
from django.contrib.auth import authenticate
from .models import Utilisateur
from .serializers import (
    UtilisateurSerializer, UtilisateurCreateSerializer, ChangePasswordSerializer
)
from .permissions import IsAdministrateur, IsOwnerOrAdmin
from django.db import models

class UtilisateurFilter(filters.FilterSet):
    """
    Filtres ultra-complets pour les utilisateurs
    """
    # Filtres texte
    nom_complet = filters.CharFilter(method='filter_nom_complet', lookup_expr='icontains')
    email = filters.CharFilter(lookup_expr='icontains')
    first_name = filters.CharFilter(lookup_expr='icontains')
    last_name = filters.CharFilter(lookup_expr='icontains')
    username = filters.CharFilter(lookup_expr='icontains')
    telephone = filters.CharFilter(lookup_expr='icontains')
    
    # Filtres choix
    role = filters.ChoiceFilter(choices=Utilisateur.ROLE_CHOICES)
    is_active = filters.BooleanFilter()
    
    # Filtres dates
    date_creation = filters.DateFromToRangeFilter()
    date_creation_after = filters.DateFilter(field_name='date_creation', lookup_expr='gte')
    date_creation_before = filters.DateFilter(field_name='date_creation', lookup_expr='lte')
    date_modification = filters.DateFromToRangeFilter()
    
    # Filtres avancés
    has_photo = filters.BooleanFilter(method='filter_has_photo')
    created_this_year = filters.BooleanFilter(method='filter_created_this_year')
    created_this_month = filters.BooleanFilter(method='filter_created_this_month')
    
    class Meta:
        model = Utilisateur
        fields = {
            'email': ['exact', 'icontains', 'istartswith'],
            'role': ['exact'],
            'is_active': ['exact'],
            'date_creation': ['exact', 'gte', 'lte', 'year', 'month'],
            'date_modification': ['exact', 'gte', 'lte'],
        }
    
    def filter_nom_complet(self, queryset, name, value):
        return queryset.filter(
            models.Q(first_name__icontains=value) | 
            models.Q(last_name__icontains=value)
        )
    
    def filter_has_photo(self, queryset, name, value):
        if value:
            return queryset.exclude(photo_profil='')
        return queryset.filter(photo_profil='')
    
    def filter_created_this_year(self, queryset, name, value):
        from django.utils import timezone
        if value:
            current_year = timezone.now().year
            return queryset.filter(date_creation__year=current_year)
        return queryset
    
    def filter_created_this_month(self, queryset, name, value):
        from django.utils import timezone
        if value:
            now = timezone.now()
            return queryset.filter(
                date_creation__year=now.year,
                date_creation__month=now.month
            )
        return queryset

class UtilisateurViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les utilisateurs avec permissions et filtres complets
    """
    queryset = Utilisateur.objects.all()
    serializer_class = UtilisateurSerializer
    filterset_class = UtilisateurFilter
    search_fields = ['email', 'first_name', 'last_name', 'username', 'telephone']
    ordering_fields = ['date_creation', 'date_modification', 'email', 'first_name', 'last_name']
    ordering = ['-date_creation']
    
    def get_permissions(self):
        """
        Permissions selon l'action
        """
        if self.action == 'create':
            # Création libre pour l'inscription
            permission_classes = [AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Modification/suppression pour propriétaire ou admin
            permission_classes = [IsOwnerOrAdmin]
        elif self.action in ['list']:
            # Liste pour admin seulement
            permission_classes = [IsAdministrateur]
        else:
            # Lecture pour authentifiés
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UtilisateurCreateSerializer
        return UtilisateurSerializer
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Retourne les infos de l'utilisateur connecté
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """
        Met à jour le profil de l'utilisateur connecté
        """
        serializer = self.get_serializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class ProfileView(APIView):
    """
    Vue pour le profil utilisateur
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UtilisateurSerializer(request.user, context={'request': request})
        return Response(serializer.data)

class ChangePasswordView(APIView):
    """
    Vue pour changer le mot de passe
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Mot de passe modifié avec succès'})