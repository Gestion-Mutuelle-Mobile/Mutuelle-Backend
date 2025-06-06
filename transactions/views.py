from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters import rest_framework as filters
from django.db import models
from django.db.models import Sum, Q, F
from decimal import Decimal
import logging
from rest_framework.response import Response
from rest_framework import status
from django.db import models, transaction
import logging
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)



from core.models import Membre, Session, TypeAssistance
from .models import (
    PaiementInscription, PaiementSolidarite, EpargneTransaction,
    Emprunt, Remboursement, AssistanceAccordee, Renflouement,
    PaiementRenflouement
)
from .serializers import (
    PaiementInscriptionSerializer, PaiementSolidariteSerializer,
    EpargneTransactionSerializer, EmpruntSerializer, RemboursementSerializer,
    AssistanceAccordeeSerializer, RenflouementSerializer,
    PaiementRenflouementSerializer, StatistiquesTransactionsSerializer
)
from authentication.permissions import IsAdministrateur, IsAdminOrReadOnly

class PaiementInscriptionFilter(filters.FilterSet):
    """
    Filtres ultra-complets pour les paiements d'inscription
    """
    # Filtres membre
    membre = filters.UUIDFilter()
    membre_numero = filters.CharFilter(field_name='membre__numero_membre', lookup_expr='icontains')
    membre_nom = filters.CharFilter(method='filter_membre_nom')
    membre_email = filters.CharFilter(field_name='membre__utilisateur__email', lookup_expr='icontains')
    membre_statut = filters.ChoiceFilter(field_name='membre__statut', choices=models.Model.choices if hasattr(models.Model, 'choices') else [])
    
    # Filtres session
    session = filters.UUIDFilter()
    session_nom = filters.CharFilter(field_name='session__nom', lookup_expr='icontains')
    exercice = filters.UUIDFilter(field_name='session__exercice')
    exercice_nom = filters.CharFilter(field_name='session__exercice__nom', lookup_expr='icontains')
    
    # Filtres montants
    montant = filters.NumberFilter()
    montant_min = filters.NumberFilter(field_name='montant', lookup_expr='gte')
    montant_max = filters.NumberFilter(field_name='montant', lookup_expr='lte')
    montant_range = filters.RangeFilter(field_name='montant')
    
    # Filtres dates
    date_paiement = filters.DateFromToRangeFilter()
    date_paiement_after = filters.DateFilter(field_name='date_paiement', lookup_expr='gte')
    date_paiement_before = filters.DateFilter(field_name='date_paiement', lookup_expr='lte')
    month = filters.NumberFilter(field_name='date_paiement', lookup_expr='month')
    year = filters.NumberFilter(field_name='date_paiement', lookup_expr='year')
    today = filters.BooleanFilter(method='filter_today')
    this_week = filters.BooleanFilter(method='filter_this_week')
    this_month = filters.BooleanFilter(method='filter_this_month')
    this_year = filters.BooleanFilter(method='filter_this_year')
    
    # Filtres avancés
    has_notes = filters.BooleanFilter(method='filter_has_notes')
    
    class Meta:
        model = PaiementInscription
        fields = {
            'montant': ['exact', 'gte', 'lte', 'gt', 'lt'],
            'date_paiement': ['exact', 'gte', 'lte', 'year', 'month', 'day'],
            'notes': ['icontains'],
        }
    
    def filter_membre_nom(self, queryset, name, value):
        return queryset.filter(
            Q(membre__utilisateur__first_name__icontains=value) |
            Q(membre__utilisateur__last_name__icontains=value)
        )
    
    def filter_today(self, queryset, name, value):
        from django.utils import timezone
        if value:
            today = timezone.now().date()
            return queryset.filter(date_paiement__date=today)
        return queryset
    
    def filter_this_week(self, queryset, name, value):
        from django.utils import timezone
        from datetime import timedelta
        if value:
            now = timezone.now()
            week_start = now - timedelta(days=now.weekday())
            return queryset.filter(date_paiement__gte=week_start)
        return queryset
    
    def filter_this_month(self, queryset, name, value):
        from django.utils import timezone
        if value:
            now = timezone.now()
            return queryset.filter(
                date_paiement__year=now.year,
                date_paiement__month=now.month
            )
        return queryset
    
    def filter_this_year(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(date_paiement__year=timezone.now().year)
        return queryset
    
    def filter_has_notes(self, queryset, name, value):
        if value:
            return queryset.exclude(notes='')
        return queryset.filter(notes='')

class PaiementInscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les paiements d'inscription
    """
    queryset = PaiementInscription.objects.select_related(
        'membre__utilisateur', 'session__exercice'
    ).all()
    serializer_class = PaiementInscriptionSerializer
    filterset_class = PaiementInscriptionFilter
    search_fields = [
        'membre__numero_membre', 'membre__utilisateur__first_name',
        'membre__utilisateur__last_name', 'session__nom', 'notes'
    ]
    ordering_fields = ['date_paiement', 'montant', 'membre__numero_membre']
    ordering = ['-date_paiement']
    permission_classes = [AllowAny]



class PaiementSolidariteFilter(filters.FilterSet):
    """
    Filtres pour les paiements de solidarité
    """
    # Mêmes filtres que PaiementInscription + spécifiques
    membre = filters.UUIDFilter()
    membre_numero = filters.CharFilter(field_name='membre__numero_membre', lookup_expr='icontains')
    membre_nom = filters.CharFilter(method='filter_membre_nom')
    session = filters.UUIDFilter()
    session_nom = filters.CharFilter(field_name='session__nom', lookup_expr='icontains')
    session_en_cours = filters.BooleanFilter(method='filter_session_en_cours')
    
    montant_min = filters.NumberFilter(field_name='montant', lookup_expr='gte')
    montant_max = filters.NumberFilter(field_name='montant', lookup_expr='lte')
    
    date_paiement = filters.DateFromToRangeFilter()
    this_month = filters.BooleanFilter(method='filter_this_month')
    this_year = filters.BooleanFilter(method='filter_this_year')
    
    class Meta:
        model = PaiementSolidarite
        fields = {
            'montant': ['exact', 'gte', 'lte'],
            'date_paiement': ['exact', 'gte', 'lte', 'year', 'month'],
        }
    
    def filter_membre_nom(self, queryset, name, value):
        return queryset.filter(
            Q(membre__utilisateur__first_name__icontains=value) |
            Q(membre__utilisateur__last_name__icontains=value)
        )
    
    def filter_session_en_cours(self, queryset, name, value):
        if value:
            return queryset.filter(session__statut='EN_COURS')
        return queryset.exclude(session__statut='EN_COURS')
    
    def filter_this_month(self, queryset, name, value):
        from django.utils import timezone
        if value:
            now = timezone.now()
            return queryset.filter(
                date_paiement__year=now.year,
                date_paiement__month=now.month
            )
        return queryset
    
    def filter_this_year(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(date_paiement__year=timezone.now().year)
        return queryset

class PaiementSolidariteViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les paiements de solidarité
    """
    queryset = PaiementSolidarite.objects.select_related(
        'membre__utilisateur', 'session'
    ).all()
    serializer_class = PaiementSolidariteSerializer
    filterset_class = PaiementSolidariteFilter
    search_fields = [
        'membre__numero_membre', 'membre__utilisateur__first_name',
        'membre__utilisateur__last_name', 'session__nom'
    ]
    ordering_fields = ['date_paiement', 'montant', 'session__date_session']
    ordering = ['-date_paiement']
    permission_classes = [AllowAny]

class EpargneTransactionFilter(filters.FilterSet):
    """
    Filtres pour les transactions d'épargne
    """
    membre = filters.UUIDFilter()
    membre_numero = filters.CharFilter(field_name='membre__numero_membre', lookup_expr='icontains')
    membre_nom = filters.CharFilter(method='filter_membre_nom')
    
    type_transaction = filters.ChoiceFilter(choices=EpargneTransaction.TYPE_CHOICES)
    type_depot = filters.BooleanFilter(method='filter_type_depot')
    type_retrait = filters.BooleanFilter(method='filter_type_retrait')
    type_interet = filters.BooleanFilter(method='filter_type_interet')
    
    montant_min = filters.NumberFilter(field_name='montant', lookup_expr='gte')
    montant_max = filters.NumberFilter(field_name='montant', lookup_expr='lte')
    montant_positif = filters.BooleanFilter(method='filter_montant_positif')
    montant_negatif = filters.BooleanFilter(method='filter_montant_negatif')
    
    session = filters.UUIDFilter()
    session_nom = filters.CharFilter(field_name='session__nom', lookup_expr='icontains')
    
    date_transaction = filters.DateFromToRangeFilter()
    this_month = filters.BooleanFilter(method='filter_this_month')
    this_year = filters.BooleanFilter(method='filter_this_year')
    
    class Meta:
        model = EpargneTransaction
        fields = {
            'type_transaction': ['exact'],
            'montant': ['exact', 'gte', 'lte', 'gt', 'lt'],
            'date_transaction': ['exact', 'gte', 'lte', 'year', 'month'],
        }
    
    def filter_membre_nom(self, queryset, name, value):
        return queryset.filter(
            Q(membre__utilisateur__first_name__icontains=value) |
            Q(membre__utilisateur__last_name__icontains=value)
        )
    
    def filter_type_depot(self, queryset, name, value):
        if value:
            return queryset.filter(type_transaction='DEPOT')
        return queryset.exclude(type_transaction='DEPOT')
    
    def filter_type_retrait(self, queryset, name, value):
        if value:
            return queryset.filter(type_transaction='RETRAIT_PRET')
        return queryset.exclude(type_transaction='RETRAIT_PRET')
    
    def filter_type_interet(self, queryset, name, value):
        if value:
            return queryset.filter(type_transaction='AJOUT_INTERET')
        return queryset.exclude(type_transaction='AJOUT_INTERET')
    
    def filter_montant_positif(self, queryset, name, value):
        if value:
            return queryset.filter(montant__gt=0)
        return queryset.filter(montant__lte=0)
    
    def filter_montant_negatif(self, queryset, name, value):
        if value:
            return queryset.filter(montant__lt=0)
        return queryset.filter(montant__gte=0)
    
    def filter_this_month(self, queryset, name, value):
        from django.utils import timezone
        if value:
            now = timezone.now()
            return queryset.filter(
                date_transaction__year=now.year,
                date_transaction__month=now.month
            )
        return queryset
    
    def filter_this_year(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(date_transaction__year=timezone.now().year)
        return queryset

class EpargneTransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les transactions d'épargne
    """
    queryset = EpargneTransaction.objects.select_related(
        'membre__utilisateur', 'session'
    ).all()
    serializer_class = EpargneTransactionSerializer
    filterset_class = EpargneTransactionFilter
    search_fields = [
        'membre__numero_membre', 'membre__utilisateur__first_name',
        'type_transaction', 'notes'
    ]
    ordering_fields = ['date_transaction', 'montant', 'type_transaction']
    ordering = ['-date_transaction']
    permission_classes = [AllowAny]

class EmpruntFilter(filters.FilterSet):
    """
    Filtres ultra-complets pour les emprunts
    """
    membre = filters.UUIDFilter()
    membre_numero = filters.CharFilter(field_name='membre__numero_membre', lookup_expr='icontains')
    membre_nom = filters.CharFilter(method='filter_membre_nom')
    
    statut = filters.ChoiceFilter(choices=Emprunt.STATUS_CHOICES)
    en_cours = filters.BooleanFilter(method='filter_en_cours')
    rembourse = filters.BooleanFilter(method='filter_rembourse')
    en_retard = filters.BooleanFilter(method='filter_en_retard')
    
    # Filtres montants
    montant_emprunte_min = filters.NumberFilter(field_name='montant_emprunte', lookup_expr='gte')
    montant_emprunte_max = filters.NumberFilter(field_name='montant_emprunte', lookup_expr='lte')
    montant_total_min = filters.NumberFilter(field_name='montant_total_a_rembourser', lookup_expr='gte')
    montant_total_max = filters.NumberFilter(field_name='montant_total_a_rembourser', lookup_expr='lte')
    montant_rembourse_min = filters.NumberFilter(field_name='montant_rembourse', lookup_expr='gte')
    montant_rembourse_max = filters.NumberFilter(field_name='montant_rembourse', lookup_expr='lte')
    
    # Filtres taux
    taux_interet_min = filters.NumberFilter(field_name='taux_interet', lookup_expr='gte')
    taux_interet_max = filters.NumberFilter(field_name='taux_interet', lookup_expr='lte')
    
    # Filtres pourcentages
    pourcentage_rembourse_min = filters.NumberFilter(method='filter_pourcentage_min')
    pourcentage_rembourse_max = filters.NumberFilter(method='filter_pourcentage_max')
    presque_rembourse = filters.BooleanFilter(method='filter_presque_rembourse')  # >80%
    peu_rembourse = filters.BooleanFilter(method='filter_peu_rembourse')  # <20%
    
    # Filtres dates
    date_emprunt = filters.DateFromToRangeFilter()
    this_month = filters.BooleanFilter(method='filter_this_month')
    this_year = filters.BooleanFilter(method='filter_this_year')
    
    # Filtres session
    session_emprunt = filters.UUIDFilter()
    session_nom = filters.CharFilter(field_name='session_emprunt__nom', lookup_expr='icontains')
    
    class Meta:
        model = Emprunt
        fields = {
            'statut': ['exact'],
            'montant_emprunte': ['exact', 'gte', 'lte'],
            'montant_total_a_rembourser': ['exact', 'gte', 'lte'],
            'montant_rembourse': ['exact', 'gte', 'lte'],
            'taux_interet': ['exact', 'gte', 'lte'],
            'date_emprunt': ['exact', 'gte', 'lte', 'year', 'month'],
        }
    
    def filter_membre_nom(self, queryset, name, value):
        return queryset.filter(
            Q(membre__utilisateur__first_name__icontains=value) |
            Q(membre__utilisateur__last_name__icontains=value)
        )
    
    def filter_en_cours(self, queryset, name, value):
        if value:
            return queryset.filter(statut='EN_COURS')
        return queryset.exclude(statut='EN_COURS')
    
    def filter_rembourse(self, queryset, name, value):
        if value:
            return queryset.filter(statut='REMBOURSE')
        return queryset.exclude(statut='REMBOURSE')
    
    def filter_en_retard(self, queryset, name, value):
        if value:
            return queryset.filter(statut='EN_RETARD')
        return queryset.exclude(statut='EN_RETARD')
    
    def filter_pourcentage_min(self, queryset, name, value):
        return queryset.filter(
            montant_rembourse__gte=F('montant_total_a_rembourser') * value / 100
        )
    
    def filter_pourcentage_max(self, queryset, name, value):
        return queryset.filter(
            montant_rembourse__lte=F('montant_total_a_rembourser') * value / 100
        )
    
    def filter_presque_rembourse(self, queryset, name, value):
        if value:
            return queryset.filter(
                montant_rembourse__gte=F('montant_total_a_rembourser') * 0.8
            )
        return queryset
    
    def filter_peu_rembourse(self, queryset, name, value):
        if value:
            return queryset.filter(
                montant_rembourse__lte=F('montant_total_a_rembourser') * 0.2
            )
        return queryset
    
    def filter_this_month(self, queryset, name, value):
        from django.utils import timezone
        if value:
            now = timezone.now()
            return queryset.filter(
                date_emprunt__year=now.year,
                date_emprunt__month=now.month
            )
        return queryset
    
    def filter_this_year(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(date_emprunt__year=timezone.now().year)
        return queryset

class EmpruntViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les emprunts avec TOUS LES CALCULS
    """
    queryset = Emprunt.objects.select_related(
        'membre__utilisateur', 'session_emprunt'
    ).prefetch_related('remboursements').all()
    serializer_class = EmpruntSerializer
    filterset_class = EmpruntFilter
    search_fields = [
        'membre__numero_membre', 'membre__utilisateur__first_name',
        'membre__utilisateur__last_name', 'notes'
    ]
    ordering_fields = [
        'date_emprunt', 'montant_emprunte', 'montant_total_a_rembourser',
        'montant_rembourse', 'taux_interet'
    ]
    ordering = ['-date_emprunt']
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def statistiques(self, request):
        """
        Statistiques des emprunts
        """
        queryset = self.get_queryset()
        
        total_emprunts = queryset.count()
        emprunts_en_cours = queryset.filter(statut='EN_COURS').count()
        emprunts_rembourses = queryset.filter(statut='REMBOURSE').count()
        emprunts_en_retard = queryset.filter(statut='EN_RETARD').count()
        
        montant_total_emprunte = queryset.aggregate(
            total=Sum('montant_emprunte'))['total'] or Decimal('0')
        montant_total_a_rembourser = queryset.aggregate(
            total=Sum('montant_total_a_rembourser'))['total'] or Decimal('0')
        montant_total_rembourse = queryset.aggregate(
            total=Sum('montant_rembourse'))['total'] or Decimal('0')
        
        return Response({
            'nombre_emprunts': {
                'total': total_emprunts,
                'en_cours': emprunts_en_cours,
                'rembourses': emprunts_rembourses,
                'en_retard': emprunts_en_retard
            },
            'montants': {
                'total_emprunte': montant_total_emprunte,
                'total_a_rembourser': montant_total_a_rembourser,
                'total_rembourse': montant_total_rembourse,
                'solde_restant': montant_total_a_rembourser - montant_total_rembourse
            },
            'pourcentages': {
                'taux_remboursement_global': (montant_total_rembourse / montant_total_a_rembourser * 100) if montant_total_a_rembourser > 0 else 0
            }
        })

class RenflouementFilter(filters.FilterSet):
    """
    Filtres pour les renflouements
    """
    membre = filters.UUIDFilter()
    membre_numero = filters.CharFilter(field_name='membre__numero_membre', lookup_expr='icontains')
    membre_nom = filters.CharFilter(method='filter_membre_nom')
    
    session = filters.UUIDFilter()
    session_nom = filters.CharFilter(field_name='session__nom', lookup_expr='icontains')
    
    type_cause = filters.ChoiceFilter(choices=Renflouement.TYPE_CAUSE_CHOICES)
    cause_assistance = filters.BooleanFilter(method='filter_cause_assistance')
    cause_collation = filters.BooleanFilter(method='filter_cause_collation')
    
    # Filtres statuts
    solde = filters.BooleanFilter(method='filter_solde')
    non_solde = filters.BooleanFilter(method='filter_non_solde')
    partiellement_paye = filters.BooleanFilter(method='filter_partiellement_paye')
    
    # Filtres montants
    montant_du_min = filters.NumberFilter(field_name='montant_du', lookup_expr='gte')
    montant_du_max = filters.NumberFilter(field_name='montant_du', lookup_expr='lte')
    montant_paye_min = filters.NumberFilter(field_name='montant_paye', lookup_expr='gte')
    montant_paye_max = filters.NumberFilter(field_name='montant_paye', lookup_expr='lte')
    
    # Filtres dates
    date_creation = filters.DateFromToRangeFilter()
    this_month = filters.BooleanFilter(method='filter_this_month')
    this_year = filters.BooleanFilter(method='filter_this_year')
    
    class Meta:
        model = Renflouement
        fields = {
            'type_cause': ['exact'],
            'montant_du': ['exact', 'gte', 'lte'],
            'montant_paye': ['exact', 'gte', 'lte'],
            'date_creation': ['exact', 'gte', 'lte', 'year', 'month'],
        }
    
    def filter_membre_nom(self, queryset, name, value):
        return queryset.filter(
            Q(membre__utilisateur__first_name__icontains=value) |
            Q(membre__utilisateur__last_name__icontains=value)
        )
    
    def filter_cause_assistance(self, queryset, name, value):
        if value:
            return queryset.filter(type_cause='ASSISTANCE')
        return queryset.exclude(type_cause='ASSISTANCE')
    
    def filter_cause_collation(self, queryset, name, value):
        if value:
            return queryset.filter(type_cause='COLLATION')
        return queryset.exclude(type_cause='COLLATION')
    
    def filter_solde(self, queryset, name, value):
        if value:
            return queryset.filter(montant_paye__gte=F('montant_du'))
        return queryset.filter(montant_paye__lt=F('montant_du'))
    
    def filter_non_solde(self, queryset, name, value):
        if value:
            return queryset.filter(montant_paye__lt=F('montant_du'))
        return queryset.filter(montant_paye__gte=F('montant_du'))
    
    def filter_partiellement_paye(self, queryset, name, value):
        if value:
            return queryset.filter(
                montant_paye__gt=0,
                montant_paye__lt=F('montant_du')
            )
        return queryset
    
    def filter_this_month(self, queryset, name, value):
        from django.utils import timezone
        if value:
            now = timezone.now()
            return queryset.filter(
                date_creation__year=now.year,
                date_creation__month=now.month
            )
        return queryset
    
    def filter_this_year(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(date_creation__year=timezone.now().year)
        return queryset

class RenflouementViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les renflouements avec TOUS LES CALCULS
    """
    queryset = Renflouement.objects.select_related(
        'membre__utilisateur', 'session'
    ).prefetch_related('paiements').all()
    serializer_class = RenflouementSerializer
    filterset_class = RenflouementFilter
    search_fields = [
        'membre__numero_membre', 'membre__utilisateur__first_name',
        'cause', 'type_cause'
    ]
    ordering_fields = [
        'date_creation', 'montant_du', 'montant_paye', 'type_cause'
    ]
    ordering = ['-date_creation']
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def statistiques(self, request):
        """
        Statistiques des renflouements
        """
        queryset = self.get_queryset()
        
        total_renflouements = queryset.count()
        renflouements_soldes = queryset.filter(montant_paye__gte=F('montant_du')).count()
        renflouements_non_soldes = total_renflouements - renflouements_soldes
        
        montant_total_du = queryset.aggregate(
            total=Sum('montant_du'))['total'] or Decimal('0')
        montant_total_paye = queryset.aggregate(
            total=Sum('montant_paye'))['total'] or Decimal('0')
        montant_restant = montant_total_du - montant_total_paye
        
        return Response({
            'nombre_renflouements': {
                'total': total_renflouements,
                'soldes': renflouements_soldes,
                'non_soldes': renflouements_non_soldes
            },
            'montants': {
                'total_du': montant_total_du,
                'total_paye': montant_total_paye,
                'montant_restant': montant_restant
            },
            'pourcentages': {
                'taux_recouvrement': (montant_total_paye / montant_total_du * 100) if montant_total_du > 0 else 0,
                'taux_solde': (renflouements_soldes / total_renflouements * 100) if total_renflouements > 0 else 0
            }
        })

# ViewSets similaires pour les autres modèles...
class RemboursementViewSet(viewsets.ModelViewSet):
    queryset = Remboursement.objects.select_related('emprunt__membre__utilisateur', 'session').all()
    serializer_class = RemboursementSerializer
    filterset_fields = ['emprunt', 'session', 'montant']
    search_fields = ['emprunt__membre__numero_membre', 'notes']
    ordering = ['-date_remboursement']
    permission_classes = [AllowAny]

logger = logging.getLogger(__name__)

class AssistanceAccordeeViewSet(viewsets.ModelViewSet):
    queryset = AssistanceAccordee.objects.select_related(
        'membre__utilisateur', 'type_assistance', 'session'
    ).all()
    serializer_class = AssistanceAccordeeSerializer
    filterset_fields = ['membre', 'type_assistance', 'statut', 'session']
    search_fields = ['membre__numero_membre', 'justification', 'notes']
    ordering = ['-date_demande']
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        print("ASSISTANCE CREATE - Data reçue:", request.data)
        
        # 🔧 AUTO-AJOUTER LA SESSION COURANTE SI MANQUANTE
        data = request.data.copy()
        if 'session' not in data or not data['session']:
            try:
                from core.models import Session
                current_session = Session.objects.filter(statut='EN_COURS').first()
                if current_session:
                    data['session'] = current_session.id
                    print(f"Session courante ajoutée automatiquement: {current_session.id}")
                else:
                    print("ERREUR: Aucune session active trouvée")
                    return Response({
                        'error': 'Aucune session active disponible'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(f"ERREUR lors de la récupération de session: {e}")
        
        # 🔍 VÉRIFICATION DES FOREIGN KEYS AVANT CRÉATION
        try:
            print(f"🔍 Vérification membre ID: {data.get('membre')}")
            membre = Membre.objects.get(id=data.get('membre'))
            print(f"✅ Membre trouvé: {membre}")
            
            print(f"🔍 Vérification type_assistance ID: {data.get('type_assistance')}")
            type_assistance = TypeAssistance.objects.get(id=data.get('type_assistance'))
            print(f"✅ Type assistance trouvé: {type_assistance}")
            
            print(f"🔍 Vérification session ID: {data.get('session')}")
            session = Session.objects.get(id=data.get('session'))
            print(f"✅ Session trouvée: {session}")
            
        except Exception as e:
            print(f"❌ ERREUR Foreign Key: {e}")
            return Response({
                'error': f'Objet non trouvé: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            print("ASSISTANCE ERRORS:", serializer.errors)
            return Response({
                'error': 'Données invalides',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            print("🔍 Début de la création...")
            
            # 🔧 UTILISE UNE TRANSACTION POUR ISOLER L'ERREUR
            with transaction.atomic():
                print("🔍 Appel perform_create...")
                assistance = serializer.save()
                print(f"✅ AssistanceAccordee créée avec ID: {assistance.id}")
                
                # 🔍 VÉRIFICATION POST-CRÉATION
                print("🔍 Vérification post-création...")
                created_assistance = AssistanceAccordee.objects.get(id=assistance.id)
                print(f"✅ Assistance vérifiée: {created_assistance}")
                
            print("✅ ASSISTANCE CREATED:", serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"❌ ASSISTANCE EXCEPTION: {str(e)}")
            print(f"❌ EXCEPTION TYPE: {type(e)}")
            import traceback
            print(f"❌ TRACEBACK: {traceback.format_exc()}")
            
            return Response({
                'error': 'Erreur lors de la création',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class PaiementRenflouementViewSet(viewsets.ModelViewSet):
    queryset = PaiementRenflouement.objects.select_related(
        'renflouement__membre__utilisateur', 'session'
    ).all()
    serializer_class = PaiementRenflouementSerializer
    filterset_fields = ['renflouement', 'session', 'montant']
    search_fields = ['renflouement__membre__numero_membre', 'notes']
    ordering = ['-date_paiement']
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        print("=" * 60)
        print("🔍 PAIEMENT RENFLOUEMENT CREATE")
        print(f"📡 Data reçue: {request.data}")
        print(f"👤 User: {request.user}")
        print(f"🔗 Headers: {dict(request.headers)}")
        
        # 🔍 VÉRIFICATION DES FOREIGN KEYS AVANT CRÉATION
        data = request.data.copy()
        
        try:
            # Vérifier le renflouement
            if 'renflouement' in data:
                print(f"🔍 Vérification renflouement ID: {data.get('renflouement')}")
                renflouement = Renflouement.objects.get(id=data.get('renflouement'))
                print(f"✅ Renflouement trouvé: {renflouement}")
                print(f"   - Membre: {renflouement.membre.numero_membre}")
                print(f"   - Montant dû: {renflouement.montant_du}")
                print(f"   - Cause: {renflouement.cause}")
            
            # Vérifier la session
            if 'session' in data:
                print(f"🔍 Vérification session ID: {data.get('session')}")
                session = Session.objects.get(id=data.get('session'))
                print(f"✅ Session trouvée: {session}")
            elif not data.get('session'):
                # Auto-assigner la session courante si manquante
                current_session = Session.objects.filter(statut="EN_COURS").first()
                if current_session:
                    data['session'] = current_session.id
                    print(f"✅ Session auto-assignée: {current_session.nom}")
                else:
                    print("❌ Aucune session active trouvée")
                    return Response({
                        'error': 'Aucune session active disponible'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier le montant
            montant = data.get('montant')
            print(f"🔍 Montant: {montant} (type: {type(montant)})")
            if montant:
                try:
                    montant_decimal = Decimal(str(montant))
                    print(f"✅ Montant converti: {montant_decimal}")
                except Exception as e:
                    print(f"❌ Erreur conversion montant: {e}")
                    return Response({
                        'error': f'Montant invalide: {e}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            print(f"❌ ERREUR Foreign Key: {e}")
            print(f"❌ Type erreur: {type(e)}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return Response({
                'error': f'Objet non trouvé: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 🔍 VALIDATION AVEC SERIALIZER
        print(f"🔍 Data finale envoyée au serializer: {data}")
        serializer = self.get_serializer(data=data)
        
        print(f"🔍 Validation du serializer...")
        if not serializer.is_valid():
            print(f"❌ ERREURS SERIALIZER: {serializer.errors}")
            print(f"❌ ERREURS DÉTAILLÉES:")
            for field, errors in serializer.errors.items():
                print(f"   - {field}: {errors}")
            
            return Response({
                'error': 'Données invalides',
                'details': serializer.errors,
                'data_received': data
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"✅ Serializer valide, validated_data: {serializer.validated_data}")
        
        # 🔍 CRÉATION
        try:
            print("🔍 Début de la création...")
            
            # Utiliser une transaction pour isoler l'erreur
            from django.db import transaction
            with transaction.atomic():
                print("🔍 Appel perform_create...")
                self.perform_create(serializer)
                print(f"✅ PaiementRenflouement créé avec succès")
                
            print("✅ PAIEMENT RENFLOUEMENT CREATED:")
            print(f"   Data: {serializer.data}")
            print("=" * 60)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"❌ EXCEPTION CRÉATION: {str(e)}")
            print(f"❌ EXCEPTION TYPE: {type(e)}")
            import traceback
            print(f"❌ TRACEBACK COMPLET:")
            print(traceback.format_exc())
            print("=" * 60)
            
            return Response({
                'error': 'Erreur lors de la création',
                'details': str(e),
                'type': str(type(e))
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)