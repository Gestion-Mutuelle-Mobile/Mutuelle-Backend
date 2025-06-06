from rest_framework import serializers
from decimal import Decimal

from authentication.models import Utilisateur

class DashboardAdministrateurSerializer(serializers.Serializer):
    """
    Serializer pour le dashboard administrateur complet
    """
    fonds_social = serializers.DictField()
    tresor = serializers.DictField()
    emprunts_en_cours = serializers.DictField()
    situation_globale = serializers.DictField()
    derniers_paiements = serializers.DictField()
    alertes = serializers.ListField()
    activite_recente = serializers.DictField()
    membres_problematiques = serializers.ListField()
    renflouements=serializers.DictField()

class GestionMembreSerializer(serializers.Serializer):
    """
    Serializer pour la gestion des membres
    """
    membre_id = serializers.UUIDField()
    action = serializers.CharField()
    details = serializers.DictField()

class GestionTransactionSerializer(serializers.Serializer):
    """
    Serializer pour la gestion des transactions par l'admin
    """
    membre_id = serializers.UUIDField(required=False)
    emprunt = serializers.UUIDField(required=False)
    session_id = serializers.UUIDField(required=False)
    montant = serializers.DecimalField(max_digits=12, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True)

class RapportFinancierSerializer(serializers.Serializer):
    """
    Serializer pour les rapports financiers
    """
    periode = serializers.DictField()
    entrees = serializers.DictField()
    sorties = serializers.DictField()
    bilan = serializers.DictField()
    indicateurs = serializers.DictField()

class StatistiquesGlobalesSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques globales
    """
    membres = serializers.DictField()
    transactions = serializers.DictField()
    performance = serializers.DictField()
    
    
# Ajouter ce serializer

class CreerMembreCompletSerializer(serializers.Serializer):
    """
    Serializer pour créer un membre complet (utilisateur + membre)
    """
    # Données utilisateur
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=50)
    telephone = serializers.CharField(max_length=15)
    password = serializers.CharField(required=False, default='0000')
    photo_profil = serializers.ImageField(required=False)
    
    # Données membre
    date_inscription = serializers.DateField(required=False)
    montant_inscription_initial = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, min_value=Decimal('0')  # ✅ CORRIGÉ
    )
    
    def validate_email(self, value):
        if Utilisateur.objects.filter(email=value).exists():
            print("Un utilisateur avec cet email existe déjà")
            raise serializers.ValidationError("Un utilisateur avec cet email existe déjà")
            
        return value
    
    def validate_username(self, value):
        if Utilisateur.objects.filter(username=value).exists():
            print("Un utilisateur avec ce nom d'utilisateur existe déjà")
            raise serializers.ValidationError("Un utilisateur avec ce nom d'utilisateur existe déjà")
        return value