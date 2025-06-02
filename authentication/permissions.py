from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework import permissions

class IsAdministrateur(BasePermission):
    """
    Permission pour les administrateurs uniquement
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'ADMINISTRATEUR'
        )

class IsMembreOrAdmin(BasePermission):
    """
    Permission pour les membres ou administrateurs
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['MEMBRE', 'ADMINISTRATEUR']
        )

class IsOwnerOrAdmin(BasePermission):
    """
    Permission pour le propriétaire de l'objet ou un administrateur
    """
    def has_object_permission(self, request, view, obj):
        # Admin peut tout faire
        if request.user.role == 'ADMINISTRATEUR':
            return True
        
        # Pour les objets liés à un membre
        if hasattr(obj, 'membre'):
            return obj.membre.utilisateur == request.user
        
        # Pour les objets utilisateur
        if hasattr(obj, 'utilisateur'):
            return obj.utilisateur == request.user
        
        # Pour les utilisateurs directement
        if hasattr(obj, 'email'):  # C'est un utilisateur
            return obj == request.user
        
        return False

class IsAdminOrReadOnly(BasePermission):
    """
    Permission lecture pour tous, écriture pour admin seulement
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'ADMINISTRATEUR'
        )