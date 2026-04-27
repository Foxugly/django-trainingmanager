# trainingmanager-server

Backend API REST pour TrainingManager — application de planification d'entraînements sportifs.

## Stack

- Python 3.12+ (testé sur 3.14)
- Django 6.0
- Django REST Framework + drf-spectacular (OpenAPI)
- JWT auth (djangorestframework-simplejwt)
- django-allauth (signup + email verification + headless mode)
- Anthropic API (Claude Haiku 4.5 par défaut)
- SQLite en dev, PostgreSQL recommandé en prod
- Email backend : Microsoft Graph API
- pytest, factory-boy, ruff, black, pre-commit

## Setup local

### Prérequis

- Python 3.12+
- gettext (pour i18n) — sur Windows : https://mlocati.github.io/articles/gettext-iconv-windows.html ou `choco install gettext`
- Une API key Anthropic (https://console.anthropic.com/)
- Un app registration Azure AD pour Microsoft Graph (envoi d'emails)

### Installation

```bash
git clone https://github.com/Foxugly/django-trainingmanager
cd django-trainingmanager
python -m venv .venv
source .venv/bin/activate    # Linux/Mac
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
# Éditer .env : remplir SECRET_KEY, ANTHROPIC_API_KEY, GRAPH_*, FRONTEND_URL
python manage.py migrate
python manage.py loaddata db.json   # fixture de seed
python manage.py runserver
```

Doc Swagger UI : http://localhost:8000/api/v1/docs/

### Pre-commit hooks

```bash
pip install pre-commit
pre-commit install
```

Ruff (lint+format) et Black tournent à chaque commit.

## Variables d'environnement

Voir `.env.example`. Critiques :

| Variable | Description |
|---|---|
| `SECRET_KEY` | Clé Django, à régénérer |
| `DEBUG` | `True` en dev, `False` en prod |
| `DATABASE_URL` | Connexion DB (par défaut SQLite) |
| `FRONTEND_URL` | URL du frontend (utilisée dans les emails) |
| `ANTHROPIC_API_KEY` | Clé Anthropic pour les endpoints IA |
| `ANTHROPIC_MODEL_DEFAULT` | Default : `claude-haiku-4-5-20251001` |
| `GRAPH_TENANT_ID` | Tenant Azure AD |
| `GRAPH_CLIENT_ID` | App ID |
| `GRAPH_CLIENT_SECRET` | Secret de l'app |
| `GRAPH_SENDER` | Adresse email d'envoi |

## Structure

```
program/      # Program (ex-Agenda) — regroupe des Events
event/        # Séances d'entraînement (rattachées à un Program)
round/        # Séries d'exercices au sein d'un Event
exercise/     # Exercices individuels (Modality, EnergySegment)
member/       # Athlètes
customuser/   # Extension du User Django (language, is_*_admin)
team/         # Teams (sport, language, owner, managers, athlètes)
sport/        # Sports + Modalities
ai/           # Endpoint /api/v1/ai/ping/
tools/        # i18n, throttling, exceptions, ai client, middleware, email
tests/        # pytest + factory_boy
locale/       # Translations (fr complet, nl/it/es à compléter)
```

## Endpoints principaux

| Méthode | URL | Permission | Description |
|---|---|---|---|
| POST | `/api/v1/auth/token/` | Public | JWT login |
| GET, PATCH | `/api/v1/me/` | Auth | Profil user courant (incl. language) |
| GET, POST | `/api/v1/teams/` | Auth | Liste / créer team |
| GET, POST | `/api/v1/programs/` | Auth | Programs |
| POST | `/api/v1/programs/{id}/generate-events/` | Manager | Génération plan IA |
| POST | `/api/v1/events/{id}/generate-training/` | Manager | Génération séance IA |
| GET, POST | `/api/v1/exercises/` | Auth (write : trainer) | Exercises |
| POST | `/api/v1/exercises/{id}/clone/` | Trainer | Cloner exercise |
| POST | `/api/v1/rounds/{id}/clone/` | Trainer | Cloner round |
| POST | `/api/v1/join-requests/` | Auth | Demander à rejoindre une team |
| POST | `/api/v1/invitations/` | Trainer | Pré-inscrire un athlète |
| GET, POST | `/api/v1/invitations/lookup/<token>/` | Public | Finaliser invitation |
| POST | `/api/v1/ai/ping/` | Trainer | Test API Anthropic |
| GET | `/api/v1/sports/` | Auth | Liste des sports |
| GET | `/api/v1/sports/<id>/modalities/` | Auth | Modalities d'un sport |

Détail complet sur `/api/v1/docs/` (Swagger UI).

## Authentification

### Flux signup classique (Flux A)

1. `POST /api/v1/_allauth/app/v1/auth/signup/` — créer compte
2. Email de vérification envoyé via Graph
3. `POST /api/v1/_allauth/app/v1/auth/email/verify/` — confirmer
4. `POST /api/v1/auth/token/` — JWT access+refresh
5. Optionnel : `POST /api/v1/join-requests/` pour rejoindre une team publique

### Flux invitation par trainer (Flux B)

1. Trainer : `POST /api/v1/invitations/` avec firstname/lastname/email
2. Système crée `Member`, envoie email avec token
3. Athlète clique le lien : `GET /api/v1/invitations/lookup/<token>/`
4. Athlète choisit username/password : `POST /api/v1/invitations/lookup/<token>/`
5. Réponse contient access+refresh JWT (auto-login)

## Tests

```bash
pytest
pytest --tb=short
```

## Catalogue partagé par sport

`Exercise` et `Round` forment un catalogue **partagé entre toutes les teams du même sport**. Concrètement :

- Un coach Natation voit **tous** les Exercises et Rounds liés au sport Natation, peu importe la team d'origine.
- Un coach Course à pied ne voit pas les Exercises de Natation, et inversement.
- L'enrichissement collectif est encouragé : un Exercise créé par un coach bénéficie à tous les coaches du même sport.
- Le mécanisme **lock + clone** protège l'intégrité : un Exercise utilisé dans 2+ Rounds (ou un Round utilisé dans 2+ Events) devient immutable. Pour modifier, il faut le cloner via `POST /api/v1/exercises/{id}/clone/` ou `POST /api/v1/rounds/{id}/clone/`.
- **Permission d'écriture** : owner ou manager d'au moins une team active (permission `IsTrainer`).
- **Permission de lecture** : tout user authentifié, **scopé par sport** via `team.utils.user_accessible_sport_ids` (l'union des sports des teams où le user est owner, manager, ou athlète).
- `Round` porte un FK `sport` explicite (PROTECT). La validation refuse qu'un exercise d'un sport différent soit attaché à un Round.

## i18n

- **Source** : anglais (`gettext_lazy(_("..."))` partout)
- **Langues supportées** : `fr`, `nl`, `en`, `it`, `es`
- **`LANGUAGE_CODE = 'en'`** (fallback technique). `Team.language` et `CustomUser.language` ont `default='fr'`.
- **Résolution langue requête** : `user.language` > `Accept-Language` > `LANGUAGE_CODE`. Le middleware `tools.middleware.UserLanguageMiddleware` force la langue de l'utilisateur authentifié sur tout le cycle de la requête.
- **Format erreur** : `{"code": "snake_case", "detail": "<localisé>"}`. Le frontend peut matcher sur `code` (identifiant stable) ou afficher `detail` (déjà localisé).
- **Traductions** : `locale/<lang>/LC_MESSAGES/django.po`. `fr.po` est complet ; `nl/it/es` sont des stubs (header seul, fallback EN).

```bash
# Après install gettext :
django-admin makemessages -l fr -l nl -l it -l es \
  --ignore=.venv --ignore=migrations
django-admin compilemessages
```

## Roadmap technique

### Fait

- DRF API-only refactor
- JWT + allauth headless
- Teams + permissions (owner / manager / athlete)
- Lock + Clone sur catalogue d'exercices et de rounds
- Self-signup et trainer invitation
- Sport + Modality
- Génération IA plan + entraînement (Anthropic Claude)
- Throttling endpoints IA (UserRateThrottle scopés)
- Pre-commit hooks (ruff + black)
- i18n niveau 1 (Team.language, User.language) et niveau 2 (codes d'erreur structurés, FR traduit)
- ENUM_NAME_OVERRIDES sur drf-spectacular pour codegen TypeScript propre

### À venir

- Sentry monitoring
- CI/CD GitHub Actions
- Tests permissions affinés
- Translations nl, it, es à compléter
- Restriction Microsoft Graph App Access Policy (avant prod)
- Multi-langue templates email
- Rotation `SECRET_KEY` + secrets Graph/Anthropic en prod
