# 🚀 HuTech — Le Réseau Social Tech

<p align="center">
  <img src="https://img.shields.io/badge/Flask-2.3+-0A192F?style=flat&logo=flask&logoColor=64FFDA" alt="Flask">
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0+-0A192F?style=flat&logo=python&logoColor=64FFDA" alt="SQLAlchemy">
  <img src="https://img.shields.io/badge/Python-3.10+-0A192F?style=flat&logo=python&logoColor=64FFDA" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-64FFDA?style=flat" alt="License">
</p>

<p align="center">
  <b>Connect · Build · Share</b>
</p>

<p align="center">
  <i>La plateforme communautaire où les développeurs, designers et passionnés de tech se rencontrent, collaborent et partagent leur savoir-faire.</i>
</p>

---

## 📸 Aperçu

| Feed | Profil | Messagerie | Stories |
|------|--------|------------|---------|
| <kbd>![Feed](docs/screenshots/feed.png)</kbd> | <kbd>![Profil](docs/screenshots/profile.png)</kbd> | <kbd>![Chat](docs/screenshots/chat.png)</kbd> | <kbd>![Stories](docs/screenshots/stories.png)</kbd> |

---

## ✨ Fonctionnalités

### 🏠 Feed & Publications
- **Feed personnalisé** — Posts des utilisateurs suivis + contenu tendance
- **Types de posts variés** : Articles, tutoriels, questions, *Show & Tell*, projets
- **Système de likes** avec notifications en temps réel
- **Commentaires imbriqués** avec réponses
- **Tags tech** pour organiser et découvrir le contenu
- **Scroll infini** via API REST

### 📖 Stories Éphémères
- Stories avec **durée de vie de 24h**
- Modes : **texte stylisé**, **image**, **code** avec coloration syntaxique
- **Carrousel** de stories par utilisateur (style Instagram)
- **Progress bar animée** et navigation au clavier
- Compteur de vues

### 💬 Messagerie Instantanée (Style WhatsApp)
- **Chat en temps réel** avec polling AJAX
- **Indicateur "en train d'écrire"**
- **Accusés de lecture** (coches bleues)
- **Statut de présence** (en ligne, vu à...)
- Envoi de **photos** dans les conversations
- **Badge de messages non lus** sur la navigation

### 👤 Profils Développeurs
- **Carte d'identité tech** : rôle, niveau d'expérience, stack
- **Liens sociaux** : GitHub, LinkedIn, Twitter, Portfolio
- **Statut de disponibilité** : open to work, open to collaborate, hiring
- **Upload d'avatar et bannière**
- **Followers / Following** avec notifications

### 🔔 Notifications
- Centre de notifications complet
- Types : like, commentaire, follow, mention, invitation projet, candidature, message
- **Badge en temps réel** sur l'icône de navigation
- Marquage "tout lu" en un clic

### 🔍 Explorer & Recherche
- **Recherche globale** : utilisateurs, posts, projets, tags
- **Tags populaires** avec couleurs personnalisées
- **Projets tendance** et publications populaires

### 🛠️ Projets Tech
- **Showcase de projets** avec stack technique
- Liens GitHub, démo, documentation
- **Recherche de contributeurs**
- Licence open source

### 💼 Offres d'Emploi
- Publication d'offres tech
- Candidatures avec lettre de motivation
- **Filtres** : remote, on-site, hybrid

---

## 🏗️ Architecture

```
HuTech/
├── app.py                 # Point d'entrée Flask
├── config.py              # Configuration (DB, OAuth, Upload)
├── db.py                  # Instance SQLAlchemy
├── models.py              # Modèles de données
├── routes.py              # Routes & contrôleurs
├── requirements.txt       # Dépendances
├── static/
│   └── images/           # Uploads (avatars, posts, stories)
└── templates/
    ├── auth/             # Pages d'authentification
    ├── base.html         # Layout principal (nav glassmorphism)
    ├── index.html        # Feed
    ├── profile.html      # Profil utilisateur
    ├── chat.html         # Messagerie
    ├── create_post.html  # Création de post
    ├── create_story.html # Création de story
    └── ...
```

### Stack Technique

| Couche | Technologie |
|--------|-------------|
| **Backend** | Python 3.10+, Flask 2.3+ |
| **ORM** | SQLAlchemy 2.0+ avec Flask-Migrate |
| **Base de données** | SQLite (dev) / PostgreSQL (prod via Neon) |
| **Auth** | Sessions Flask + OAuth 2.0 (Google, GitHub) |
| **Frontend** | HTML5, CSS3 vanilla, JavaScript vanilla |
| **UI/UX** | Glassmorphism, Inter font, design system custom |
| **Temps réel** | Polling AJAX + Server-Sent Events (notifications) |

---

## 🚀 Installation

### Prérequis
- Python 3.10 ou supérieur
- pip ou uv

### 1. Cloner le repo

```bash
git clone https://github.com/maryam2379/HuTech.git
cd HuTech
```

### 2. Créer l'environnement virtuel

```bash
python3 -m venv hubtech_env
source hubtech_env/bin/activate  # Linux/Mac
# ou
hubtech_env\Scripts\activate  # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configuration

Créer un fichier `.env` à la racine :

```env
SECRET_KEY=votre-cle-secrete-tres-securisee
UPLOAD_FOLDER=static/images
MAX_CONTENT_LENGTH=16777216

# Base de données (optionnel — SQLite par défaut)
# DATABASE_URL=postgresql://user:pass@host/db

# OAuth Google
GOOGLE_CLIENT_ID=votre-client-id
GOOGLE_CLIENT_SECRET=votre-client-secret

# OAuth GitHub
GITHUB_CLIENT_ID=votre-client-id
GITHUB_CLIENT_SECRET=votre-client-secret
```

### 5. Lancer l'application

```bash
python app.py
```

L'application est accessible sur **http://localhost:5000** 🎉

---

## 🗄️ Modèles de Données

```mermaid
erDiagram
    USER ||--o{ POST : "publie"
    USER ||--o{ PROJECT : "possède"
    USER ||--o{ MESSAGE : "envoie"
    USER ||--o{ MESSAGE : "reçoit"
    USER ||--o{ STORY : "crée"
    USER ||--o{ NOTIFICATION : "reçoit"
    USER ||--o{ JOB : "publie"
    USER }o--o{ USER : "follow"
    USER }o--o{ PROJECT : "contribue"
    USER }o--o{ TAG : "skills"
    POST }o--o{ TAG : "tags"
    PROJECT }o--o{ TAG : "tags"
    POST ||--o{ COMMENT : "contient"
    JOB ||--o{ JOB_APPLICATION : "reçoit"
    STORY ||--o{ STORY_VIEW : "vue par"
```

### Entités principales

| Entité | Description |
|--------|-------------|
| **User** | Développeur avec profil tech complet |
| **Post** | Publication (article, tutoriel, question, projet) |
| **Story** | Contenu éphémère 24h (texte, image, code) |
| **Message** | Chat privé avec accusés de lecture |
| **Project** | Showcase de projet avec stack technique |
| **Job** | Offre d'emploi tech |
| **Notification** | Système de notification temps réel |
| **Tag** | Technologies / catégories (Python, React, etc.) |

---

## 🔐 Authentification

### Connexion classique
- Inscription avec validation email
- Hashage bcrypt des mots de passe
- Sessions sécurisées

### OAuth 2.0
- **Google** — Connexion via compte Google
- **GitHub** — Connexion via compte GitHub avec récupération automatique du profil (bio, localisation, avatar)

---

## 🎨 Design System

### Palette de couleurs

| Token | Hex | Usage |
|-------|-----|-------|
| `--navy` | `#0A192F` | Couleur principale, fonds sombres |
| `--teal` | `#64FFDA` | Accent, boutons, liens |
| `--white` | `#F8FAFC` | Texte clair, fonds |
| `--slate` | `#8892B0` | Texte secondaire |
| `--coral` | `#FF6B6B` | Alertes, likes |

### Composants UI
- **Navigation bottom** — Glassmorphism avec blur 20px
- **Cartes** — Bordures subtiles, ombres douces, radius 20px+
- **Boutons** — Dégradés, hover avec translation Y
- **Inputs** — Focus ring teal avec glow
- **Stories** — Overlay sombre, progress bars animées

---

## 📡 API Endpoints

### Posts
```
GET  /api/feed?page=1&per_page=10&type=all    # Feed paginé
POST /api/posts/<id>/like                      # Like/unlike
GET  /api/posts/<id>/comments                  # Commentaires
```

### Notifications
```
GET  /api/notifications/unread-count           # Badge non lues
POST /api/notifications/<id>/read              # Marquer lue
POST /api/notifications/mark-all-read          # Tout lu
```

### Messages
```
POST /messages/<user>/send                     # Envoyer message
GET  /messages/<user>/poll?after=<id>          # Polling nouveaux messages
POST /messages/<user>/typing                   # Signal "en train d'écrire"
GET  /api/messages/unread                      # Badge messages
```

### Stories
```
GET  /api/stories/active                       # Stories actives
GET  /api/stories/<id>                         # Détail story
```

---

## 🛣️ Roadmap

- [ ] **WebSockets** — Remplacer le polling par Socket.IO pour le chat temps réel
- [ ] **PWA** — Application web progressive avec offline mode
- [ ] **Dark mode** — Thème sombre natif
- [ ] **Recherche avancée** — Elasticsearch pour la recherche full-text
- [ ] **CI/CD** — GitHub Actions + Docker
- [ ] **Tests** — Pytest avec couverture > 80%
- [ ] **Internationalisation** — i18n (FR/EN)

---

## 🤝 Contribution

Les contributions sont les bienvenues !

1. Fork le projet
2. Créer une branche (`git checkout -b feature/ma-feature`)
3. Commit (`git commit -m 'feat: ajout de ma feature'`)
4. Push (`git push origin feature/ma-feature`)
5. Ouvrir une Pull Request

### Convention de commits
- `feat:` — Nouvelle fonctionnalité
- `fix:` — Correction de bug
- `style:` — Changement de style/CSS
- `refactor:` — Refactoring
- `docs:` — Documentation

---

## 📄 Licence

Ce projet est sous licence **MIT**. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 👩‍💻 Auteure

**MFOPIT MAR'YAM** — [@maryam2379](https://github.com/maryam2379)

<p align="center">
  <sub>Construit avec 💚 et beaucoup de café</sub>
</p>
