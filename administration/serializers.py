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
    membre_id = serializers.UUIDField(required=False, allow_null=True)
    emprunt = serializers.UUIDField(required=False, allow_null=True)
    session_id = serializers.UUIDField(required=False, allow_null=True)
    montant = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    # Champs alternatifs utilisés comme alias (non déclarés dans le serializer)
    ALIAS_MAP = {
        'membre_id': ['membre', 'membre_id'],
        'session_id': ['session', 'session_id'],
        'montant': ['montant', 'montant_emprunte', 'montant_emprunt', 'montant_paye'],
        'notes': ['notes', 'justification', 'motif']
        # Ajoute ici d'autres alias si besoin
    }

    def to_internal_value(self, data):
        # Reconstruire le dict avec les bons noms
        normalized = {}
        errors = {}
        for field, aliases in self.ALIAS_MAP.items():
            value_found = None
            for alias in aliases:
                if alias in data:
                    value_found = data[alias]
                    break
            normalized[field] = value_found

        # Appel du parent avec le dict reconstruit
        # (Garde les champs non aliasés tel quel)
        for k, v in data.items():
            if k not in sum(self.ALIAS_MAP.values(), []):
                normalized[k] = v

        # Utilise le validateur standard DRF
        return super().to_internal_value(normalized)

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