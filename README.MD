# 📚 API Mutuelle Enseignants ENSPY - Documentation Complète

> **Documentation ultra-détaillée pour le développeur frontend**  
> Tout ce qu'il faut savoir pour intégrer l'API de la Mutuelle des Enseignants ENSPY

---

## 🎯 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture de l'API](#architecture-de-lapi)
3. [Authentification](#authentification)
4. [Endpoints par Module](#endpoints-par-module)
5. [Filtres et Recherche](#filtres-et-recherche)
6. [Modèles de Données](#modèles-de-données)
7. [Gestion des Erreurs](#gestion-des-erreurs)
8. [Exemples d'Utilisation](#exemples-dutilisation)
9. [Cas d'Usage Spécifiques](#cas-dusage-spécifiques)

---

## 🌟 Vue d'ensemble

L'API de la Mutuelle ENSPY est une API REST complète qui gère tous les aspects financiers d'une mutuelle d'enseignants :

- **💰 Gestion financière** : épargnes, emprunts, remboursements
- **👥 Gestion des membres** : inscriptions, statuts, données complètes
- **🤝 Solidarité** : paiements de solidarité, fonds social
- **🎁 Assistances** : demandes, validations, paiements
- **💸 Renflouements** : calculs automatiques, suivis des paiements
- **📊 Rapports** : statistiques complètes, tableaux de bord

### Base URL
```
http://localhost:8000/api/
```

### Format des Réponses
Toutes les réponses sont en JSON avec encodage UTF-8.

---

## 🏗️ Architecture de l'API

### Structure des URLs

```
/api/
├── auth/                    # Authentification et utilisateurs
├── token/                   # Gestion des tokens JWT
├── core/                    # Modèles de base (membres, exercices, sessions)
├── transactions/            # Toutes les transactions financières
└── administration/          # Dashboard et gestion admin
```

### Modules Principaux

| Module | Description | Accès |
|--------|-------------|-------|
| **authentication** | Utilisateurs, profils, auth | Public/Privé |
| **core** | Membres, exercices, sessions, config | Public |
| **transactions** | Paiements, emprunts, épargnes | Public |
| **administration** | Dashboard admin, rapports | Admin seulement |

---

## 🔐 Authentification

### Système d'Auth : JWT (JSON Web Tokens)

#### 1. Obtenir un Token

```http
POST /api/token/
Content-Type: application/json

{
  "email": "admin@enspy.com",
  "password": "motdepasse123"
}
```

**Réponse :**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### 2. Utiliser le Token

```http
GET /api/core/membres/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### 3. Rafraîchir le Token

```http
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### 4. Vérifier un Token

```http
POST /api/token/verify/
Content-Type: application/json

{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Permissions par Endpoint

| Type d'Endpoint | Permission | Description |
|------------------|------------|-------------|
| `GET` (lecture) | `AllowAny` | Accès libre à toutes les données |
| `POST/PUT/PATCH` données | `AllowAny` | Création/modification libre |
| Dashboard admin | `IsAdministrateur` | Admin seulement |
| Profil utilisateur | `IsOwnerOrAdmin` | Propriétaire ou admin |

---

## 📋 Endpoints par Module

### 🔑 Authentication

#### Utilisateurs

```http
GET    /api/auth/utilisateurs/           # Liste des utilisateurs (admin)
POST   /api/auth/utilisateurs/           # Créer un utilisateur
GET    /api/auth/utilisateurs/{id}/      # Détails d'un utilisateur
PUT    /api/auth/utilisateurs/{id}/      # Modifier un utilisateur
DELETE /api/auth/utilisateurs/{id}/      # Supprimer un utilisateur

# Actions spéciales
GET    /api/auth/utilisateurs/me/        # Mon profil
PATCH  /api/auth/utilisateurs/update_profile/  # Modifier mon profil
```

#### exemple :

```javascript

// 1. Se connecter
const login = async (email, password) => {
  const response = await fetch('/api/token/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  const { access, refresh } = await response.json();
  
  // 2. Récupérer les données utilisateur
  const userResponse = await fetch('/api/auth/utilisateurs/me/', {
    headers: { 'Authorization': `Bearer ${access}` }
  });
  
  const userData = await userResponse.json();
  
  // 3. Stocker tout
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
  localStorage.setItem('user_data', JSON.stringify(userData));
  
  return { access, refresh, user: userData };
};

```


#### Profil et Mot de Passe

```http
GET    /api/auth/profile/                # Mon profil complet
POST   /api/auth/change-password/        # Changer mot de passe
```

**Exemple - Créer un utilisateur :**
```json
POST /api/auth/utilisateurs/
{
  "username": "jean.dupont",
  "email": "jean.dupont@gmail.com",
  "first_name": "Jean",
  "last_name": "Dupont",
  "telephone": "+237690123456",
  "role": "MEMBRE",
  "password": "motdepasse123",
  "password_confirm": "motdepasse123",
  "photo_profil": null
}
```

---

### 🏢 Core (Modèles de Base)

#### Configuration de la Mutuelle

```http
GET    /api/core/configurations/         # Liste des configurations
GET    /api/core/configurations/current/ # Configuration actuelle
PUT    /api/core/configurations/{id}/    # Modifier config (admin)
```

**Réponse Configuration Actuelle :**
```json
{
  "id": "uuid",
  "montant_inscription": 150000,
  "montant_solidarite": 10000,
  "taux_interet": 3.0,
  "coefficient_emprunt_max": 5,
  "duree_exercice_mois": 12,
  "date_creation": "2024-01-01T00:00:00Z",
  "date_modification": "2024-06-02T21:34:56Z"
}
```

#### Exercices

```http
GET    /api/core/exercices/              # Liste des exercices
POST   /api/core/exercices/              # Créer exercice (admin)
GET    /api/core/exercices/{id}/         # Détails exercice
GET    /api/core/exercices/current/      # Exercice en cours
```

**Filtres Exercices :**
- `?nom=2024` - Par nom
- `?statut=EN_COURS` - Par statut
- `?is_current=true` - Exercice en cours
- `?year=2024` - Par année
- `?has_sessions=true` - Qui ont des sessions

#### Sessions

```http
GET    /api/core/sessions/               # Liste des sessions
POST   /api/core/sessions/               # Créer session (admin)
GET    /api/core/sessions/{id}/          # Détails session
GET    /api/core/sessions/current/       # Session en cours
```

**Filtres Sessions :**
- `?nom=janvier` - Par nom
- `?exercice={uuid}` - Par exercice
- `?statut=EN_COURS` - Par statut
- `?has_collation=true` - Avec collation
- `?this_month=true` - Ce mois
- `?date_session_after=2024-01-01` - Après date

#### Membres (⭐ LE PLUS IMPORTANT)

```http
GET    /api/core/membres/                # Liste des membres
POST   /api/core/membres/                # Créer membre
GET    /api/core/membres/{id}/           # Détails membre
GET    /api/core/membres/{id}/donnees_completes/  # 🔥 DONNÉES FINANCIÈRES COMPLÈTES
GET    /api/core/membres/statistiques/   # Stats globales membres
```

**🚨 SUPER IMPORTANT - Données Complètes d'un Membre :**

```json
GET /api/core/membres/{id}/donnees_completes/

{
  "membre_info": {
    "id": "uuid",
    "numero_membre": "ENS-0001",
    "nom_complet": "Jean Dupont",
    "email": "jean@gmail.com",
    "telephone": "+237690123456",
    "photo_profil_url": "http://localhost:8000/media/profiles/photo.jpg",
    "date_inscription": "2024-01-15",
    "statut": "EN_REGLE",
    "en_regle": true
  },
  "inscription": {
    "montant_total_inscription": 150000,
    "montant_paye_inscription": 150000,
    "montant_restant_inscription": 0,
    "inscription_complete": true,
    "pourcentage_inscription": 100
  },
  "solidarite": {
    "montant_solidarite_session_courante": 10000,
    "montant_paye_session_courante": 10000,
    "montant_restant_session_courante": 0,
    "solidarite_session_courante_complete": true,
    "total_solidarite_due": 60000,
    "total_solidarite_payee": 60000,
    "dette_solidarite_cumul": 0,
    "solidarite_a_jour": true
  },
  "epargne": {
    "epargne_base": 500000,
    "retraits_pour_prets": 200000,
    "interets_recus": 25000,
    "retours_remboursements": 0,
    "epargne_totale": 325000,
    "epargne_plus_interets": 325000,
    "montant_interets_separe": 25000
  },
  "emprunt": {
    "a_emprunt_en_cours": true,
    "montant_emprunt_en_cours": 200000,
    "montant_total_a_rembourser": 206000,
    "montant_deja_rembourse": 100000,
    "montant_restant_a_rembourser": 106000,
    "pourcentage_rembourse": 48.54,
    "montant_max_empruntable": 1625000,
    "nombre_emprunts_total": 3
  },
  "renflouement": {
    "total_renflouement_du": 15000,
    "total_renflouement_paye": 10000,
    "solde_renflouement_du": 5000,
    "renflouement_a_jour": false,
    "nombre_renflouements": 2
  },
  "resume_financier": {
    "patrimoine_total": 325000,
    "obligations_totales": 111000,
    "situation_nette": 119000
  }
}
```

**Filtres Membres Ultra-Complets :**
```http
# Filtres de base
?numero_membre=ENS-001
?nom_complet=jean
?email=jean
?statut=EN_REGLE

# Filtres financiers
?is_en_regle=true
?has_emprunts=true
?has_emprunts_en_cours=true
?has_renflouements_dus=true
?inscription_complete=true

# Filtres temporels
?inscrit_this_month=true
?inscrit_this_year=true
?month_inscription=6
?year_inscription=2024
?date_inscription_after=2024-01-01
```

#### Types d'Assistance

```http
GET    /api/core/types-assistance/       # Liste des types
POST   /api/core/types-assistance/       # Créer type (admin)
```

#### Fonds Social

```http
GET    /api/core/fonds-social/           # Historique fonds social
GET    /api/core/fonds-social/current/   # Fonds social actuel
```

**Réponse Fonds Social Actuel :**
```json
{
  "id": "uuid",
  "exercice": "uuid",
  "exercice_nom": "Exercice 2024",
  "montant_total": 2500000,
  "mouvements_recents": [
    {
      "type_mouvement": "ENTREE",
      "montant": 10000,
      "description": "Solidarité ENS-001 - Session Juin 2024",
      "date_mouvement": "2024-06-02T20:00:00Z"
    }
  ],
  "date_creation": "2024-01-01T00:00:00Z",
  "date_modification": "2024-06-02T21:30:00Z"
}
```

---

### 💰 Transactions

#### Paiements d'Inscription

```http
GET    /api/transactions/paiements-inscription/     # Liste
POST   /api/transactions/paiements-inscription/     # Créer paiement
GET    /api/transactions/paiements-inscription/{id}/ # Détails
```

**Filtres :**
```http
?membre={uuid}
?membre_numero=ENS-001
?membre_nom=jean
?session={uuid}
?montant_min=50000
?montant_max=150000
?today=true
?this_week=true
?this_month=true
?this_year=true
?year=2024
?month=6
```

#### Paiements de Solidarité

```http
GET    /api/transactions/paiements-solidarite/      # Liste
POST   /api/transactions/paiements-solidarite/      # Créer paiement
```

**Filtres :**
```http
?membre={uuid}
?session={uuid}
?session_en_cours=true
?this_month=true
```

#### Transactions d'Épargne

```http
GET    /api/transactions/epargne-transactions/      # Liste
POST   /api/transactions/epargne-transactions/      # Créer transaction
```

**Filtres Spéciaux :**
```http
?type_transaction=DEPOT
?type_depot=true
?type_retrait=true
?type_interet=true
?montant_positif=true
?montant_negatif=true
```

#### Emprunts (⭐ TRÈS IMPORTANT)

```http
GET    /api/transactions/emprunts/                  # Liste des emprunts
POST   /api/transactions/emprunts/                  # Créer emprunt
GET    /api/transactions/emprunts/{id}/             # Détails emprunt
GET    /api/transactions/emprunts/statistiques/     # Stats emprunts
```

**Filtres Emprunts Ultra-Avancés :**
```http
# Statuts
?statut=EN_COURS
?en_cours=true
?rembourse=true
?en_retard=true

# Montants
?montant_emprunte_min=100000
?montant_emprunte_max=1000000
?montant_total_min=200000
?taux_interet_min=2.5

# Pourcentages de remboursement
?pourcentage_rembourse_min=50
?pourcentage_rembourse_max=80
?presque_rembourse=true     # >80% remboursé
?peu_rembourse=true         # <20% remboursé

# Dates
?this_month=true
?this_year=true
?date_emprunt_after=2024-01-01
```

**Réponse Statistiques Emprunts :**
```json
GET /api/transactions/emprunts/statistiques/

{
  "nombre_emprunts": {
    "total": 45,
    "en_cours": 12,
    "rembourses": 30,
    "en_retard": 3
  },
  "montants": {
    "total_emprunte": 25000000,
    "total_a_rembourser": 25750000,
    "total_rembourse": 20000000,
    "solde_restant": 5750000
  },
  "pourcentages": {
    "taux_remboursement_global": 77.67
  }
}
```

#### Remboursements

```http
GET    /api/transactions/remboursements/            # Liste
POST   /api/transactions/remboursements/            # Créer remboursement
```

#### Assistances

```http
GET    /api/transactions/assistances/               # Liste
POST   /api/transactions/assistances/               # Demander assistance
PUT    /api/transactions/assistances/{id}/          # Modifier statut
```

**États d'une Assistance :**
- `DEMANDEE` → `APPROUVEE` → `PAYEE`
- `DEMANDEE` → `REJETEE`

#### Renflouements (⭐ CRUCIAL)

```http
GET    /api/transactions/renflouements/             # Liste
GET    /api/transactions/renflouements/statistiques/ # Stats renflouements
```

**Filtres Renflouements :**
```http
?type_cause=ASSISTANCE
?type_cause=COLLATION
?cause_assistance=true
?cause_collation=true
?solde=true                 # Soldés
?non_solde=true            # Non soldés
?partiellement_paye=true   # Partiellement payés
```

**Réponse Statistiques Renflouements :**
```json
{
  "nombre_renflouements": {
    "total": 125,
    "soldes": 80,
    "non_soldes": 45
  },
  "montants": {
    "total_du": 1250000,
    "total_paye": 950000,
    "montant_restant": 300000
  },
  "pourcentages": {
    "taux_recouvrement": 76.0,
    "taux_solde": 64.0
  }
}
```

#### Paiements de Renflouement

```http
GET    /api/transactions/paiements-renflouement/    # Liste
POST   /api/transactions/paiements-renflouement/    # Payer renflouement
```

---

### 👑 Administration (Admin Seulement)

#### Dashboard Complet

```http
GET    /api/administration/dashboard/dashboard_complet/
```

**🔥 RÉPONSE DASHBOARD COMPLET :**
```json
{
  "fonds_social": {
    "montant_total": 2500000,
    "exercice": "Exercice 2024",
    "derniere_modification": "2024-06-02T21:30:00Z"
  },
  "tresor": {
    "cumul_total_epargnes": 15000000,
    "nombre_membres": 120
  },
  "emprunts_en_cours": {
    "nombre": 12,
    "montant_total_attendu": 5750000
  },
  "situation_globale": {
    "liquidites_totales": 17500000,
    "engagements_totaux": 5750000
  },
  "derniers_paiements": {
    "inscriptions": [...],
    "solidarites": [...],
    "remboursements": [...]
  },
  "alertes": [
    {
      "type": "RETARD_RENFLOUEMENT",
      "message": "ENS-025 a 75,000 FCFA de retard",
      "priorite": "HAUTE",
      "membre_id": "uuid"
    }
  ],
  "activite_recente": {
    "nouveaux_membres": 3,
    "nouveaux_emprunts": 1,
    "assistances_demandees": 2,
    "total_paiements": 150000
  },
  "membres_problematiques": [...]
}
```

#### Gestion des Membres

```http
POST   /api/administration/gestion-membres/ajouter_paiement_inscription/
POST   /api/administration/gestion-membres/ajouter_paiement_solidarite/
# Création
POST /api/administration/gestion-membres/creer_membre_complet/

# Gestion transactions
POST /api/administration/gestion-membres/ajouter_paiement_inscription/
POST /api/administration/gestion-membres/ajouter_paiement_solidarite/
POST /api/administration/gestion-membres/ajouter_epargne/
POST /api/administration/gestion-membres/creer_emprunt/
POST /api/administration/gestion-membres/ajouter_remboursement/
POST   /api/administration/gestion-membres/ajouter_epargne/
POST   /api/administration/gestion-membres/creer_emprunt/
POST   /api/administration/gestion-membres/ajouter_remboursement/
```

**Exemple - Ajouter Paiement d'Inscription :**
```json
POST /api/administration/gestion-membres/ajouter_paiement_inscription/
{
  "membre_id": "uuid",
  "montant": 75000,
  "notes": "Paiement partiel inscription"
}

// Réponse
{
  "message": "Paiement inscription ajouté avec succès",
  "paiement_id": "uuid",
  "nouveau_statut": "EN_REGLE",
  "total_paye": 150000
}


```
### 5. Gestion Complète des Membres (Admin)

#### Créer un Membre Complet

L'admin peut créer un membre complet (utilisateur + membre + paiement initial optionnel) en une seule opération :

```http
POST /api/administration/gestion-membres/creer_membre_complet/
```

**Corps de la requête :**
```json
{
  "username": "marie.martin",
  "email": "marie.martin@gmail.com", 
  "first_name": "Marie",
  "last_name": "Martin",
  "telephone": "+237691234567",
  "password": "motdepasse123",
  "photo_profil": null,
  "date_inscription": "2024-06-02",
  "montant_inscription_initial": 75000
}
```

**Champs requis :**
- `username` : Nom d'utilisateur unique
- `email` : Email unique
- `first_name` : Prénom
- `last_name` : Nom de famille
- `telephone` : Numéro de téléphone

**Champs optionnels :**
- `password` : Mot de passe (défaut: "motdepasse123")
- `photo_profil` : Photo de profil (fichier image)
- `date_inscription` : Date d'inscription (défaut: aujourd'hui)
- `montant_inscription_initial` : Paiement d'inscription initial (défaut: 0)

**Réponse de succès (201) :**
```json
{
  "message": "Membre créé avec succès",
  "utilisateur_id": "uuid-utilisateur",
  "membre_id": "uuid-membre",
  "numero_membre": "ENS-0025",
  "statut": "NON_EN_REGLE"
}
```

**Logique automatique :**
1. **Création utilisateur** avec rôle "MEMBRE"
2. **Génération automatique** du numéro de membre (ENS-XXXX)
3. **Association** à l'exercice et session en cours
4. **Paiement initial** si montant > 0
5. **Statut automatique** : "EN_REGLE" si paiement >= montant inscription, sinon "NON_EN_REGLE"

**Erreurs possibles :**
```json
// Email déjà utilisé (400)
{
  "email": ["Un utilisateur avec cet email existe déjà"]
}

// Username déjà utilisé (400)  
{
  "username": ["Un utilisateur avec ce nom d'utilisateur existe déjà"]
}

// Aucun exercice en cours (400)
{
  "error": "Aucun exercice en cours pour l'inscription"
}

// Aucune session en cours (400)
{
  "error": "Aucune session en cours pour l'inscription"
}
```

#### Exemple d'utilisation JavaScript

```javascript
// Créer un nouveau membre complet
const creerMembreComplet = async (donneesNouveauMembre) => {
  try {
    const response = await fetch('/api/administration/gestion-membres/creer_membre_complet/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(donneesNouveauMembre)
    });
    
    if (!response.ok) {
      const errors = await response.json();
      
      // Gestion des erreurs de validation
      if (response.status === 400) {
        if (errors.email) {
          throw new Error('Cet email est déjà utilisé');
        }
        if (errors.username) {
          throw new Error('Ce nom d\'utilisateur est déjà pris');
        }
        if (errors.error) {
          throw new Error(errors.error);
        }
      }
      
      throw new Error('Erreur lors de la création du membre');
    }
    
    const resultat = await response.json();
    
    return {
      success: true,
      message: resultat.message,
      membre: {
        id: resultat.membre_id,
        numero: resultat.numero_membre,
        statut: resultat.statut
      }
    };
    
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

// Exemple d'usage
const nouveauMembre = {
  username: 'jean.doe',
  email: 'jean.doe@gmail.com',
  first_name: 'Jean',
  last_name: 'Doe',
  telephone: '+237690987654',
  password: 'motdepasse456',
  montant_inscription_initial: 100000
};

const resultat = await creerMembreComplet(nouveauMembre);

if (resultat.success) {
  console.log(`Membre créé: ${resultat.membre.numero} (${resultat.membre.statut})`);
  // Rafraîchir la liste des membres
  await chargerListeMembres();
} else {
  console.error('Erreur:', resultat.error);
  // Afficher l'erreur à l'utilisateur
  showError(resultat.error);
}
```

#### Formulaire de Création (React Native)

```javascript
const FormulaireNouveauMembre = ({ onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    telephone: '',
    password: 'motdepasse123',
    montant_inscription_initial: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  
  const handleSubmit = async () => {
    setLoading(true);
    setErrors({});
    
    try {
      // Validation côté client
      const newErrors = {};
      if (!formData.email) newErrors.email = 'Email requis';
      if (!formData.first_name) newErrors.first_name = 'Prénom requis';
      if (!formData.last_name) newErrors.last_name = 'Nom requis';
      if (!formData.telephone) newErrors.telephone = 'Téléphone requis';
      
      if (Object.keys(newErrors).length > 0) {
        setErrors(newErrors);
        setLoading(false);
        return;
      }
      
      // Générer username si pas fourni
      if (!formData.username) {
        formData.username = `${formData.first_name.toLowerCase()}.${formData.last_name.toLowerCase()}`;
      }
      
      const resultat = await creerMembreComplet(formData);
      
      if (resultat.success) {
        onSuccess(resultat.membre);
      } else {
        setErrors({ general: resultat.error });
      }
      
    } catch (error) {
      setErrors({ general: 'Erreur de connexion' });
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <View style={styles.form}>
      <Text style={styles.title}>Nouveau Membre</Text>
      
      {errors.general && (
        <Text style={styles.error}>{errors.general}</Text>
      )}
      
      <TextInput
        style={styles.input}
        placeholder="Email *"
        value={formData.email}
        onChangeText={(text) => setFormData({...formData, email: text})}
        keyboardType="email-address"
        autoCapitalize="none"
      />
      {errors.email && <Text style={styles.fieldError}>{errors.email}</Text>}
      
      <TextInput
        style={styles.input}
        placeholder="Prénom *"
        value={formData.first_name}
        onChangeText={(text) => setFormData({...formData, first_name: text})}
      />
      {errors.first_name && <Text style={styles.fieldError}>{errors.first_name}</Text>}
      
      <TextInput
        style={styles.input}
        placeholder="Nom *"
        value={formData.last_name}
        onChangeText={(text) => setFormData({...formData, last_name: text})}
      />
      {errors.last_name && <Text style={styles.fieldError}>{errors.last_name}</Text>}
      
      <TextInput
        style={styles.input}
        placeholder="Téléphone *"
        value={formData.telephone}
        onChangeText={(text) => setFormData({...formData, telephone: text})}
        keyboardType="phone-pad"
      />
      {errors.telephone && <Text style={styles.fieldError}>{errors.telephone}</Text>}
      
      <TextInput
        style={styles.input}
        placeholder="Nom d'utilisateur (optionnel)"
        value={formData.username}
        onChangeText={(text) => setFormData({...formData, username: text})}
        autoCapitalize="none"
      />
      
      <TextInput
        style={styles.input}
        placeholder="Mot de passe (défaut: motdepasse123)"
        value={formData.password}
        onChangeText={(text) => setFormData({...formData, password: text})}
        secureTextEntry
      />
      
      <TextInput
        style={styles.input}
        placeholder="Paiement initial (FCFA)"
        value={formData.montant_inscription_initial}
        onChangeText={(text) => setFormData({...formData, montant_inscription_initial: text})}
        keyboardType="numeric"
      />
      
      <View style={styles.buttons}>
        <TouchableOpacity 
          style={[styles.button, styles.cancelButton]} 
          onPress={onCancel}
        >
          <Text style={styles.cancelButtonText}>Annuler</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.button, styles.submitButton, loading && styles.disabled]} 
          onPress={handleSubmit}
          disabled={loading}
        >
          <Text style={styles.submitButtonText}>
            {loading ? 'Création...' : 'Créer Membre'}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};
```

#### Workflow Complet de Création

```javascript
// 1. Validation et création
const processusCreationMembre = async (donnees) => {
  console.log('🚀 Début création membre...');
  
  // Étape 1: Créer le membre
  const resultat = await creerMembreComplet(donnees);
  
  if (!resultat.success) {
    console.error('❌ Échec création:', resultat.error);
    return { success: false, error: resultat.error };
  }
  
  console.log('✅ Membre créé:', resultat.membre.numero);
  
  // Étape 2: Récupérer les données complètes
  const donneesCompletes = await fetch(`/api/core/membres/${resultat.membre.id}/donnees_completes/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }).then(r => r.json());
  
  // Étape 3: Notifier les autres admins (optionnel)
  await notifierCreationMembre(resultat.membre);
  
  // Étape 4: Logger l'action
  console.log(`✅ Nouveau membre ${resultat.membre.numero} créé par ${currentUser.username}`);
  
  return {
    success: true,
    membre: resultat.membre,
    donneesCompletes: donneesCompletes
  };
};
```

#### Routes Complètes Administration Membres

```http
# 🆕 Création complète
POST /api/administration/gestion-membres/creer_membre_complet/

# 💰 Gestion financière  
POST /api/administration/gestion-membres/ajouter_paiement_inscription/
POST /api/administration/gestion-membres/ajouter_paiement_solidarite/
POST /api/administration/gestion-membres/ajouter_epargne/
POST /api/administration/gestion-membres/creer_emprunt/
POST /api/administration/gestion-membres/ajouter_remboursement/
```

**Permissions :** Toutes ces routes nécessitent le rôle `ADMINISTRATEUR`.

#### Rapports

```http
GET    /api/administration/rapports/rapport_financier_complet/
```

**Paramètres Rapport :**
```http
?date_debut=2024-01-01
?date_fin=2024-06-30
?exercice_id=uuid
```

---

## 🔍 Filtres et Recherche

### Système de Filtres Global

Tous les endpoints supportent :

#### 1. Filtres Django Standard
```http
?field=value                    # Égalité exacte
?field__icontains=value        # Contient (insensible à la casse)
?field__gte=value              # Supérieur ou égal
?field__lte=value              # Inférieur ou égal
?field__year=2024              # Année spécifique
?field__month=6                # Mois spécifique
```

#### 2. Filtres de Plage
```http
?field_min=100&field_max=500   # Entre 100 et 500
?date_after=2024-01-01         # Après date
?date_before=2024-12-31        # Avant date
```

#### 3. Filtres Booléens
```http
?has_field=true                # A une valeur
?is_active=true                # Champ booléen
?this_month=true               # Ce mois
?this_year=true                # Cette année
```

#### 4. Recherche Textuelle
```http
?search=jean                   # Recherche dans tous les champs définis
```

#### 5. Tri
```http
?ordering=date_creation        # Tri croissant
?ordering=-date_creation       # Tri décroissant
?ordering=nom,date_creation    # Tri multiple
```

#### 6. Pagination
```http
?page=2                        # Page 2
?page_size=50                  # 50 éléments par page
```

### Exemples de Requêtes Complexes

```http
# Membres inscrits cette année, en règle, avec emprunts
GET /api/core/membres/?inscrit_this_year=true&is_en_regle=true&has_emprunts=true

# Emprunts de plus de 500k, remboursés à moins de 30%
GET /api/transactions/emprunts/?montant_emprunte_min=500000&pourcentage_rembourse_max=30

# Paiements de solidarité de ce mois pour session en cours
GET /api/transactions/paiements-solidarite/?this_month=true&session_en_cours=true

# Renflouements non soldés pour assistances
GET /api/transactions/renflouements/?non_solde=true&cause_assistance=true
```

---

## 📊 Modèles de Données

### Utilisateur

```json
{
  "id": "uuid",
  "username": "jean.dupont",
  "email": "jean@gmail.com",
  "first_name": "Jean",
  "last_name": "Dupont",
  "telephone": "+237690123456",
  "role": "MEMBRE|ADMINISTRATEUR",
  "photo_profil": "url",
  "photo_profil_url": "url_complete",
  "nom_complet": "Jean Dupont",
  "is_membre": true,
  "is_administrateur": false,
  "date_creation": "datetime",
  "date_modification": "datetime",
  "is_active": true
}
```

### Membre

```json
{
  "id": "uuid",
  "utilisateur": { /* Utilisateur complet */ },
  "numero_membre": "ENS-0001",
  "date_inscription": "date",
  "statut": "EN_REGLE|NON_EN_REGLE|SUSPENDU",
  "exercice_inscription": "uuid",
  "exercice_inscription_nom": "Exercice 2024",
  "session_inscription": "uuid",
  "session_inscription_nom": "Session Janvier 2024",
  "is_en_regle": true,
  "donnees_financieres": { /* Toutes les données calculées */ }
}
```

### Emprunt

```json
{
  "id": "uuid",
  "membre": "uuid",
  "membre_info": { /* Info membre */ },
  "montant_emprunte": 500000,
  "taux_interet": 3.0,
  "montant_total_a_rembourser": 515000,
  "montant_rembourse": 250000,
  "montant_restant_a_rembourser": 265000,
  "montant_interets": 15000,
  "pourcentage_rembourse": 48.54,
  "session_emprunt": "uuid",
  "session_nom": "Session Mars 2024",
  "date_emprunt": "datetime",
  "statut": "EN_COURS|REMBOURSE|EN_RETARD",
  "statut_display": "En cours",
  "notes": "string",
  "remboursements_details": [ /* Liste des remboursements */ ]
}
```

### Renflouement

```json
{
  "id": "uuid",
  "membre": "uuid",
  "membre_info": { /* Info membre */ },
  "session": "uuid",
  "session_nom": "Session Juin 2024",
  "montant_du": 15000,
  "montant_paye": 10000,
  "montant_restant": 5000,
  "is_solde": false,
  "pourcentage_paye": 66.67,
  "cause": "Assistance Décès pour ENS-042",
  "type_cause": "ASSISTANCE|COLLATION|AUTRE",
  "type_cause_display": "Assistance",
  "date_creation": "datetime",
  "paiements_details": [ /* Liste des paiements */ ]
}
```

---

## 🚨 Gestion des Erreurs

### Codes de Statut HTTP

| Code | Signification | Usage |
|------|---------------|-------|
| `200` | OK | Succès |
| `201` | Created | Création réussie |
| `400` | Bad Request | Données invalides |
| `401` | Unauthorized | Token manquant/invalide |
| `403` | Forbidden | Pas les permissions |
| `404` | Not Found | Ressource introuvable |
| `500` | Server Error | Erreur serveur |

### Format des Erreurs

```json
// Erreur de validation
{
  "field_name": [
    "Ce champ est requis."
  ],
  "montant": [
    "Assurez-vous que cette valeur est supérieure ou égale à 0."
  ]
}

// Erreur générale
{
  "detail": "Token invalide ou expiré."
}

// Erreur métier
{
  "error": "Vous avez déjà un emprunt en cours"
}
```

## 📝 Notes Importantes

### 1. Permissions
- **La plupart des endpoints sont en `AllowAny`** comme spécifié
- Seuls les endpoints d'administration nécessitent le rôle `ADMINISTRATEUR`
- L'authentification JWT est optionnelle pour la lecture

### 2. Calculs Automatiques
- **Tous les calculs financiers sont faits côté backend**
- Les données de renflouement se mettent à jour automatiquement
- Le fonds social est géré automatiquement
- Les intérêts sont redistributés automatiquement

### 3. Performance
- **Utilisation de `select_related` et `prefetch_related`** pour optimiser les requêtes
- Pagination automatique sur tous les endpoints
- Filtres indexés pour de meilleures performances

### 4. Données en Temps Réel
- **Le dashboard admin** se met à jour en temps réel
- **Les statistiques** sont calculées à la demande
- **Les alertes** sont générées automatiquement

### 5. Extensibilité
- **Filtres ultra-complets** pour toutes les recherches possibles
- **Actions personnalisées** sur les ViewSets
- **Serializers avec données calculées** pour éviter les appels multiples

---


Cette API vous donne **TOUT** ce qu'il faut pour créer une application mobile complète de gestion de mutuelle ! 

**Points forts :**
- ✅ **Données calculées automatiquement** - pas de calculs côté frontend
- ✅ **Filtres ultra-complets** - recherche sur tout et n'importe quoi
- ✅ **Permissions flexibles** - accès libre selon vos specs
- ✅ **Administration complète** - dashboard avec tout ce qu'il faut
- ✅ **Gestion financière automatique** - fonds social, renflouements, intérêts
- ✅ **Documentation exhaustive** - tous les détails sont là !

**Besoin d'aide ?** Tous les exemples de code sont prêts à utiliser ! 🚀

---

**Développé avec ❤️ pour la Mutuelle des Enseignants ENSPY**  
*Date de dernière mise à jour : 2 Juin 2024*