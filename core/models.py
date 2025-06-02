from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
import uuid
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum, Q
from Backend.settings import MUTUELLE_DEFAULTS

class ConfigurationMutuelle(models.Model):
    """
    Configuration globale de la mutuelle (paramètres modifiables)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    montant_inscription = models.DecimalField(
        max_digits=12, decimal_places=2, default=MUTUELLE_DEFAULTS["INSCRIPTION_AMOUNT"],
        validators=[MinValueValidator(0)],
        verbose_name="Montant inscription (FCFA)"
    )
    montant_solidarite = models.DecimalField(
        max_digits=12, decimal_places=2, default=MUTUELLE_DEFAULTS["SOLIDARITE_AMOUNT"],
        validators=[MinValueValidator(0)],
        verbose_name="Montant solidarité par session (FCFA)"
    )
    taux_interet = models.DecimalField(
        max_digits=5, decimal_places=2, default=MUTUELLE_DEFAULTS["INTEREST_RATE"],
        validators=[MinValueValidator(0)],
        verbose_name="Taux d'intérêt (%)"
    )
    coefficient_emprunt_max = models.IntegerField(
        default=MUTUELLE_DEFAULTS["LOAN_MULTIPLIER"],
        validators=[MinValueValidator(1)],
        verbose_name="Coefficient multiplicateur max pour emprunts"
    )
    duree_exercice_mois = models.IntegerField(
        default=MUTUELLE_DEFAULTS["EXERCISE_DURATION_MONTHS"],
        validators=[MinValueValidator(1)],
        verbose_name="Durée exercice (mois)"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuration Mutuelle"
        verbose_name_plural = "Configurations Mutuelle"
    
    def __str__(self):
        return f"Configuration Mutuelle (Modifiée le {self.date_modification.date()})"
    
    @classmethod
    def get_configuration(cls):
        """Retourne la configuration actuelle ou en crée une par défaut"""
        config = cls.objects.first()
        if not config:
            config = cls.objects.create()
        return config

class Exercice(models.Model):
    """
    Exercice de la mutuelle (généralement 1 an)
    """
    STATUS_CHOICES = [
        ('EN_COURS', 'En cours'),
        ('TERMINE', 'Terminé'),
        ('PLANIFIE', 'Planifié'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100, verbose_name="Nom de l'exercice")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    statut = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PLANIFIE', verbose_name="Statut")
    description = models.TextField(blank=True, verbose_name="Description")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Exercice"
        verbose_name_plural = "Exercices"
        ordering = ['-date_debut']
        unique_together = [['date_debut', 'date_fin']]
    
    def __str__(self):
        return f"{self.nom} ({self.date_debut} - {self.date_fin})"
    
    @property
    def is_en_cours(self):
        return self.statut == 'EN_COURS'
    
    @classmethod
    def get_exercice_en_cours(cls):
        """Retourne l'exercice en cours"""
        return cls.objects.filter(statut='EN_COURS').first()

class Session(models.Model):
    """
    Session mensuelle dans un exercice
    """
    STATUS_CHOICES = [
        ('EN_COURS', 'En cours'),
        ('TERMINEE', 'Terminée'),
        ('PLANIFIEE', 'Planifiée'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exercice = models.ForeignKey(Exercice, on_delete=models.CASCADE, related_name='sessions', verbose_name="Exercice")
    nom = models.CharField(max_length=100, verbose_name="Nom de la session")
    date_session = models.DateField(verbose_name="Date de la session")
    montant_collation = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Montant collation (FCFA)"
    )
    statut = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PLANIFIEE', verbose_name="Statut")
    description = models.TextField(blank=True, verbose_name="Description")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Session"
        verbose_name_plural = "Sessions"
        ordering = ['-date_session']
        unique_together = [['exercice', 'date_session']]
        constraints = [
            models.UniqueConstraint(
                fields=['exercice'],
                condition=models.Q(statut='EN_COURS'),
                name='unique_session_en_cours_par_exercice'
            )
        ]
    
    def __str__(self):
        return f"{self.nom} - {self.date_session} ({self.exercice.nom})"
    
    @property
    def is_en_cours(self):
        return self.statut == 'EN_COURS'
    
    @classmethod
    def get_session_en_cours(cls):
        """Retourne la session en cours"""
        return cls.objects.filter(statut='EN_COURS').first()
    def save(self, *args, **kwargs):
        old_statut = None
        if self.pk:
            old_instance = Session.objects.get(pk=self.pk)
            old_statut = old_instance.statut
        
        super().save(*args, **kwargs)
        
        # Traiter la collation quand la session devient EN_COURS
        if self.statut == 'EN_COURS' and old_statut != 'EN_COURS':
            if self.montant_collation > 0:
                self._traiter_collation()
    
    def _traiter_collation(self):
        """
        Traite le paiement de la collation:
        1. Prélève du fonds social
        2. Crée les renflouements pour tous les membres en règle
        """
        from django.utils import timezone
        
        # 1. PRÉLEVER DU FONDS SOCIAL
        fonds = FondsSocial.get_fonds_actuel()
        if not fonds:
            print("ERREUR: Aucun fonds social actuel trouvé pour la collation")
            return
        
        if not fonds.retirer_montant(
            self.montant_collation,
            f"Collation Session {self.nom} - {self.date_session}"
        ):
            print(f"ERREUR: Fonds social insuffisant pour la collation de {self.montant_collation:,.0f} FCFA")
            return
        
        # 2. CRÉER LES RENFLOUEMENTS
        self._creer_renflouement_collation()
        
        print(f"Collation payée: {self.montant_collation:,.0f} FCFA prélevés du fonds social")
    
    def _creer_renflouement_collation(self):
        """Crée les renflouements pour la collation"""
        membres_en_regle = Membre.objects.filter(
            statut='EN_REGLE',
            date_inscription__lte=self.date_session
        )
        
        nombre_membres = membres_en_regle.count()
        if nombre_membres == 0:
            print("ATTENTION: Aucun membre en règle pour le renflouement de collation")
            return
        
        montant_par_membre = (self.montant_collation / nombre_membres).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        for membre in membres_en_regle:
            from transactions.models import Renflouement
            Renflouement.objects.create(
                membre=membre,
                session=self,
                montant_du=montant_par_membre,
                cause=f"Collation Session {self.nom} - {self.date_session}",
                type_cause='COLLATION'
            )
        
        print(f"Renflouement collation créé: {nombre_membres} membres - {montant_par_membre:,.0f} FCFA chacun")

class TypeAssistance(models.Model):
    """
    Types d'assistance disponibles (mariage, décès, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom du type")
    montant = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Montant (FCFA)"
    )
    description = models.TextField(blank=True, verbose_name="Description")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Type d'assistance"
        verbose_name_plural = "Types d'assistance"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} - {self.montant:,.0f} FCFA"

class Membre(models.Model):
    """
    Modèle Membre lié à un Utilisateur
    """
    STATUS_CHOICES = [
        ('EN_REGLE', 'En règle'),
        ('NON_EN_REGLE', 'Non en règle'),
        ('SUSPENDU', 'Suspendu'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='membre_profile')
    numero_membre = models.CharField(max_length=20, unique=True, verbose_name="Numéro de membre")
    date_inscription = models.DateField(verbose_name="Date d'inscription")
    statut = models.CharField(max_length=15, choices=STATUS_CHOICES, default='NON_EN_REGLE', verbose_name="Statut")
    exercice_inscription = models.ForeignKey(Exercice, on_delete=models.CASCADE, related_name='nouveaux_membres', verbose_name="Exercice d'inscription")
    session_inscription = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='nouveaux_membres', verbose_name="Session d'inscription")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Membre"
        verbose_name_plural = "Membres"
        ordering = ['-date_inscription']
    
    def __str__(self):
        return f"{self.numero_membre} - {self.utilisateur.nom_complet}"
    
    @property
    def is_en_regle(self):
        return self.statut == 'EN_REGLE'
    

    def calculer_epargne_totale(self):
        """Calcule l'épargne totale du membre"""
        from transactions.models import EpargneTransaction
        
        transactions = EpargneTransaction.objects.filter(membre=self)
        
        depots = transactions.filter(type_transaction='DEPOT').aggregate(
            total=Sum('montant'))['total'] or Decimal('0')
        
        retraits = transactions.filter(type_transaction='RETRAIT_PRET').aggregate(
            total=Sum('montant'))['total'] or Decimal('0')
        
        interets = transactions.filter(type_transaction='AJOUT_INTERET').aggregate(
            total=Sum('montant'))['total'] or Decimal('0')
        
        retours = transactions.filter(type_transaction='RETOUR_REMBOURSEMENT').aggregate(
            total=Sum('montant'))['total'] or Decimal('0')
        
        return depots - retraits + interets + retours
    
    def get_donnees_completes(self):
        """Retourne toutes les données financières du membre"""
        from core.utils import calculer_donnees_membre_completes
        return calculer_donnees_membre_completes(self)
    
    def peut_emprunter(self, montant):
        """Vérifie si le membre peut emprunter un montant donné"""
        from core.models import ConfigurationMutuelle
        from transactions.models import Emprunt
        
        # Vérifier qu'il n'a pas d'emprunt en cours
        if Emprunt.objects.filter(membre=self, statut='EN_COURS').exists():
            return False, "Vous avez déjà un emprunt en cours"
        
        # Vérifier qu'il est en règle
        if not self.is_en_regle:
            return False, "Vous devez être en règle pour emprunter"
        
        # Vérifier le montant maximum
        config = ConfigurationMutuelle.get_configuration()
        epargne_totale = self.calculer_epargne_totale()
        montant_max = epargne_totale * config.coefficient_emprunt_max
        
        if montant > montant_max:
            return False, f"Montant maximum empruntable: {montant_max:,.0f} FCFA"
        
        return True, "Emprunt autorisé"
    
    def calculer_statut_en_regle(self):
        """Calcule si le membre est en règle selon tous les critères"""
        donnees = self.get_donnees_completes()
        return donnees['membre_info']['en_regle']
    
    def save(self, *args, **kwargs):
        if not self.numero_membre:
            # Génération automatique du numéro de membre
            last_member = Membre.objects.order_by('numero_membre').last()
            if last_member:
                last_number = int(last_member.numero_membre.split('-')[-1])
                self.numero_membre = f"ENS-{last_number + 1:04d}"
            else:
                self.numero_membre = "ENS-0001"
        super().save(*args, **kwargs)
        
        


class FondsSocial(models.Model):
    """
    Suivi du fonds social total de la mutuelle
    Le fonds social est alimenté par les solidarités et les renflouements
    Il est diminué par les assistances et les collations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exercice = models.OneToOneField(Exercice, on_delete=models.CASCADE, related_name='fonds_social')
    montant_total = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name="Montant total du fonds social (FCFA)"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Fonds Social"
        verbose_name_plural = "Fonds Sociaux"
    
    def __str__(self):
        return f"Fonds Social {self.exercice.nom} - {self.montant_total:,.0f} FCFA"
    
    @classmethod
    def get_fonds_actuel(cls):
        """Retourne le fonds social de l'exercice en cours"""
        exercice_actuel = Exercice.get_exercice_en_cours()
        if exercice_actuel:
            fonds, created = cls.objects.get_or_create(exercice=exercice_actuel)
            return fonds
        return None
    
    def ajouter_montant(self, montant, description=""):
        """Ajoute un montant au fonds social"""
        self.montant_total += montant
        self.save()
        
        # Log de l'opération
        MouvementFondsSocial.objects.create(
            fonds_social=self,
            type_mouvement='ENTREE',
            montant=montant,
            description=description
        )
        print(f"Fonds Social: +{montant:,.0f} FCFA - {description}")
    
    def retirer_montant(self, montant, description=""):
        """Retire un montant du fonds social"""
        if self.montant_total >= montant:
            self.montant_total -= montant
            self.save()
            
            # Log de l'opération
            MouvementFondsSocial.objects.create(
                fonds_social=self,
                type_mouvement='SORTIE',
                montant=montant,
                description=description
            )
            print(f"Fonds Social: -{montant:,.0f} FCFA - {description}")
            return True
        else:
            print(f"ERREUR: Fonds insuffisant. Disponible: {self.montant_total:,.0f}, Demandé: {montant:,.0f}")
            return False

class MouvementFondsSocial(models.Model):
    """
    Historique des mouvements du fonds social
    """
    TYPE_CHOICES = [
        ('ENTREE', 'Entrée'),
        ('SORTIE', 'Sortie'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fonds_social = models.ForeignKey(FondsSocial, on_delete=models.CASCADE, related_name='mouvements')
    type_mouvement = models.CharField(max_length=10, choices=TYPE_CHOICES)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    date_mouvement = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Mouvement Fonds Social"
        verbose_name_plural = "Mouvements Fonds Social"
        ordering = ['-date_mouvement']
    
    def __str__(self):
        signe = "+" if self.type_mouvement == 'ENTREE' else "-"
        return f"{signe}{self.montant:,.0f} FCFA - {self.description[:50]}"