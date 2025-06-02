from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Utilisateur

@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    """
    Administration personnalisée pour le modèle Utilisateur
    """
    list_display = (
        'email', 'nom_complet_formate', 'username', 'role_formate', 
        'telephone', 'is_active', 'date_creation'
    )
    list_filter = ('role', 'is_active', 'is_staff', 'date_creation')
    search_fields = ('email', 'first_name', 'last_name', 'username', 'telephone')
    ordering = ('-date_creation',)
    
    # Champs en lecture seule
    readonly_fields = ('date_creation', 'date_modification', 'last_login', 'date_joined')
    
    # Configuration des fieldsets pour la vue de détail
    fieldsets = (
        ('Informations de connexion', {
            'fields': ('username', 'email', 'password')
        }),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'telephone', 'photo_profil')
        }),
        ('Permissions et rôle', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    # Configuration pour l'ajout d'un nouvel utilisateur
    add_fieldsets = (
        ('Informations de base', {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        }),
        ('Informations supplémentaires', {
            'fields': ('telephone', 'role', 'photo_profil', 'is_active')
        }),
    )
    
    # Actions personnalisées
    actions = ['marquer_actif', 'marquer_inactif', 'promouvoir_admin', 'retrograder_membre']
    
    def nom_complet_formate(self, obj):
        """Affiche le nom complet avec formatage"""
        return obj.nom_complet
    nom_complet_formate.short_description = 'Nom complet'
    
    def role_formate(self, obj):
        """Affiche le rôle avec couleur"""
        colors = {
            'ADMINISTRATEUR': 'red',
            'MEMBRE': 'blue'
        }
        color = colors.get(obj.role, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_role_display()
        )
    role_formate.short_description = 'Rôle'
    
    def marquer_actif(self, request, queryset):
        """Action pour marquer les utilisateurs comme actifs"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} utilisateur(s) marqué(s) comme actif(s).')
    marquer_actif.short_description = "Marquer comme actif"
    
    def marquer_inactif(self, request, queryset):
        """Action pour marquer les utilisateurs comme inactifs"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} utilisateur(s) marqué(s) comme inactif(s).')
    marquer_inactif.short_description = "Marquer comme inactif"
    
    def promouvoir_admin(self, request, queryset):
        """Action pour promouvoir des membres en administrateurs"""
        updated = queryset.filter(role='MEMBRE').update(role='ADMINISTRATEUR', is_staff=True)
        self.message_user(request, f'{updated} membre(s) promu(s) administrateur(s).')
    promouvoir_admin.short_description = "Promouvoir en administrateur"
    
    def retrograder_membre(self, request, queryset):
        """Action pour rétrograder des administrateurs en membres"""
        # Ne pas rétrograder les superusers
        updated = queryset.filter(role='ADMINISTRATEUR', is_superuser=False).update(
            role='MEMBRE', is_staff=False
        )
        self.message_user(request, f'{updated} administrateur(s) rétrogradé(s) en membre(s).')
    retrograder_membre.short_description = "Rétrograder en membre"
    
    def get_queryset(self, request):
        """Optimiser les requêtes"""
        return super().get_queryset(request).select_related()
    
    def has_delete_permission(self, request, obj=None):
        """Empêcher la suppression des superusers"""
        if obj and obj.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

# Configuration de l'admin site
admin.site.site_header = "Administration Mutuelle Enseignants ENSPY"
admin.site.site_title = "Mutuelle ENSPY Admin"
admin.site.index_title = "Tableau de bord administrateur"

# Personnalisation supplémentaire
admin.site.empty_value_display = '(Aucune valeur)'