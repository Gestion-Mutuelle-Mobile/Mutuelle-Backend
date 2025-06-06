from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from decimal import Decimal, ROUND_HALF_UP
import uuid
from core.models import Membre, Session, Exercice, TypeAssistance
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum, Q
from django.utils import timezone

class PaiementInscription(models.Model):
    """
    Paiements d'inscription par tranche
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    membre = models.ForeignKey(Membre, on_delete=models.CASCADE, related_name='paiements_inscription')
    montant = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Montant payé (FCFA)"
    )
    date_paiement = models.DateTimeField(auto_now_add=True, verbose_name="Date de paiement")
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='paiements_inscription', verbose_name="Session")
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    class Meta:
        verbose_name = "Paiement d'inscription"
        verbose_name_plural = "Paiements d'inscription"
        ordering = ['-date_paiement']
        
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Alimenter le fonds social à chaque paiement d'inscription
        if is_new:
            from core.models import FondsSocial
            fonds = FondsSocial.get_fonds_actuel()
            if fonds:
                fonds.ajouter_montant(
                    self.montant,
                    f"Inscription {self.membre.numero_membre} - Session {self.session.nom}"
                )
    
    def __str__(self):
        return f"{self.membre.numero_membre} - {self.montant:,.0f} FCFA ({self.date_paiement.date()})"

class PaiementSolidarite(models.Model):
    """
    Paiements de solidarité (fonds social) par session
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    membre = models.ForeignKey(Membre, on_delete=models.CASCADE, related_name='paiements_solidarite')
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='paiements_solidarite')
    montant = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Montant payé (FCFA)"
    )
    date_paiement = models.DateTimeField(auto_now_add=True, verbose_name="Date de paiement")
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    class Meta:
        verbose_name = "Paiement de solidarité"
        verbose_name_plural = "Paiements de solidarité"
        ordering = ['-date_paiement']
        unique_together = [['membre', 'session']]
        
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Alimenter le fonds social à chaque paiement de solidarité
        if is_new:
            from core.models import FondsSocial
            fonds = FondsSocial.get_fonds_actuel()
            if fonds:
                fonds.ajouter_montant(
                    self.montant,
                    f"Solidarité {self.membre.numero_membre} - Session {self.session.nom}"
                )
    
    def __str__(self):
        return f"{self.membre.numero_membre} - Session {self.session.nom} - {self.montant:,.0f} FCFA"

class EpargneTransaction(models.Model):
    """
    Transactions d'épargne (dépôts et retraits pour prêts)
    """
    TYPE_CHOICES = [
        ('DEPOT', 'Dépôt'),
        ('RETRAIT_PRET', 'Retrait pour prêt'),
        ('AJOUT_INTERET', 'Ajout d\'intérêt'),
        ('RETOUR_REMBOURSEMENT', 'Retour de remboursement'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    membre = models.ForeignKey(Membre, on_delete=models.CASCADE, related_name='transactions_epargne')
    type_transaction = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type de transaction")
    montant = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name="Montant (FCFA)"
    )
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='transactions_epargne')
    date_transaction = models.DateTimeField(auto_now_add=True, verbose_name="Date de transaction")
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    class Meta:
        verbose_name = "Transaction d'épargne"
        verbose_name_plural = "Transactions d'épargne"
        ordering = ['-date_transaction']
    
    def __str__(self):
        signe = "+" if self.montant >= 0 else ""
        return f"{self.membre.numero_membre} - {self.get_type_transaction_display()} - {signe}{self.montant:,.0f} FCFA"

class Emprunt(models.Model):
    """
    Emprunts effectués par les membres
    """
    STATUS_CHOICES = [
        ('EN_COURS', 'En cours'),
        ('REMBOURSE', 'Remboursé'),
        ('EN_RETARD', 'En retard'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    membre = models.ForeignKey(Membre, on_delete=models.CASCADE, related_name='emprunts')
    montant_emprunte = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Montant emprunté (FCFA)"
    )
    taux_interet = models.DecimalField(
        max_digits=5, decimal_places=2,
        verbose_name="Taux d'intérêt (%)"
    )
    montant_total_a_rembourser = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name="Montant total à rembourser (FCFA)"
    )
    montant_rembourse = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Montant déjà remboursé (FCFA)"
    )
    session_emprunt = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='emprunts')
    date_emprunt = models.DateTimeField(auto_now_add=True, verbose_name="Date d'emprunt")
    statut = models.CharField(max_length=15, choices=STATUS_CHOICES, default='EN_COURS', verbose_name="Statut")
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    class Meta:
        verbose_name = "Emprunt"
        verbose_name_plural = "Emprunts"
        ordering = ['-date_emprunt']
    
    def __str__(self):
        return f"{self.membre.numero_membre} - {self.montant_emprunte:,.0f} FCFA ({self.statut})"
    
    @property
    def montant_restant_a_rembourser(self):
        """Calcule le montant restant à rembourser"""
        return self.montant_total_a_rembourser - self.montant_rembourse
    
    @property
    def montant_interets(self):
        """Calcule le montant des intérêts"""
        return self.montant_total_a_rembourser - self.montant_emprunte
    
    @property
    def pourcentage_rembourse(self):
        """Calcule le pourcentage remboursé"""
        if self.montant_total_a_rembourser == 0:
            return 0
        return (self.montant_rembourse / self.montant_total_a_rembourser) * 100
    
    def save(self, *args, **kwargs):
        # Calcul automatique du montant total à rembourser
        if not self.montant_total_a_rembourser:
            interet = (self.montant_emprunte * self.taux_interet) / 100
            self.montant_total_a_rembourser = self.montant_emprunte + interet
        
        # Vérification du statut
        if self.montant_rembourse >= self.montant_total_a_rembourser:
            self.statut = 'REMBOURSE'
        
        super().save(*args, **kwargs)

class Remboursement(models.Model):
    """
    Remboursements par tranche des emprunts
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emprunt = models.ForeignKey(Emprunt, on_delete=models.CASCADE, related_name='remboursements')
    montant = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Montant remboursé (FCFA)"
    )
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='remboursements')
    date_remboursement = models.DateTimeField(auto_now_add=True, verbose_name="Date de remboursement")
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    # Champs pour la redistribution des intérêts
    montant_capital = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Part capital du remboursement"
    )
    montant_interet = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Part intérêt du remboursement"
    )
    
    class Meta:
        verbose_name = "Remboursement"
        verbose_name_plural = "Remboursements"
        ordering = ['-date_remboursement']
    
    def __str__(self):
        return f"{self.emprunt.membre.numero_membre} - {self.montant:,.0f} FCFA ({self.date_remboursement.date()})"
    
    def save(self, *args, **kwargs):
        # Calcul automatique de la répartition capital/intérêt
        if not self.montant_capital and not self.montant_interet:
            self._calculer_repartition_capital_interet()
        
        super().save(*args, **kwargs)
        
        # Mise à jour du montant remboursé de l'emprunt
        self.emprunt.montant_rembourse = sum(
            r.montant for r in self.emprunt.remboursements.all()
        )
        self.emprunt.save()
        
        # Redistribution des intérêts aux membres
        if self.montant_interet > 0:
            self._redistribuer_interets()
    
    def _calculer_repartition_capital_interet(self):
        """Calcule la répartition entre capital et intérêt du remboursement"""
        emprunt = self.emprunt
        capital_restant = emprunt.montant_emprunte - sum(
            r.montant_capital for r in emprunt.remboursements.exclude(id=self.id)
        )
        
        if self.montant <= capital_restant:
            self.montant_capital = self.montant
            self.montant_interet = Decimal('0')
        else:
            self.montant_capital = capital_restant
            self.montant_interet = self.montant - capital_restant
    
    def _redistribuer_interets(self):
        """Redistribue les intérêts proportionnellement aux épargnes"""
        if self.montant_interet <= 0:
            return
        
        # Calculer le total des épargnes de tous les membres
        total_epargnes = Decimal('0')
        membres_epargnes = {}
        
        for membre in Membre.objects.filter(statut='EN_REGLE'):
            epargne_membre = membre.calculer_epargne_totale()
            if epargne_membre > 0:
                membres_epargnes[membre] = epargne_membre
                total_epargnes += epargne_membre
        
        if total_epargnes == 0:
            return
        
        # Redistribuer proportionnellement
        for membre, epargne_membre in membres_epargnes.items():
            pourcentage = epargne_membre / total_epargnes
            interet_membre = (self.montant_interet * pourcentage).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            
            # Créer la transaction d'épargne pour l'intérêt
            EpargneTransaction.objects.create(
                membre=membre,
                type_transaction='AJOUT_INTERET',
                montant=interet_membre,
                session=self.session,
                notes=f"Intérêt redistributed from emprunt {self.emprunt.id}"
            )
            
            print(f"Intérêt redistributed: {membre.numero_membre} - {interet_membre} FCFA")

class AssistanceAccordee(models.Model):
    """
    Assistances accordées aux membres
    """
    STATUS_CHOICES = [
        ('DEMANDEE', 'Demandée'),
        ('APPROUVEE', 'Approuvée'),
        ('PAYEE', 'Payée'),
        ('REJETEE', 'Rejetée'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    membre = models.ForeignKey(Membre, on_delete=models.CASCADE, related_name='assistances_recues')
    type_assistance = models.ForeignKey(TypeAssistance, on_delete=models.CASCADE, related_name='assistances_accordees')
    montant = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name="Montant accordé (FCFA)"
    )
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='assistances_accordees')
    date_demande = models.DateTimeField(auto_now_add=True, verbose_name="Date de demande")
    date_paiement = models.DateTimeField(null=True, blank=True, verbose_name="Date de paiement")
    statut = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PAYEE', verbose_name="Statut")
    justification = models.TextField(verbose_name="Justification")
    notes = models.TextField(blank=True, verbose_name="Notes administratives")
    
    class Meta:
        verbose_name = "Assistance accordée"
        verbose_name_plural = "Assistances accordées"
        ordering = ['-date_demande']
    
    def __str__(self):
        return f"{self.membre.numero_membre} - {self.type_assistance.nom} - {self.montant:,.0f} FCFA"
    
    def save(self, *args, **kwargs):
        old_statut = None
        if self.pk:
            old_instance = AssistanceAccordee.objects.get(pk=self.pk)
            old_statut = old_instance.statut
        
        # Copier le montant du type d'assistance si pas défini
        if not self.montant:
            self.montant = self.type_assistance.montant
        
        super().save(*args, **kwargs)
        
        # Déclencher le processus quand le statut passe à PAYEE
        # if self.statut == 'PAYEE' and old_statut != 'PAYEE':
        #     if not hasattr(self, '_assistance_payee_traitee'):
        #         self._traiter_paiement_assistance()
        #         self._assistance_payee_traitee = True
        if True:
            if not hasattr(self, '_assistance_payee_traitee'):
                self._traiter_paiement_assistance()
                self._assistance_payee_traitee = True
    
    def _traiter_paiement_assistance(self):
        """
        Traite le paiement d'une assistance:
        1. Prélève du fonds social
        2. Crée les renflouements pour tous les membres en règle
        """
        from core.models import FondsSocial
        from django.utils import timezone
        
        # 1. PRÉLEVER DU FONDS SOCIAL
        fonds = FondsSocial.get_fonds_actuel()
        if not fonds:
            print("ERREUR: Aucun fonds social actuel trouvé")
            return
        
        # Vérifier si le fonds a assez d'argent
        if not fonds.retirer_montant(
            self.montant,
            f"Assistance {self.type_assistance.nom} pour {self.membre.numero_membre}"
        ):
            print(f"ERREUR: Fonds social insuffisant pour l'assistance de {self.montant:,.0f} FCFA")
            return
        
        # Mettre à jour la date de paiement
        if not self.date_paiement:
            self.date_paiement = timezone.now()
            super().save(update_fields=['date_paiement'])
        
        # 2. CRÉER LES RENFLOUEMENTS
        self._creer_renflouement()
        
        print(f"Assistance payée: {self.montant:,.0f} FCFA prélevés du fonds social")
    
    def _creer_renflouement(self):
        """Crée les renflouements pour tous les membres en règle"""
        # Prendre les membres qui étaient en règle AVANT le paiement de l'assistance
        membres_en_regle = Membre.objects.filter(
            statut='EN_REGLE',
            date_inscription__lte=self.date_paiement or timezone.now()
        )
        
        nombre_membres = membres_en_regle.count()
        if nombre_membres == 0:
            print("ATTENTION: Aucun membre en règle pour le renflouement")
            return
        
        montant_par_membre = (self.montant / nombre_membres).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        renflouements_crees = 0
        for membre in membres_en_regle:
            Renflouement.objects.create(
                membre=membre,
                session=self.session,
                montant_du=montant_par_membre,
                cause=f"Assistance {self.type_assistance.nom} pour {self.membre.numero_membre}",
                type_cause='ASSISTANCE'
            )
            renflouements_crees += 1
        
        print(f"Renflouement créé: {renflouements_crees} membres - {montant_par_membre:,.0f} FCFA chacun")

class Renflouement(models.Model):
    """
    Renflouements dus par les membres suite aux sorties d'argent
    """
    TYPE_CAUSE_CHOICES = [
        ('ASSISTANCE', 'Assistance'),
        ('COLLATION', 'Collation'),
        ('AUTRE', 'Autre'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    membre = models.ForeignKey(Membre, on_delete=models.CASCADE, related_name='renflouements')
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='renflouements')
    montant_du = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Montant dû (FCFA)"
    )
    montant_paye = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Montant payé (FCFA)"
    )
    cause = models.TextField(verbose_name="Cause du renflouement",blank=True)
    type_cause = models.CharField(max_length=15, choices=TYPE_CAUSE_CHOICES, verbose_name="Type de cause")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_derniere_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Renflouement"
        verbose_name_plural = "Renflouements"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.membre.numero_membre} - {self.montant_du:,.0f} FCFA ({self.type_cause})"
    
    @property
    def montant_restant(self):
        """Calcule le montant restant à payer"""
        return self.montant_du - self.montant_paye
    
    @property
    def is_solde(self):
        """Vérifie si le renflouement est soldé"""
        return self.montant_paye >= self.montant_du
    
    @property
    def pourcentage_paye(self):
        """Calcule le pourcentage payé"""
        if self.montant_du == 0:
            return 100
        return (self.montant_paye / self.montant_du) * 100

class PaiementRenflouement(models.Model):
    """
    Paiements de renflouement par tranche
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    renflouement = models.ForeignKey(Renflouement, on_delete=models.CASCADE, related_name='paiements')
    montant = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Montant payé (FCFA)"
    )
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='paiements_renflouement')
    date_paiement = models.DateTimeField(auto_now_add=True, verbose_name="Date de paiement")
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    class Meta:
        verbose_name = "Paiement de renflouement"
        verbose_name_plural = "Paiements de renflouement"
        ordering = ['-date_paiement']
    
    def __str__(self):
        return f"{self.renflouement.membre.numero_membre} - {self.montant:,.0f} FCFA ({self.date_paiement.date()})"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Mise à jour du montant payé du renflouement
        self.renflouement.montant_paye = sum(
            p.montant for p in self.renflouement.paiements.all()
        )
        self.renflouement.save()
        
        # CRUCIAL: Alimenter le fonds social avec le paiement de renflouement
        if is_new:
            from core.models import FondsSocial
            fonds = FondsSocial.get_fonds_actuel()
            if fonds:
                fonds.ajouter_montant(
                    self.montant,
                    f"Renflouement {self.renflouement.membre.numero_membre} - {self.renflouement.cause}"
                )