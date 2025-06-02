from rest_framework import serializers
from decimal import Decimal
from django.db import models
from .models import (
    PaiementInscription, PaiementSolidarite, EpargneTransaction,
    Emprunt, Remboursement, AssistanceAccordee, Renflouement,
    PaiementRenflouement
)
from core.serializers import MembreSimpleSerializer, SessionSerializer, TypeAssistanceSerializer

class PaiementInscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer pour les paiements d'inscription
    """
    membre_info = MembreSimpleSerializer(source='membre', read_only=True)
    session_nom = serializers.CharField(source='session.nom', read_only=True)
    
    class Meta:
        model = PaiementInscription
        fields = [
            'id', 'membre', 'membre_info', 'montant', 'date_paiement',
            'session', 'session_nom', 'notes'
        ]

class PaiementSolidariteSerializer(serializers.ModelSerializer):
    """
    Serializer pour les paiements de solidarité
    """
    membre_info = MembreSimpleSerializer(source='membre', read_only=True)
    session_nom = serializers.CharField(source='session.nom', read_only=True)
    
    class Meta:
        model = PaiementSolidarite
        fields = [
            'id', 'membre', 'membre_info', 'session', 'session_nom',
            'montant', 'date_paiement', 'notes'
        ]

class EpargneTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer pour les transactions d'épargne
    """
    membre_info = MembreSimpleSerializer(source='membre', read_only=True)
    session_nom = serializers.CharField(source='session.nom', read_only=True)
    type_transaction_display = serializers.CharField(source='get_type_transaction_display', read_only=True)
    
    class Meta:
        model = EpargneTransaction
        fields = [
            'id', 'membre', 'membre_info', 'type_transaction', 'type_transaction_display',
            'montant', 'session', 'session_nom', 'date_transaction', 'notes'
        ]

class EmpruntSerializer(serializers.ModelSerializer):
    """
    Serializer pour les emprunts AVEC TOUS LES CALCULS
    """
    membre_info = MembreSimpleSerializer(source='membre', read_only=True)
    session_nom = serializers.CharField(source='session_emprunt.nom', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    # Calculs automatiques
    montant_restant_a_rembourser = serializers.ReadOnlyField()
    montant_interets = serializers.ReadOnlyField()
    pourcentage_rembourse = serializers.ReadOnlyField()
    
    # Détails des remboursements
    remboursements_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Emprunt
        fields = [
            'id', 'membre', 'membre_info', 'montant_emprunte', 'taux_interet',
            'montant_total_a_rembourser', 'montant_rembourse', 'montant_restant_a_rembourser',
            'montant_interets', 'pourcentage_rembourse', 'session_emprunt', 'session_nom',
            'date_emprunt', 'statut', 'statut_display', 'notes', 'remboursements_details'
        ]
    
    def get_remboursements_details(self, obj):
        remboursements = obj.remboursements.all()
        return RemboursementSerializer(remboursements, many=True).data

class RemboursementSerializer(serializers.ModelSerializer):
    """
    Serializer pour les remboursements
    """
    emprunt_info = serializers.SerializerMethodField()
    session_nom = serializers.CharField(source='session.nom', read_only=True)
    
    class Meta:
        model = Remboursement
        fields = [
            'id', 'emprunt', 'emprunt_info', 'montant', 'montant_capital',
            'montant_interet', 'session', 'session_nom', 'date_remboursement', 'notes'
        ]
    
    def get_emprunt_info(self, obj):
        return {
            'id': str(obj.emprunt.id),
            'membre_numero': obj.emprunt.membre.numero_membre,
            'membre_nom': obj.emprunt.membre.utilisateur.nom_complet,
            'montant_emprunte': obj.emprunt.montant_emprunte,
            'montant_total_a_rembourser': obj.emprunt.montant_total_a_rembourser
        }

class AssistanceAccordeeSerializer(serializers.ModelSerializer):
    """
    Serializer pour les assistances accordées
    """
    membre_info = MembreSimpleSerializer(source='membre', read_only=True)
    type_assistance_info = TypeAssistanceSerializer(source='type_assistance', read_only=True)
    session_nom = serializers.CharField(source='session.nom', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = AssistanceAccordee
        fields = [
            'id', 'membre', 'membre_info', 'type_assistance', 'type_assistance_info',
            'montant', 'session', 'session_nom', 'date_demande', 'date_paiement',
            'statut', 'statut_display', 'justification', 'notes'
        ]

class RenflouementSerializer(serializers.ModelSerializer):
    """
    Serializer pour les renflouements AVEC TOUS LES CALCULS
    """
    membre_info = MembreSimpleSerializer(source='membre', read_only=True)
    session_nom = serializers.CharField(source='session.nom', read_only=True)
    type_cause_display = serializers.CharField(source='get_type_cause_display', read_only=True)
    
    # Calculs automatiques
    montant_restant = serializers.ReadOnlyField()
    is_solde = serializers.ReadOnlyField()
    pourcentage_paye = serializers.ReadOnlyField()
    
    # Détails des paiements
    paiements_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Renflouement
        fields = [
            'id', 'membre', 'membre_info', 'session', 'session_nom',
            'montant_du', 'montant_paye', 'montant_restant', 'is_solde',
            'pourcentage_paye', 'cause', 'type_cause', 'type_cause_display',
            'date_creation', 'date_derniere_modification', 'paiements_details'
        ]
    
    def get_paiements_details(self, obj):
        paiements = obj.paiements.all()
        return PaiementRenflouementSerializer(paiements, many=True).data

class PaiementRenflouementSerializer(serializers.ModelSerializer):
    """
    Serializer pour les paiements de renflouement
    """
    renflouement_info = serializers.SerializerMethodField()
    session_nom = serializers.CharField(source='session.nom', read_only=True)
    
    class Meta:
        model = PaiementRenflouement
        fields = [
            'id', 'renflouement', 'renflouement_info', 'montant',
            'session', 'session_nom', 'date_paiement', 'notes'
        ]
    
    def get_renflouement_info(self, obj):
        return {
            'id': str(obj.renflouement.id),
            'membre_numero': obj.renflouement.membre.numero_membre,
            'membre_nom': obj.renflouement.membre.utilisateur.nom_complet,
            'montant_total_du': obj.renflouement.montant_du,
            'cause': obj.renflouement.cause
        }

class StatistiquesTransactionsSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques des transactions
    """
    inscriptions = serializers.DictField()
    solidarites = serializers.DictField()
    epargnes = serializers.DictField()
    emprunts = serializers.DictField()
    assistances = serializers.DictField()
    renflouements = serializers.DictField()