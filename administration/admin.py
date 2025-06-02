# Administration n'a pas de modèles propres, donc pas d'admin.py nécessaire
# Tous les modèles sont dans core et transactions
# Ce fichier peut être supprimé ou laissé vide

# Si on veut des actions administratives personnalisées dans l'admin Django :
from django.contrib import admin
from core.models import Membre, FondsSocial
from transactions.models import Emprunt, Renflouement

# Actions personnalisées pour l'admin Django
def marquer_membres_en_regle(modeladmin, request, queryset):
    queryset.update(statut='EN_REGLE')
marquer_membres_en_regle.short_description = "Marquer les membres sélectionnés comme en règle"

def marquer_membres_non_en_regle(modeladmin, request, queryset):
    queryset.update(statut='NON_EN_REGLE')
marquer_membres_non_en_regle.short_description = "Marquer les membres sélectionnés comme non en règle"

def marquer_emprunts_en_retard(modeladmin, request, queryset):
    queryset.update(statut='EN_RETARD')
marquer_emprunts_en_retard.short_description = "Marquer les emprunts sélectionnés en retard"

# On peut ajouter ces actions aux admins existants si nécessaire