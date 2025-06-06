from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from .models import (
    PaiementInscription, PaiementSolidarite, EpargneTransaction,
    Emprunt, Remboursement, AssistanceAccordee, Renflouement,
    PaiementRenflouement
)

@admin.register(PaiementInscription)
class PaiementInscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'membre_numero', 'membre_nom', 'montant_formate', 
        'session_nom', 'date_paiement', 'progression_inscription'
    )
    list_filter = ('session', 'date_paiement')
    search_fields = (
        'membre__numero_membre', 'membre__utilisateur__first_name',
        'membre__utilisateur__last_name', 'notes'
    )
    date_hierarchy = 'date_paiement'
    readonly_fields = ('date_paiement',)
    
    def membre_numero(self, obj):
        return obj.membre.numero_membre
    membre_numero.short_description = 'Numéro Membre'
    
    def membre_nom(self, obj):
        return obj.membre.utilisateur.nom_complet
    membre_nom.short_description = 'Nom'
    
    def montant_formate(self, obj):
        return f"{obj.montant:,.0f} FCFA"
    montant_formate.short_description = 'Montant'
    
    def session_nom(self, obj):
        return obj.session.nom
    session_nom.short_description = 'Session'
    
    def progression_inscription(self, obj):
        from core.models import ConfigurationMutuelle
        config = ConfigurationMutuelle.get_configuration()
        total_paye = PaiementInscription.objects.filter(
            membre=obj.membre
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        pourcentage = (total_paye / config.montant_inscription * 100) if config.montant_inscription > 0 else 0
        
        if pourcentage >= 100:
            color = 'green'
            status = 'Complète'
        elif pourcentage >= 50:
            color = 'orange'
            status = f'{pourcentage:.0f}%'
        else:
            color = 'red'
            status = f'{pourcentage:.0f}%'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    progression_inscription.short_description = 'Progression'

@admin.register(PaiementSolidarite)
class PaiementSolidariteAdmin(admin.ModelAdmin):
    list_display = (
        'membre_numero', 'membre_nom', 'montant_formate',
        'session_nom', 'exercice_nom', 'date_paiement'
    )
    list_filter = ('session__exercice', 'session', 'date_paiement')
    search_fields = (
        'membre__numero_membre', 'membre__utilisateur__first_name',
        'membre__utilisateur__last_name'
    )
    date_hierarchy = 'date_paiement'
    readonly_fields = ('date_paiement',)
    
    def membre_numero(self, obj):
        return obj.membre.numero_membre
    membre_numero.short_description = 'Numéro Membre'
    
    def membre_nom(self, obj):
        return obj.membre.utilisateur.nom_complet
    membre_nom.short_description = 'Nom'
    
    def montant_formate(self, obj):
        return f"{obj.montant:,.0f} FCFA"
    montant_formate.short_description = 'Montant'
    
    def session_nom(self, obj):
        return obj.session.nom
    session_nom.short_description = 'Session'
    
    def exercice_nom(self, obj):
        return obj.session.exercice.nom
    exercice_nom.short_description = 'Exercice'

@admin.register(EpargneTransaction)
class EpargneTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'membre_numero', 'membre_nom', 'type_transaction_formate',
        'montant_formate', 'session_nom', 'date_transaction'
    )
    list_filter = ('type_transaction', 'session', 'date_transaction')
    search_fields = (
        'membre__numero_membre', 'membre__utilisateur__first_name',
        'notes'
    )
    date_hierarchy = 'date_transaction'
    readonly_fields = ('date_transaction',)
    
    def membre_numero(self, obj):
        return obj.membre.numero_membre
    membre_numero.short_description = 'Numéro Membre'
    
    def membre_nom(self, obj):
        return obj.membre.utilisateur.nom_complet
    membre_nom.short_description = 'Nom'
    
    def type_transaction_formate(self, obj):
        colors = {
            'DEPOT': 'green',
            'RETRAIT_PRET': 'red',
            'AJOUT_INTERET': 'blue',
            'RETOUR_REMBOURSEMENT': 'orange'
        }
        color = colors.get(obj.type_transaction, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_type_transaction_display()
        )
    type_transaction_formate.short_description = 'Type'
    
    def montant_formate(self, obj):
        if obj.montant >= 0:
            return format_html(
                '<span style="color: green;">+{:,.0f} FCFA</span>',
                obj.montant
            )
        else:
            return format_html(
                '<span style="color: red;">{:,.0f} FCFA</span>',
                obj.montant
            )
    montant_formate.short_description = 'Montant'
    
    def session_nom(self, obj):
        return obj.session.nom
    session_nom.short_description = 'Session'

@admin.register(Emprunt)
class EmpruntAdmin(admin.ModelAdmin):
    list_display = (
        'membre_numero', 'membre_nom', 'montant_emprunte_formate',
        'montant_total_formate', 'montant_rembourse_formate', 
        'statut_formate', 'progression', 'date_emprunt'
    )
    list_filter = ('statut', 'taux_interet', 'session_emprunt', 'date_emprunt')
    search_fields = (
        'membre__numero_membre', 'membre__utilisateur__first_name',
        'membre__utilisateur__last_name', 'notes'
    )
    date_hierarchy = 'date_emprunt'
    readonly_fields = ('date_emprunt', 'montant_total_a_rembourser', 'pourcentage_rembourse')
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('membre', 'montant_emprunte', 'taux_interet', 'session_emprunt')
        }),
        ('Calculs automatiques', {
            'fields': ('montant_total_a_rembourser', 'montant_rembourse', 'statut'),
            'classes': ('collapse',)
        }),
        ('Suivi', {
            'fields': ('pourcentage_rembourse', 'date_emprunt', 'notes')
        })
    )
    
    def membre_numero(self, obj):
        return obj.membre.numero_membre
    membre_numero.short_description = 'Numéro'
    
    def membre_nom(self, obj):
        return obj.membre.utilisateur.nom_complet
    membre_nom.short_description = 'Nom'
    
    def montant_emprunte_formate(self, obj):
        return f"{obj.montant_emprunte:,.0f} FCFA"
    montant_emprunte_formate.short_description = 'Emprunté'
    
    def montant_total_formate(self, obj):
        return f"{obj.montant_total_a_rembourser:,.0f} FCFA"
    montant_total_formate.short_description = 'À rembourser'
    
    def montant_rembourse_formate(self, obj):
        return f"{obj.montant_rembourse:,.0f} FCFA"
    montant_rembourse_formate.short_description = 'Remboursé'
    
    def statut_formate(self, obj):
        colors = {
            'EN_COURS': 'orange',
            'REMBOURSE': 'green',
            'EN_RETARD': 'red'
        }
        color = colors.get(obj.statut, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_statut_display()
        )
    statut_formate.short_description = 'Statut'
    
    def progression(self, obj):
        pourcentage = obj.pourcentage_rembourse
        if pourcentage >= 100:
            color = 'green'
        elif pourcentage >= 50:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{}%</div></div>',
            min(pourcentage, 100), color, pourcentage
        )
    progression.short_description = 'Progression'

@admin.register(Remboursement)
class RemboursementAdmin(admin.ModelAdmin):
    list_display = (
        'emprunt_info', 'montant_formate', 'montant_capital_formate',
        'montant_interet_formate', 'session_nom', 'date_remboursement'
    )
    list_filter = ('session', 'date_remboursement')
    search_fields = (
        'emprunt__membre__numero_membre', 
        'emprunt__membre__utilisateur__first_name',
        'notes'
    )
    date_hierarchy = 'date_remboursement'
    readonly_fields = ('date_remboursement', 'montant_capital', 'montant_interet')
    
    def emprunt_info(self, obj):
        return f"{obj.emprunt.membre.numero_membre} - {obj.emprunt.montant_emprunte:,.0f} FCFA"
    emprunt_info.short_description = 'Emprunt'
    
    def montant_formate(self, obj):
        return f"{obj.montant:,.0f} FCFA"
    montant_formate.short_description = 'Montant total'
    
    def montant_capital_formate(self, obj):
        return f"{obj.montant_capital:,.0f} FCFA"
    montant_capital_formate.short_description = 'Capital'
    
    def montant_interet_formate(self, obj):
        return format_html(
            '<span style="color: blue;">{:,.0f} FCFA</span>',
            obj.montant_interet
        )
    montant_interet_formate.short_description = 'Intérêt'
    
    def session_nom(self, obj):
        return obj.session.nom
    session_nom.short_description = 'Session'

@admin.register(AssistanceAccordee)
class AssistanceAccordeeAdmin(admin.ModelAdmin):
    list_display = (
        'membre_numero', 'membre_nom', 'type_assistance_nom',
        'montant_formate', 'statut_formate', 'date_demande', 'date_paiement'
    )
    list_filter = ('type_assistance', 'statut', 'session', 'date_demande')
    search_fields = (
        'membre__numero_membre', 'membre__utilisateur__first_name',
        'justification', 'notes'
    )
    date_hierarchy = 'date_demande'
    readonly_fields = ('date_demande', 'date_paiement')
    
    fieldsets = (
        ('Demande', {
            'fields': ('membre', 'type_assistance', 'justification', 'session')
        }),
        ('Traitement', {
            'fields': ('statut', 'montant', 'date_paiement', 'notes')
        }),
        ('Historique', {
            'fields': ('date_demande',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['approuver_assistances', 'rejeter_assistances', 'marquer_payees']
    
    def membre_numero(self, obj):
        return obj.membre.numero_membre
    membre_numero.short_description = 'Numéro'
    
    def membre_nom(self, obj):
        return obj.membre.utilisateur.nom_complet
    membre_nom.short_description = 'Nom'
    
    def type_assistance_nom(self, obj):
        return obj.type_assistance.nom
    type_assistance_nom.short_description = 'Type'
    
    def montant_formate(self, obj):
        return f"{obj.montant:,.0f} FCFA"
    montant_formate.short_description = 'Montant'
    
    def statut_formate(self, obj):
        colors = {
            'DEMANDEE': 'blue',
            'APPROUVEE': 'orange',
            'PAYEE': 'green',
            'REJETEE': 'red'
        }
        color = colors.get(obj.statut, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_statut_display()
        )
    statut_formate.short_description = 'Statut'
    
    def approuver_assistances(self, request, queryset):
        queryset.update(statut='APPROUVEE')
        self.message_user(request, f"{queryset.count()} assistances approuvées.")
    approuver_assistances.short_description = "Approuver les assistances sélectionnées"
    
    def rejeter_assistances(self, request, queryset):
        queryset.update(statut='REJETEE')
        self.message_user(request, f"{queryset.count()} assistances rejetées.")
    rejeter_assistances.short_description = "Rejeter les assistances sélectionnées"
    
    def marquer_payees(self, request, queryset):
        from django.utils import timezone
        queryset.update(statut='PAYEE', date_paiement=timezone.now())
        self.message_user(request, f"{queryset.count()} assistances marquées comme payées.")
    marquer_payees.short_description = "Marquer comme payées"

@admin.register(Renflouement)
class RenflouementAdmin(admin.ModelAdmin):
    list_display = (
        'membre_numero', 'membre_nom', 'montant_du_formate',
        'montant_paye_formate', 'montant_restant_formate',
        'type_cause', 'progression_paiement', 'date_creation'
    )
    list_filter = ('type_cause', 'session', 'date_creation')
    search_fields = (
        'membre__numero_membre', 'membre__utilisateur__first_name',
        'cause'
    )
    date_hierarchy = 'date_creation'
    readonly_fields = ('date_creation', 'date_derniere_modification', 'montant_restant', 'pourcentage_paye')
    
    def membre_numero(self, obj):
        return obj.membre.numero_membre
    membre_numero.short_description = 'Numéro'
    
    def membre_nom(self, obj):
        return obj.membre.utilisateur.nom_complet
    membre_nom.short_description = 'Nom'
    
    def montant_du_formate(self, obj):
        return f"{obj.montant_du:,.0f} FCFA"
    montant_du_formate.short_description = 'Dû'
    
    def montant_paye_formate(self, obj):
        return f"{obj.montant_paye:,.0f} FCFA"
    montant_paye_formate.short_description = 'Payé'
    
    def montant_restant_formate(self, obj):
        restant = obj.montant_restant
        if restant > 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{:,.0f} FCFA</span>',
                restant
            )
        else:
            return format_html(
                '<span style="color: green;">Soldé</span>'
            )
    montant_restant_formate.short_description = 'Restant'
    
    def progression_paiement(self, obj):
        pourcentage = obj.pourcentage_paye
        if pourcentage >= 100:
            color = 'green'
            text = 'Soldé'
        elif pourcentage >= 50:
            color = 'orange'
            text = f'{pourcentage:.0f}%'
        else:
            color = 'red'
            text = f'{pourcentage:.0f}%'
        
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{}</div></div>',
            min(pourcentage, 100), color, text
        )
    progression_paiement.short_description = 'Progression'

@admin.register(PaiementRenflouement)
class PaiementRenflouementAdmin(admin.ModelAdmin):
    list_display = (
        'renflouement_info', 'montant_formate', 'session_nom', 'date_paiement'
    )
    list_filter = ('session', 'date_paiement')
    search_fields = (
        'renflouement__membre__numero_membre',
        'renflouement__membre__utilisateur__first_name',
        'notes'
    )
    date_hierarchy = 'date_paiement'
    readonly_fields = ('date_paiement',)
    
    def renflouement_info(self, obj):
        return f"{obj.renflouement.membre.numero_membre} - {obj.renflouement.cause[:30]}..."
    renflouement_info.short_description = 'Renflouement'
    
    def montant_formate(self, obj):
        return f"{obj.montant:,.0f} FCFA"
    montant_formate.short_description = 'Montant'
    
    def session_nom(self, obj):
        return obj.session.nom
    session_nom.short_description = 'Session'

# Configuration de l'admin site
admin.site.site_header = "Administration Mutuelle Enseignants ENSPY"
admin.site.site_title = "Mutuelle ENSPY Admin"
admin.site.index_title = "Tableau de bord administrateur"