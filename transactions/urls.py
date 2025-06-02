from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'paiements-inscription', views.PaiementInscriptionViewSet)
router.register(r'paiements-solidarite', views.PaiementSolidariteViewSet)
router.register(r'epargne-transactions', views.EpargneTransactionViewSet)
router.register(r'emprunts', views.EmpruntViewSet)
router.register(r'remboursements', views.RemboursementViewSet)
router.register(r'assistances', views.AssistanceAccordeeViewSet)
router.register(r'renflouements', views.RenflouementViewSet)
router.register(r'paiements-renflouement', views.PaiementRenflouementViewSet)

urlpatterns = [
    path('', include(router.urls)),
]