from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters import rest_framework as filters
from django.db import models, transaction
from django.db.models import Sum, Count, Q, F
from decimal import Decimal
from django.utils import timezone
from authentication.models import Utilisateur
from core.models import (
    ConfigurationMutuelle, Exercice, Session, Membre, FondsSocial
)
from transactions.models import (
    PaiementInscription, PaiementSolidarite, EpargneTransaction,
    Emprunt, Remboursement, AssistanceAccordee, Renflouement,
    PaiementRenflouement
)
from decimal import Decimal, InvalidOperation
from .serializers import (
    CreerMembreCompletSerializer, DashboardAdministrateurSerializer, GestionMembreSerializer,
    GestionTransactionSerializer, RapportFinancierSerializer,
    StatistiquesGlobalesSerializer
)
from authentication.permissions import IsAdministrateur
from core.utils import calculer_donnees_administrateur

class AdministrationDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet principal pour le dashboard administrateur
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def dashboard_complet(self, request):
        """
        Retourne TOUTES les données du dashboard administrateur
        """
        donnees = calculer_donnees_administrateur()
        
        # Ajouter des données supplémentaires
        donnees.update({
            'derniers_paiements': self._get_derniers_paiements(),
            'alertes': self._get_alertes(),
            'activite_recente': self._get_activite_recente(),
            'membres_problematiques': self._get_membres_problematiques()
        })
        # Calculer les stats de renflouement
        def _get_renflouements_stats():
            print("CALCUL DES REMFLOUEMENTS")
            
            qs = Renflouement.objects.all()
            total_du = qs.aggregate(total=Sum('montant_du'))['total'] or Decimal('0')
            total_paye = qs.aggregate(total=Sum('montant_paye'))['total'] or Decimal('0')
            taux_recouvrement = float(total_paye) / float(total_du) * 100 if total_du > 0 else 100
            
            data = {
                "montants": {
                    "total_du": float(total_du),
                    "total_paye": float(total_paye),
                },
                "pourcentages": {
                    "taux_recouvrement": round(taux_recouvrement, 2)
                }
            }
            print(data)

            return data
        donnees['renflouements'] = _get_renflouements_stats()
                
        serializer = DashboardAdministrateurSerializer(donnees)
        return Response(serializer.data)
    
    def _get_derniers_paiements(self):
        """Derniers paiements de tous types"""
        from django.contrib.contenttypes.models import ContentType
        
        # Derniers paiements inscription
        paiements_inscription = PaiementInscription.objects.select_related(
            'membre__utilisateur'
        ).order_by('-date_paiement')[:5]
        
        # Derniers paiements solidarité
        paiements_solidarite = PaiementSolidarite.objects.select_related(
            'membre__utilisateur'
        ).order_by('-date_paiement')[:5]
        
        # Derniers remboursements
        remboursements = Remboursement.objects.select_related(
            'emprunt__membre__utilisateur'
        ).order_by('-date_remboursement')[:5]
        
        return {
            'inscriptions': [
                {
                    'membre': p.membre.numero_membre,
                    'montant': p.montant,
                    'date': p.date_paiement,
                    'type': 'inscription'
                } for p in paiements_inscription
            ],
            'solidarites': [
                {
                    'membre': p.membre.numero_membre,
                    'montant': p.montant,
                    'date': p.date_paiement,
                    'type': 'solidarite'
                } for p in paiements_solidarite
            ],
            'remboursements': [
                {
                    'membre': r.emprunt.membre.numero_membre,
                    'montant': r.montant,
                    'date': r.date_remboursement,
                    'type': 'remboursement'
                } for r in remboursements
            ]
        }
    
    def _get_alertes(self):
        """Alertes pour l'administrateur"""
        alertes = []
        
        # Membres avec beaucoup de retard
        membres_retard = Membre.objects.filter(
            renflouements__montant_paye__lt=F('renflouements__montant_du')
        ).annotate(
            dette_renflouement=Sum(F('renflouements__montant_du') - F('renflouements__montant_paye'))
        ).filter(dette_renflouement__gt=50000)  # Plus de 50k de retard
        
        for membre in membres_retard:
            alertes.append({
                'type': 'RETARD_RENFLOUEMENT',
                'message': f"{membre.numero_membre} a {membre.dette_renflouement:,.0f} FCFA de retard",
                'priorite': 'HAUTE',
                'membre_id': str(membre.id)
            })
        
        # Emprunts en retard
        emprunts_retard = Emprunt.objects.filter(statut='EN_RETARD')
        for emprunt in emprunts_retard:
            alertes.append({
                'type': 'EMPRUNT_RETARD',
                'message': f"Emprunt de {emprunt.membre.numero_membre} en retard",
                'priorite': 'HAUTE',
                'emprunt_id': str(emprunt.id)
            })
        
        # Fonds social faible
        fonds = FondsSocial.get_fonds_actuel()
        if fonds and fonds.montant_total < 100000:  # Moins de 100k
            alertes.append({
                'type': 'FONDS_FAIBLE',
                'message': f"Fonds social faible: {fonds.montant_total:,.0f} FCFA",
                'priorite': 'MOYENNE'
            })
        
        return alertes
    
    def _get_activite_recente(self):
        """Activité récente dans la mutuelle"""
        from datetime import timedelta
        
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        
        return {
            'nouveaux_membres': Membre.objects.filter(date_creation__gte=week_ago).count(),
            'nouveaux_emprunts': Emprunt.objects.filter(date_emprunt__gte=week_ago).count(),
            'assistances_demandees': AssistanceAccordee.objects.filter(date_demande__gte=week_ago).count(),
            'total_paiements': (
                PaiementInscription.objects.filter(date_paiement__gte=week_ago).aggregate(
                    total=Sum('montant'))['total'] or Decimal('0')
            ) + (
                PaiementSolidarite.objects.filter(date_paiement__gte=week_ago).aggregate(
                    total=Sum('montant'))['total'] or Decimal('0')
            )
        }
    
    def _get_membres_problematiques(self):
        """Membres ayant des problèmes financiers"""
        # Membres avec inscription non complète depuis plus de 3 mois
        from datetime import timedelta
        three_months_ago = timezone.now() - timedelta(days=90)
        
        config = ConfigurationMutuelle.get_configuration()
        
        membres_problematiques = []
        
        # Inscription non terminée
        membres_inscription_incomplete = Membre.objects.filter(
            date_inscription__lte=three_months_ago
        ).annotate(
            total_paye=Sum('paiements_inscription__montant')
        ).filter(
            Q(total_paye__isnull=True) | Q(total_paye__lt=config.montant_inscription)
        )
        
        for membre in membres_inscription_incomplete:
            total_paye = membre.total_paye or Decimal('0')
            membres_problematiques.append({
                'membre_id': str(membre.id),
                'numero': membre.numero_membre,
                'nom': membre.utilisateur.nom_complet,
                'probleme': 'INSCRIPTION_INCOMPLETE',
                'details': f"Payé {total_paye:,.0f} sur {config.montant_inscription:,.0f}"
            })
        
        return membres_problematiques[:10]  # Top 10

class GestionMembresViewSet(viewsets.ViewSet):
    """
    ViewSet pour la gestion des membres par l'admin
    """
    permission_classes = [IsAdministrateur]
    
    @action(detail=False, methods=['post'])
    def ajouter_paiement_inscription(self, request):
        """
        Ajouter un paiement d'inscription pour un membre
        """
        serializer = GestionTransactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            membre = Membre.objects.get(id=serializer.validated_data['membre_id'])
            session = Session.get_session_en_cours()
            
            if not session:
                return Response(
                    {'error': 'Aucune session en cours'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            paiement = PaiementInscription.objects.create(
                membre=membre,
                montant=serializer.validated_data['montant'],
                session=session,
                notes=serializer.validated_data.get('notes', '')
            )
            
            # Mettre à jour le statut du membre si inscription complète
            config = ConfigurationMutuelle.get_configuration()
            total_paye = PaiementInscription.objects.filter(
                membre=membre
            ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
            
            if total_paye >= config.montant_inscription and membre.statut != 'EN_REGLE':
                
                try:
                    if membre.calculer_statut_en_regle() :
                        membre.statut = 'EN_REGLE'
                        membre.save()
                except e :
                    print(f"Erreur de calcul de sttus en regle : {e} ")
                    pass
                print("MEMEBRE EN REGLE POUR INSCRIPTION")
            
            return Response({
                'message': 'Paiement inscription ajouté avec succès',
                'paiement_id': str(paiement.id),
                'nouveau_statut': membre.statut,
                'total_paye': total_paye
            })
            
        except Membre.DoesNotExist:
            return Response(
                {'error': 'Membre introuvable'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def ajouter_paiement_solidarite(self, request):
        """
        Ajouter un paiement de solidarité pour un membre
        """
        serializer = GestionTransactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            membre = Membre.objects.get(id=serializer.validated_data['membre_id'])
            session_id = serializer.validated_data.get('session_id')
            
            if session_id:
                session = Session.objects.get(id=session_id)
            else:
                session = Session.get_session_en_cours()
            
            if not session:
                return Response(
                    {'error': 'Session introuvable'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Vérifier si déjà payé pour cette session
            paiement_existant = PaiementSolidarite.objects.filter(
                membre=membre, session=session
            ).first()
            
            if paiement_existant:
                # Mettre à jour le montant
                paiement_existant.montant += serializer.validated_data['montant']
                paiement_existant.save()
                paiement = paiement_existant
            else:
                # Créer nouveau paiement
                paiement = PaiementSolidarite.objects.create(
                    membre=membre,
                    session=session,
                    montant=serializer.validated_data['montant'],
                    notes=serializer.validated_data.get('notes', '')
                )
            
            return Response({
                'message': 'Paiement solidarité ajouté avec succès',
                'paiement_id': str(paiement.id),
                'montant_total': paiement.montant
            })
            
        except (Membre.DoesNotExist, Session.DoesNotExist):
            return Response(
                {'error': 'Membre ou session introuvable'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def ajouter_epargne(self, request):
        """
        Ajouter une épargne pour un membre
        """
        serializer = GestionTransactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            membre = Membre.objects.get(id=serializer.validated_data['membre_id'])
            session = Session.get_session_en_cours()
            
            if not session:
                return Response(
                    {'error': 'Aucune session en cours'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            epargne = EpargneTransaction.objects.create(
                membre=membre,
                type_transaction='DEPOT',
                montant=serializer.validated_data['montant'],
                session=session,
                notes=serializer.validated_data.get('notes', '')
            )
            
            # Calculer nouvelle épargne totale
            nouvelle_epargne = membre.calculer_epargne_totale()
            
            return Response({
                'message': 'Épargne ajoutée avec succès',
                'transaction_id': str(epargne.id),
                'nouvelle_epargne_totale': nouvelle_epargne
            })
            
        except Membre.DoesNotExist:
            return Response(
                {'error': 'Membre introuvable'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def creer_emprunt(self, request):
        """
        Créer un emprunt pour un membre avec logs détaillés et robustesse
        """
        print("=" * 100)
        print("🔍 CRÉATION EMPRUNT - DÉBUT")
        print(f"📡 User: {request.user}")
        print(f"📡 Data reçue: {request.data}")
        print(f"📡 Headers: {dict(request.headers)}")
        print(f"📡 Method: {request.method}")
        print(f"📡 Content-Type: {request.content_type}")
        print("=" * 50)

        try:
            # 🔧 ÉTAPE 1: Validation du serializer
            print("🔍 ÉTAPE 1: Validation du serializer")
            serializer = GestionTransactionSerializer(data=request.data)
            print(f"🔍 Validation en cours...")
            if not serializer.is_valid():
                print(f"❌ ERREURS SERIALIZER: {serializer.errors}")
                print(f"❌ ERREURS DÉTAILLÉES:")
                for field, errors in serializer.errors.items():
                    print(f"   - {field}: {errors}")
                return Response({
                    'error': 'Données invalides',
                    'details': serializer.errors,
                    'data_received': request.data
                }, status=status.HTTP_400_BAD_REQUEST)
            print(f"✅ Serializer valide, validated_data: {serializer.validated_data}")

            # 🔧 ÉTAPE 2: Récupération du membre
            membre_id = serializer.validated_data.get('membre_id')
            if not membre_id:
                error_msg = "ID du membre manquant dans les données"
                print(f"❌ ERREUR: {error_msg}")
                return Response({
                    'error': error_msg,
                    'data_received': serializer.validated_data
                }, status=status.HTTP_400_BAD_REQUEST)
            try:
                membre = Membre.objects.select_related('utilisateur').get(id=membre_id)
                print(f"✅ Membre trouvé: {membre.numero_membre} - {membre.utilisateur.nom_complet}")
            except Membre.DoesNotExist:
                error_msg = f"Membre avec ID {membre_id} introuvable"
                print(f"❌ ERREUR: {error_msg}")
                return Response({
                    'error': error_msg,
                    'membre_id': membre_id
                }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                error_msg = f"Erreur lors de la récupération du membre: {e}"
                print(f"❌ ERREUR: {error_msg}")
                return Response({
                    'error': error_msg,
                    'membre_id': membre_id
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 🔧 ÉTAPE 3: Validation du montant
            montant = serializer.validated_data.get('montant')
            print(f"🔍 Montant demandé: {montant}")
            try:
                montant_decimal = Decimal(str(montant))
                print(f"✅ Montant converti en Decimal: {montant_decimal}")

                if montant_decimal <= 0:
                    error_msg = "Le montant de l'emprunt doit être positif"
                    print(f"❌ ERREUR MONTANT: {error_msg}")
                    return Response({
                        'error': error_msg,
                        'montant_recu': montant
                    }, status=status.HTTP_400_BAD_REQUEST)
            except (InvalidOperation, TypeError, ValueError) as e:
                error_msg = f"Montant invalide: {e}"
                print(f"❌ ERREUR CONVERSION MONTANT: {error_msg}")
                return Response({
                    'error': error_msg,
                    'montant_recu': montant
                }, status=status.HTTP_400_BAD_REQUEST)

            # 🔧 ÉTAPE 4: Vérifier si le membre peut emprunter
            print("🔍 ÉTAPE 4: Vérification de la capacité d'emprunt")
            peut_emprunter, message = membre.peut_emprunter(montant_decimal)
            print(f"🔍 Peut emprunter ? {peut_emprunter} | Raison: {message}")
            if not peut_emprunter:
                print(f"❌ REFUS: {message}")
                return Response(
                    {'error': message},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 🔧 ÉTAPE 5: Récupération de la session en cours
            print("🔍 ÉTAPE 5: Récupération de la session en cours")
            try:
                session = Session.get_session_en_cours()
                if not session:
                    error_msg = "Aucune session en cours"
                    print(f"❌ ERREUR SESSION: {error_msg}")
                    return Response(
                        {'error': error_msg},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                print(f"✅ Session trouvée: {session.nom} ({session.id})")
            except Exception as e:
                error_msg = f"Erreur lors de la récupération de la session en cours: {e}"
                print(f"❌ ERREUR: {error_msg}")
                return Response({
                    'error': error_msg
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 🔧 ÉTAPE 6: Récupération de la config mutuelle
            print("🔍 ÉTAPE 6: Récupération de la configuration mutuelle")
            try:
                config = ConfigurationMutuelle.get_configuration()
                print(f"✅ Config récupérée: taux_interet={config.taux_interet}")
            except Exception as e:
                error_msg = f"Erreur lors de la récupération de la configuration: {e}"
                print(f"❌ ERREUR: {error_msg}")
                return Response({
                    'error': error_msg
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 🔧 ÉTAPE 7: Création de l'emprunt avec transaction
            print("🔍 ÉTAPE 7: Création de l'emprunt et transaction épargne")
            notes = serializer.validated_data.get('notes', '')
            try:
                from django.db import transaction as db_transaction
                with db_transaction.atomic():
                    print("🔍 Début transaction DB...")
                    emprunt = Emprunt.objects.create(
                        membre=membre,
                        montant_emprunte=montant_decimal,
                        taux_interet=config.taux_interet,
                        session_emprunt=session,
                        notes=notes
                    )
                    print(f"✅ Emprunt créé: {emprunt.id} pour {emprunt.montant_emprunte} F à {emprunt.taux_interet}%")
                    # Créer la transaction d'épargne (retrait pour prêt)
                    EpargneTransaction.objects.create(
                        membre=membre,
                        type_transaction='RETRAIT_PRET',
                        montant=-montant_decimal,  # Négatif car c'est un retrait
                        session=session,
                        notes=f"Retrait pour emprunt {emprunt.id}"
                    )
                    print(f"✅ Transaction épargne créée pour emprunt {emprunt.id}")
                    emprunt.refresh_from_db()
                    response_data = {
                        'message': 'Emprunt créé avec succès',
                        'emprunt_id': str(emprunt.id),
                        'montant_emprunte': float(emprunt.montant_emprunte),
                        'montant_a_rembourser': float(getattr(emprunt, 'montant_total_a_rembourser', 0)),
                        'taux_interet': float(emprunt.taux_interet)
                    }
                    print(f"✅ Données de réponse: {response_data}")
                    print("=" * 100)
                    return Response(response_data, status=status.HTTP_201_CREATED)
            except Exception as e:
                print(f"❌ EXCEPTION LORS DE LA CRÉATION: {str(e)}")
                print(f"❌ TYPE D'EXCEPTION: {type(e)}")
                import traceback
                print(f"❌ TRACEBACK COMPLET:\n{traceback.format_exc()}")
                print("=" * 100)
                return Response({
                    'error': 'Erreur lors de la création de l\'emprunt',
                    'details': str(e),
                    'type': str(type(e))
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            print(f"❌ EXCEPTION GÉNÉRALE: {str(e)}")
            print(f"❌ TYPE D'EXCEPTION: {type(e)}")
            import traceback
            print(f"❌ TRACEBACK COMPLET:\n{traceback.format_exc()}")
            print("=" * 100)
            return Response({
                'error': 'Erreur interne du serveur',
                'details': str(e),
                'type': str(type(e))
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    @action(detail=False, methods=['post'])
    def ajouter_remboursement(self, request):
        """
        Ajouter un remboursement pour un emprunt
        """
        print("=" * 100)
        print("🔍 AJOUT REMBOURSEMENT - DÉBUT")
        print(f"📡 User: {request.user}")
        print(f"📡 Data reçue: {request.data}")
        print(f"📡 Headers: {dict(request.headers)}")
        print(f"📡 Method: {request.method}")
        print(f"📡 Content-Type: {request.content_type}")
        print("=" * 50)
        
        try:
            # 🔧 ÉTAPE 1: Validation du serializer
            print("🔍 ÉTAPE 1: Validation du serializer")
            serializer = GestionTransactionSerializer(data=request.data)
            
            print(f"🔍 Validation en cours...")
            if not serializer.is_valid():
                print(f"❌ ERREURS SERIALIZER: {serializer.errors}")
                print(f"❌ ERREURS DÉTAILLÉES:")
                for field, errors in serializer.errors.items():
                    print(f"   - {field}: {errors}")
                
                return Response({
                    'error': 'Données invalides',
                    'details': serializer.errors,
                    'data_received': request.data
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"✅ Serializer valide, validated_data: {serializer.validated_data}")
            
            # 🔧 ÉTAPE 2: Récupération de l'emprunt
            print("🔍 ÉTAPE 2: Récupération de l'emprunt")
            emprunt_id = serializer.validated_data.get('emprunt')
            print(f"🔍 Recherche emprunt avec ID: {emprunt_id}")
            
            if not emprunt_id:
                error_msg = "ID de l'emprunt manquant dans les données"
                print(f"❌ ERREUR: {error_msg}")
                return Response({
                    'error': error_msg,
                    'data_received': serializer.validated_data
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                emprunt = Emprunt.objects.select_related('membre__utilisateur', 'session_emprunt').get(id=emprunt_id)
                print(f"✅ Emprunt trouvé:")
                print(f"   - ID: {emprunt.id}")
                print(f"   - Membre: {emprunt.membre.numero_membre} - {emprunt.membre.utilisateur.nom_complet}")
                print(f"   - Montant emprunté: {emprunt.montant_emprunte}")
                print(f"   - Montant total à rembourser: {emprunt.montant_total_a_rembourser}")
                print(f"   - Montant déjà remboursé: {emprunt.montant_rembourse}")
                print(f"   - Montant restant: {emprunt.montant_restant_a_rembourser}")
                print(f"   - Statut: {emprunt.statut}")
                print(f"   - Session: {emprunt.session_emprunt.nom}")
                print(f"   - Date emprunt: {emprunt.date_emprunt}")
                print(f"   - Date max remboursement: {getattr(emprunt, 'date_remboursement_max', 'N/A')}")
                
            except Emprunt.DoesNotExist:
                error_msg = f"Emprunt avec ID {emprunt_id} introuvable"
                print(f"❌ ERREUR: {error_msg}")
                return Response({
                    'error': error_msg,
                    'emprunt_id': emprunt_id
                }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                error_msg = f"Erreur lors de la récupération de l'emprunt: {e}"
                print(f"❌ ERREUR: {error_msg}")
                return Response({
                    'error': error_msg,
                    'emprunt_id': emprunt_id
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 🔧 ÉTAPE 3: Validation du statut de l'emprunt
            print("🔍 ÉTAPE 3: Validation du statut de l'emprunt")
            print(f"🔍 Statut actuel: {emprunt.statut}")
            
            if emprunt.statut not in ['EN_COURS', 'EN_RETARD']:
                error_msg = f"Cet emprunt n'est pas remboursable (statut: {emprunt.statut})"
                print(f"❌ ERREUR STATUT: {error_msg}")
                return Response({
                    'error': error_msg,
                    'statut_actuel': emprunt.statut,
                    'statuts_autorises': ['EN_COURS', 'EN_RETARD']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"✅ Statut valide pour remboursement: {emprunt.statut}")
            
            # 🔧 ÉTAPE 4: Validation du montant
            print("🔍 ÉTAPE 4: Validation du montant")
            montant = serializer.validated_data['montant']
            print(f"🔍 Montant demandé: {montant}")
            print(f"🔍 Montant restant à rembourser: {emprunt.montant_restant_a_rembourser}")
            
            try:
                montant_decimal = Decimal(str(montant))
                print(f"✅ Montant converti en Decimal: {montant_decimal}")
                
                if montant_decimal <= 0:
                    error_msg = "Le montant du remboursement doit être positif"
                    print(f"❌ ERREUR MONTANT: {error_msg}")
                    return Response({
                        'error': error_msg,
                        'montant_recu': montant
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Vérification du montant restant
                montant_restant = emprunt.montant_restant_a_rembourser
                if montant_decimal > montant_restant:
                    error_msg = f'Montant trop élevé. Restant à rembourser: {montant_restant}'
                    print(f"❌ ERREUR MONTANT TROP ÉLEVÉ: {error_msg}")
                    return Response({
                        'error': error_msg,
                        'montant_demande': float(montant_decimal),
                        'montant_restant': float(montant_restant),
                        'montant_max_autorise': float(montant_restant)
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                print(f"✅ Montant validé: {montant_decimal}")
                
            except (InvalidOperation, TypeError, ValueError) as e:
                error_msg = f"Montant invalide: {e}"
                print(f"❌ ERREUR CONVERSION MONTANT: {error_msg}")
                return Response({
                    'error': error_msg,
                    'montant_recu': montant
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 🔧 ÉTAPE 5: Récupération de la session
            print("🔍 ÉTAPE 5: Récupération de la session")
            
            try:
                session = Session.get_session_en_cours()
                if not session:
                    error_msg = "Aucune session en cours disponible"
                    print(f"❌ ERREUR SESSION: {error_msg}")
                    return Response({
                        'error': error_msg
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                print(f"✅ Session trouvée:")
                print(f"   - ID: {session.id}")
                print(f"   - Nom: {session.nom}")
                print(f"   - Statut: {session.statut}")
                print(f"   - Date début: {session.date_creation}")
                
            except Exception as e:
                error_msg = f"Erreur lors de la récupération de la session: {e}"
                print(f"❌ ERREUR SESSION: {error_msg}")
                return Response({
                    'error': error_msg
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 🔧 ÉTAPE 6: Vérification des remboursements existants
            print("🔍 ÉTAPE 6: Vérification des remboursements existants")
            
            try:
                remboursements_existants = Remboursement.objects.filter(emprunt=emprunt)
                print(f"🔍 Nombre de remboursements existants: {remboursements_existants.count()}")
                
                if remboursements_existants.exists():
                    print("🔍 Remboursements existants:")
                    for i, remb in enumerate(remboursements_existants[:5], 1):  # Afficher max 5
                        print(f"   {i}. ID: {remb.id} - Montant: {remb.montant} - Date: {remb.date_remboursement}")
                    
                    if remboursements_existants.count() > 5:
                        print(f"   ... et {remboursements_existants.count() - 5} autres")
                else:
                    print("   Aucun remboursement existant")
                    
            except Exception as e:
                print(f"⚠️ Erreur lors de la vérification des remboursements existants: {e}")
            
            # 🔧 ÉTAPE 7: Préparation des données pour création
            print("🔍 ÉTAPE 7: Préparation des données pour création")
            
            notes = serializer.validated_data.get('notes', '')
            print(f"🔍 Notes: '{notes}'")
            
            creation_data = {
                'emprunt': emprunt,
                'montant': montant_decimal,
                'session': session,
                'notes': notes
            }
            print(f"🔍 Données de création: {creation_data}")
            
            # 🔧 ÉTAPE 8: Création du remboursement avec transaction
            print("🔍 ÉTAPE 8: Création du remboursement")
            
            try:
                from django.db import transaction as db_transaction
                
                with db_transaction.atomic():
                    print("🔍 Début de la transaction...")
                    
                    # Sauvegarder l'état avant modification
                    ancien_montant_rembourse = emprunt.montant_rembourse
                    ancien_statut = emprunt.statut
                    
                    print(f"🔍 État avant création:")
                    print(f"   - Ancien montant remboursé: {ancien_montant_rembourse}")
                    print(f"   - Ancien statut: {ancien_statut}")
                    
                    # Créer le remboursement
                    print("🔍 Création de l'instance Remboursement...")
                    remboursement = Remboursement.objects.create(**creation_data)
                    
                    print(f"✅ Remboursement créé:")
                    print(f"   - ID: {remboursement.id}")
                    print(f"   - Montant total: {remboursement.montant}")
                    print(f"   - Montant capital: {getattr(remboursement, 'montant_capital', 'N/A')}")
                    print(f"   - Montant intérêt: {getattr(remboursement, 'montant_interet', 'N/A')}")
                    print(f"   - Date: {remboursement.date_remboursement}")
                    print(f"   - Session: {remboursement.session.nom}")
                    print(f"   - Notes: '{remboursement.notes}'")
                    
                    # Recharger l'emprunt pour voir les modifications
                    print("🔍 Rechargement de l'emprunt...")
                    emprunt.refresh_from_db()
                    
                    print(f"✅ État après création:")
                    print(f"   - Nouveau montant remboursé: {emprunt.montant_rembourse}")
                    print(f"   - Nouveau montant restant: {emprunt.montant_restant_a_rembourser}")
                    print(f"   - Nouveau statut: {emprunt.statut}")
                    print(f"   - Pourcentage remboursé: {emprunt.pourcentage_rembourse:.2f}%")
                    
                    # Préparer la réponse
                    response_data = {
                        'message': 'Remboursement ajouté avec succès',
                        'remboursement_id': str(remboursement.id),
                        'montant_rembourse': float(remboursement.montant),
                        'montant_capital': float(getattr(remboursement, 'montant_capital', 0)),
                        'montant_interet': float(getattr(remboursement, 'montant_interet', 0)),
                        'nouveau_solde': float(emprunt.montant_restant_a_rembourser),
                        'nouveau_statut': emprunt.statut,
                        'pourcentage_rembourse': float(emprunt.pourcentage_rembourse),
                        'emprunt_complete': emprunt.statut == 'REMBOURSE'
                    }
                    
                    print(f"✅ REMBOURSEMENT CRÉÉ AVEC SUCCÈS")
                    print(f"✅ Données de réponse: {response_data}")
                    print("=" * 100)
                    
                    return Response(response_data, status=status.HTTP_201_CREATED)
                    
            except Exception as e:
                print(f"❌ EXCEPTION LORS DE LA CRÉATION: {str(e)}")
                print(f"❌ TYPE D'EXCEPTION: {type(e)}")
                import traceback
                print(f"❌ TRACEBACK COMPLET:")
                print(traceback.format_exc())
                print("=" * 100)
                
                return Response({
                    'error': 'Erreur lors de la création du remboursement',
                    'details': str(e),
                    'type': str(type(e))
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            print(f"❌ EXCEPTION GÉNÉRALE: {str(e)}")
            print(f"❌ TYPE D'EXCEPTION: {type(e)}")
            import traceback
            print(f"❌ TRACEBACK COMPLET:")
            print(traceback.format_exc())
            print("=" * 100)
            
            return Response({
                'error': 'Erreur interne du serveur',
                'details': str(e),
                'type': str(type(e))
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   
    # Ajouter cette méthode dans la classe GestionMembresViewSet

    @action(detail=False, methods=['post'])
    def creer_membre_complet(self, request):
        """
        Créer un membre complet (utilisateur + membre) en une seule fois
        """
        print("*****************REQUETE DE CREATION DE MEMEBRE***************************")
        print(request.data)
        print("****************************************************************************")
        
        
        
        
        try:
            serializer = CreerMembreCompletSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                
                
                if serializer.validated_data.get('photo_profil'):
                    utilisateur_data = {
                    'username': serializer.validated_data['username'],
                    'email': serializer.validated_data['email'],
                    'first_name': serializer.validated_data['first_name'],
                    'last_name': serializer.validated_data['last_name'],
                    'telephone': serializer.validated_data['telephone'],
                    'role': 'MEMBRE',
                    'photo_profil': serializer.validated_data.get('photo_profil')
                    }
                else:
                    # 1. Créer l'utilisateur
                    utilisateur_data = {
                        'username': serializer.validated_data['username'],
                        'email': serializer.validated_data['email'],
                        'first_name': serializer.validated_data['first_name'],
                        'last_name': serializer.validated_data['last_name'],
                        'telephone': serializer.validated_data['telephone'],
                        'role': 'MEMBRE'
                    }
                
                
                utilisateur = Utilisateur.objects.create_user(
                    password=serializer.validated_data.get('password', '000000'),
                    **utilisateur_data
                )
                
                # 2. Créer le membre
                exercice_actuel = Exercice.get_exercice_en_cours()
                session_actuelle = Session.get_session_en_cours()
                
                if not exercice_actuel:
                    print("Aucun exercice en cours pour l\'inscription")
                    return Response(
                        {'error': 'Aucun exercice en cours pour l\'inscription'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if not session_actuelle:
                    print("Aucune session en cours pour l\'inscription")
                    return Response(
                        {'error': 'Aucune session en cours pour l\'inscription'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                membre = Membre.objects.create(
                    utilisateur=utilisateur,
                    date_inscription=serializer.validated_data.get('date_inscription', timezone.now().date()),
                    exercice_inscription=exercice_actuel,
                    session_inscription=session_actuelle,
                    statut='NON_EN_REGLE'  # Par défaut
                )
                
                # 3. Optionnel : ajouter un paiement d'inscription initial
                montant_initial = serializer.validated_data.get('montant_inscription_initial')
                if montant_initial and montant_initial > 0:
                    PaiementInscription.objects.create(
                        membre=membre,
                        montant=montant_initial,
                        session=session_actuelle,
                        notes="Paiement initial lors de la création"
                    )
                    
                    # Vérifier si inscription complète
                    config = ConfigurationMutuelle.get_configuration()
                    if montant_initial >= config.montant_inscription:
                        membre.statut = 'EN_REGLE'
                        membre.save()
                
                return Response({
                    'message': 'Membre créé avec succès',
                    'utilisateur_id': str(utilisateur.id),
                    'membre_id': str(membre.id),
                    'numero_membre': membre.numero_membre,
                    'statut': membre.statut
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RapportsViewSet(viewsets.ViewSet):
    """
    ViewSet pour les rapports administrateur
    """
    permission_classes = [IsAdministrateur]
    
    @action(detail=False, methods=['get'])
    def rapport_financier_complet(self, request):
        """
        Rapport financier complet de la mutuelle
        """
        # Filtres optionnels
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        exercice_id = request.query_params.get('exercice_id')
        
        rapport = self._generer_rapport_financier(date_debut, date_fin, exercice_id)
        serializer = RapportFinancierSerializer(rapport)
        return Response(serializer.data)
    
    def _generer_rapport_financier(self, date_debut=None, date_fin=None, exercice_id=None):
        """Génère un rapport financier détaillé"""
        from datetime import datetime
        
        # Construire les filtres
        filters_base = Q()
        if date_debut:
            filters_base &= Q(date_creation__gte=datetime.fromisoformat(date_debut))
        if date_fin:
            filters_base &= Q(date_creation__lte=datetime.fromisoformat(date_fin))
        if exercice_id:
            # Adapter selon le modèle
            pass
        
        # Calculs des entrées
        total_inscriptions = PaiementInscription.objects.filter(filters_base).aggregate(
            total=Sum('montant'))['total'] or Decimal('0')
        
        total_solidarites = PaiementSolidarite.objects.filter(filters_base).aggregate(
            total=Sum('montant'))['total'] or Decimal('0')
        
        total_epargnes = EpargneTransaction.objects.filter(
            filters_base, type_transaction='DEPOT'
        ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
        
        total_remboursements = Remboursement.objects.filter(filters_base).aggregate(
            total=Sum('montant'))['total'] or Decimal('0')
        
        total_renflouements = PaiementRenflouement.objects.filter(filters_base).aggregate(
            total=Sum('montant'))['total'] or Decimal('0')
        
        # Calculs des sorties
        total_emprunts = Emprunt.objects.filter(filters_base).aggregate(
            total=Sum('montant_emprunte'))['total'] or Decimal('0')
        
        total_assistances = AssistanceAccordee.objects.filter(
            filters_base, statut='PAYEE'
        ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
        
        total_collations = Session.objects.filter(filters_base).aggregate(
            total=Sum('montant_collation'))['total'] or Decimal('0')
        
        # Situation actuelle
        fonds_social = FondsSocial.get_fonds_actuel()
        cumul_epargnes = sum(m.calculer_epargne_totale() for m in Membre.objects.all())
        
        entrees_totales = (
            total_inscriptions + total_solidarites + total_epargnes + 
            total_remboursements + total_renflouements
        )
        sorties_totales = total_emprunts + total_assistances + total_collations
        
        return {
            'periode': {
                'date_debut': date_debut,
                'date_fin': date_fin,
                'exercice_id': exercice_id
            },
            'entrees': {
                'inscriptions': total_inscriptions,
                'solidarites': total_solidarites,
                'epargnes': total_epargnes,
                'remboursements': total_remboursements,
                'renflouements': total_renflouements,
                'total': entrees_totales
            },
            'sorties': {
                'emprunts': total_emprunts,
                'assistances': total_assistances,
                'collations': total_collations,
                'total': sorties_totales
            },
            'bilan': {
                'solde_periode': entrees_totales - sorties_totales,
                'fonds_social_actuel': fonds_social.montant_total if fonds_social else Decimal('0'),
                'cumul_epargnes_actuel': cumul_epargnes,
                'liquidites_totales': (fonds_social.montant_total if fonds_social else Decimal('0')) + cumul_epargnes
            },
            'indicateurs': {
                'nombre_membres_total': Membre.objects.count(),
                'nombre_membres_en_regle': Membre.objects.filter(statut='EN_REGLE').count(),
                'nombre_emprunts_en_cours': Emprunt.objects.filter(statut='EN_COURS').count(),
                'taux_recouvrement_renflouements': self._calculer_taux_recouvrement()
            }
        }
    
    def _calculer_taux_recouvrement(self):
        """Calcule le taux de recouvrement des renflouements"""
        total_du = Renflouement.objects.aggregate(total=Sum('montant_du'))['total'] or Decimal('0')
        total_paye = Renflouement.objects.aggregate(total=Sum('montant_paye'))['total'] or Decimal('0')
        
        if total_du == 0:
            return 100
        return float((total_paye / total_du) * 100)
    
    
