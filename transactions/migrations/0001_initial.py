# Generated by Django 5.1.1 on 2025-06-02 22:03

import django.core.validators
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssistanceAccordee",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "montant",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        verbose_name="Montant accordé (FCFA)",
                    ),
                ),
                (
                    "date_demande",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Date de demande"
                    ),
                ),
                (
                    "date_paiement",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Date de paiement"
                    ),
                ),
                (
                    "statut",
                    models.CharField(
                        choices=[
                            ("DEMANDEE", "Demandée"),
                            ("APPROUVEE", "Approuvée"),
                            ("PAYEE", "Payée"),
                            ("REJETEE", "Rejetée"),
                        ],
                        default="DEMANDEE",
                        max_length=15,
                        verbose_name="Statut",
                    ),
                ),
                ("justification", models.TextField(verbose_name="Justification")),
                (
                    "notes",
                    models.TextField(blank=True, verbose_name="Notes administratives"),
                ),
                (
                    "membre",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assistances_recues",
                        to="core.membre",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assistances_accordees",
                        to="core.session",
                    ),
                ),
                (
                    "type_assistance",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assistances_accordees",
                        to="core.typeassistance",
                    ),
                ),
            ],
            options={
                "verbose_name": "Assistance accordée",
                "verbose_name_plural": "Assistances accordées",
                "ordering": ["-date_demande"],
            },
        ),
        migrations.CreateModel(
            name="Emprunt",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "montant_emprunte",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Montant emprunté (FCFA)",
                    ),
                ),
                (
                    "taux_interet",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=5,
                        verbose_name="Taux d'intérêt (%)",
                    ),
                ),
                (
                    "montant_total_a_rembourser",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        verbose_name="Montant total à rembourser (FCFA)",
                    ),
                ),
                (
                    "montant_rembourse",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="Montant déjà remboursé (FCFA)",
                    ),
                ),
                (
                    "date_emprunt",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Date d'emprunt"
                    ),
                ),
                (
                    "statut",
                    models.CharField(
                        choices=[
                            ("EN_COURS", "En cours"),
                            ("REMBOURSE", "Remboursé"),
                            ("EN_RETARD", "En retard"),
                        ],
                        default="EN_COURS",
                        max_length=15,
                        verbose_name="Statut",
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Notes")),
                (
                    "membre",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="emprunts",
                        to="core.membre",
                    ),
                ),
                (
                    "session_emprunt",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="emprunts",
                        to="core.session",
                    ),
                ),
            ],
            options={
                "verbose_name": "Emprunt",
                "verbose_name_plural": "Emprunts",
                "ordering": ["-date_emprunt"],
            },
        ),
        migrations.CreateModel(
            name="EpargneTransaction",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "type_transaction",
                    models.CharField(
                        choices=[
                            ("DEPOT", "Dépôt"),
                            ("RETRAIT_PRET", "Retrait pour prêt"),
                            ("AJOUT_INTERET", "Ajout d'intérêt"),
                            ("RETOUR_REMBOURSEMENT", "Retour de remboursement"),
                        ],
                        max_length=20,
                        verbose_name="Type de transaction",
                    ),
                ),
                (
                    "montant",
                    models.DecimalField(
                        decimal_places=2, max_digits=12, verbose_name="Montant (FCFA)"
                    ),
                ),
                (
                    "date_transaction",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Date de transaction"
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Notes")),
                (
                    "membre",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transactions_epargne",
                        to="core.membre",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transactions_epargne",
                        to="core.session",
                    ),
                ),
            ],
            options={
                "verbose_name": "Transaction d'épargne",
                "verbose_name_plural": "Transactions d'épargne",
                "ordering": ["-date_transaction"],
            },
        ),
        migrations.CreateModel(
            name="PaiementInscription",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "montant",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Montant payé (FCFA)",
                    ),
                ),
                (
                    "date_paiement",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Date de paiement"
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Notes")),
                (
                    "membre",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="paiements_inscription",
                        to="core.membre",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="paiements_inscription",
                        to="core.session",
                        verbose_name="Session",
                    ),
                ),
            ],
            options={
                "verbose_name": "Paiement d'inscription",
                "verbose_name_plural": "Paiements d'inscription",
                "ordering": ["-date_paiement"],
            },
        ),
        migrations.CreateModel(
            name="Remboursement",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "montant",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Montant remboursé (FCFA)",
                    ),
                ),
                (
                    "date_remboursement",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Date de remboursement"
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Notes")),
                (
                    "montant_capital",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="Part capital du remboursement",
                    ),
                ),
                (
                    "montant_interet",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="Part intérêt du remboursement",
                    ),
                ),
                (
                    "emprunt",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="remboursements",
                        to="transactions.emprunt",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="remboursements",
                        to="core.session",
                    ),
                ),
            ],
            options={
                "verbose_name": "Remboursement",
                "verbose_name_plural": "Remboursements",
                "ordering": ["-date_remboursement"],
            },
        ),
        migrations.CreateModel(
            name="Renflouement",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "montant_du",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Montant dû (FCFA)",
                    ),
                ),
                (
                    "montant_paye",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Montant payé (FCFA)",
                    ),
                ),
                (
                    "cause",
                    models.TextField(blank=True, verbose_name="Cause du renflouement"),
                ),
                (
                    "type_cause",
                    models.CharField(
                        choices=[
                            ("ASSISTANCE", "Assistance"),
                            ("COLLATION", "Collation"),
                            ("AUTRE", "Autre"),
                        ],
                        max_length=15,
                        verbose_name="Type de cause",
                    ),
                ),
                (
                    "date_creation",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Date de création"
                    ),
                ),
                ("date_derniere_modification", models.DateTimeField(auto_now=True)),
                (
                    "membre",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="renflouements",
                        to="core.membre",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="renflouements",
                        to="core.session",
                    ),
                ),
            ],
            options={
                "verbose_name": "Renflouement",
                "verbose_name_plural": "Renflouements",
                "ordering": ["-date_creation"],
            },
        ),
        migrations.CreateModel(
            name="PaiementRenflouement",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "montant",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Montant payé (FCFA)",
                    ),
                ),
                (
                    "date_paiement",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Date de paiement"
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Notes")),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="paiements_renflouement",
                        to="core.session",
                    ),
                ),
                (
                    "renflouement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="paiements",
                        to="transactions.renflouement",
                    ),
                ),
            ],
            options={
                "verbose_name": "Paiement de renflouement",
                "verbose_name_plural": "Paiements de renflouement",
                "ordering": ["-date_paiement"],
            },
        ),
        migrations.CreateModel(
            name="PaiementSolidarite",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "montant",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Montant payé (FCFA)",
                    ),
                ),
                (
                    "date_paiement",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Date de paiement"
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Notes")),
                (
                    "membre",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="paiements_solidarite",
                        to="core.membre",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="paiements_solidarite",
                        to="core.session",
                    ),
                ),
            ],
            options={
                "verbose_name": "Paiement de solidarité",
                "verbose_name_plural": "Paiements de solidarité",
                "ordering": ["-date_paiement"],
                "unique_together": {("membre", "session")},
            },
        ),
    ]
