from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum, Q
from django.utils import timezone



def calculer_fonds_social_total():
    """
    Calcule le montant total du fonds social pour l'exercice en cours
    """
    from core.models import FondsSocial
    
    fonds = FondsSocial.get_fonds_actuel()
    if fonds:
        return {
            'montant_total': fonds.montant_total,
            'exercice': fonds.exercice.nom,
            'derniere_modification': fonds.date_modification
        }
    return {
        'montant_total': Decimal('0'),
        'exercice': 'Aucun exercice en cours',
        'derniere_modification': None
    }

def calculer_cumul_epargnes_total():
    """
    Calcule le cumul total des épargnes de tous les membres (le trésor)
    """
    from core.models import Membre
    
    total_epargnes = Decimal('0')
    membres_actifs = Membre.objects.filter(statut__in=['EN_REGLE', 'NON_EN_REGLE'])
    
    for membre in membres_actifs:
        epargne_membre = membre.calculer_epargne_totale()
        total_epargnes += epargne_membre
    
    return {
        'cumul_total_epargnes': total_epargnes,
        'nombre_membres': membres_actifs.count()
    }

def calculer_donnees_administrateur():
    """
    Calcule toutes les données que l'administrateur doit voir
    """
    fonds_social = calculer_fonds_social_total()
    tresor = calculer_cumul_epargnes_total()
    
    # Calcul des montants attendus (emprunts en cours)
    from transactions.models import Emprunt
    emprunts_en_cours = Emprunt.objects.filter(statut='EN_COURS')
    
    montant_attendu_emprunts = sum(
        emprunt.montant_restant_a_rembourser for emprunt in emprunts_en_cours
    )
    
    return {
        'fonds_social': fonds_social,
        'tresor': tresor,
        'emprunts_en_cours': {
            'nombre': emprunts_en_cours.count(),
            'montant_total_attendu': montant_attendu_emprunts
        },
        'situation_globale': {
            'liquidites_totales': fonds_social['montant_total'] + tresor['cumul_total_epargnes'],
            'engagements_totaux': montant_attendu_emprunts
        }
    }

def calculer_donnees_membre_completes(membre):
    """
    Calcule TOUTES les données financières d'un membre
    Cette fonction est cruciale car elle retourne toutes les informations
    que le frontend doit afficher selon les spécifications
    """
    from core.models import ConfigurationMutuelle, Session
    from transactions.models import (
        PaiementInscription, PaiementSolidarite, EpargneTransaction,
        Emprunt, Renflouement
    )
    
    config = ConfigurationMutuelle.get_configuration()
    session_courante = Session.get_session_en_cours()
    
    # 1. INSCRIPTION
    total_paye_inscription = PaiementInscription.objects.filter(
        membre=membre
    ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
    
    inscription_data = {
        'montant_total_inscription': config.montant_inscription,
        'montant_paye_inscription': total_paye_inscription,
        'montant_restant_inscription': config.montant_inscription - total_paye_inscription,
        'inscription_complete': total_paye_inscription >= config.montant_inscription,
        'pourcentage_inscription': (total_paye_inscription / config.montant_inscription * 100) if config.montant_inscription > 0 else 0
    }
    
    # 2. SOLIDARITÉ (SESSION COURANTE + CUMUL DES DETTES)
    solidarite_data = {'sessions_impayees': []}
    
    if session_courante:
        # Solidarité pour la session courante
        paiement_session_courante = PaiementSolidarite.objects.filter(
            membre=membre,
            session=session_courante
        ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
        
        solidarite_data.update({
            'montant_solidarite_session_courante': config.montant_solidarite,
            'montant_paye_session_courante': paiement_session_courante,
            'montant_restant_session_courante': config.montant_solidarite - paiement_session_courante,
            'solidarite_session_courante_complete': paiement_session_courante >= config.montant_solidarite
        })
    
    # Calcul du cumul des dettes de solidarité
    # Pour toutes les sessions depuis l'inscription du membre
    sessions_depuis_inscription = Session.objects.filter(
        exercice__date_debut__gte=membre.date_inscription,
        statut__in=['EN_COURS', 'TERMINEE']
    )
    
    total_solidarite_due = sessions_depuis_inscription.count() * config.montant_solidarite
    total_solidarite_payee = PaiementSolidarite.objects.filter(
        membre=membre,
        session__in=sessions_depuis_inscription
    ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
    
    solidarite_data.update({
        'total_solidarite_due': total_solidarite_due,
        'total_solidarite_payee': total_solidarite_payee,
        'dette_solidarite_cumul': total_solidarite_due - total_solidarite_payee,
        'solidarite_a_jour': total_solidarite_payee >= total_solidarite_due
    })
    
    # 3. ÉPARGNES ET INTÉRÊTS
    transactions_epargne = EpargneTransaction.objects.filter(membre=membre)
    
    epargne_base = transactions_epargne.filter(
        type_transaction='DEPOT'
    ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
    
    retraits_prets = transactions_epargne.filter(
        type_transaction='RETRAIT_PRET'
    ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
    
    interets_recus = transactions_epargne.filter(
        type_transaction='AJOUT_INTERET'
    ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
    
    retours_remboursements = transactions_epargne.filter(
        type_transaction='RETOUR_REMBOURSEMENT'
    ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
    
    epargne_totale = epargne_base - retraits_prets + interets_recus + retours_remboursements
    
    epargne_data = {
        'epargne_base': epargne_base,
        'retraits_pour_prets': retraits_prets,
        'interets_recus': interets_recus,
        'retours_remboursements': retours_remboursements,
        'epargne_totale': epargne_totale,
        'epargne_plus_interets': epargne_totale,  # Dans notre cas, c'est la même chose
        'montant_interets_separe': interets_recus
    }
    
    # 4. EMPRUNTS
    emprunt_en_cours = Emprunt.objects.filter(
        membre=membre,
        statut='EN_COURS'
    ).first()
    
    emprunt_data = {
        'a_emprunt_en_cours': emprunt_en_cours is not None,
        'montant_emprunt_en_cours': emprunt_en_cours.montant_emprunte if emprunt_en_cours else Decimal('0'),
        'montant_total_a_rembourser': emprunt_en_cours.montant_total_a_rembourser if emprunt_en_cours else Decimal('0'),
        'montant_deja_rembourse': emprunt_en_cours.montant_rembourse if emprunt_en_cours else Decimal('0'),
        'montant_restant_a_rembourser': emprunt_en_cours.montant_restant_a_rembourser if emprunt_en_cours else Decimal('0'),
        'pourcentage_rembourse': emprunt_en_cours.pourcentage_rembourse if emprunt_en_cours else 0,
        'nombre_emprunts_total': Emprunt.objects.filter(membre=membre).count()
    }
    
    # Calcul du montant maximum empruntable
    if not emprunt_en_cours and epargne_totale > 0:
        montant_max_empruntable = epargne_totale * config.coefficient_emprunt_max
    else:
        montant_max_empruntable = Decimal('0')
    
    emprunt_data['montant_max_empruntable'] = montant_max_empruntable
    
    # 5. RENFLOUEMENTS
    renflouements_dus = Renflouement.objects.filter(membre=membre)
    
    total_renflouement_du = renflouements_dus.aggregate(
        total=Sum('montant_du')
    )['total'] or Decimal('0')
    
    total_renflouement_paye = renflouements_dus.aggregate(
        total=Sum('montant_paye')
    )['total'] or Decimal('0')
    
    renflouement_data = {
        'total_renflouement_du': total_renflouement_du,
        'total_renflouement_paye': total_renflouement_paye,
        'solde_renflouement_du': total_renflouement_du - total_renflouement_paye,
        'renflouement_a_jour': total_renflouement_paye >= total_renflouement_du,
        'nombre_renflouements': renflouements_dus.count()
    }
    
    # 6. STATUT GLOBAL "EN RÈGLE"
    # Un membre est en règle s'il a payé son inscription complètement
    # et s'il n'a pas de retard critique sur les autres obligations
    en_regle = (
        inscription_data['inscription_complete'] and
        not (solidarite_data['dette_solidarite_cumul'] > config.montant_solidarite * 0) and  # Max 0 sessions de retard
        not (renflouement_data['solde_renflouement_du'] > config.montant_solidarite * 0)  # Max 0x solidarité en renflouement
    )
    
    # 7. DONNÉES CONSOLIDÉES
    donnees_completes = {
        'membre_info': {
            'id': str(membre.id),
            'numero_membre': membre.numero_membre,
            'nom_complet': membre.utilisateur.nom_complet,
            'email': membre.utilisateur.email,
            'telephone': membre.utilisateur.telephone,
            'photo_profil_url': membre.utilisateur.photo_profil.url if membre.utilisateur.photo_profil else None,
            'date_inscription': membre.date_inscription,
            'statut': membre.statut,
            'en_regle': en_regle
        },
        'inscription': inscription_data,
        'solidarite': solidarite_data,
        'epargne': epargne_data,
        'emprunt': emprunt_data,
        'renflouement': renflouement_data,
        'resume_financier': {
            'patrimoine_total': epargne_totale,
            'obligations_totales': (
                inscription_data['montant_restant_inscription'] +
                solidarite_data['dette_solidarite_cumul'] +
                renflouement_data['solde_renflouement_du'] +
                emprunt_data['montant_restant_a_rembourser']
            ),
            'situation_nette': epargne_totale - emprunt_data['montant_restant_a_rembourser']
        }
    }
    
    print(f"Calcul complet pour {membre.numero_membre}: En règle = {en_regle}")
    return donnees_completes