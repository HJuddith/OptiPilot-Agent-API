# 🧭 OptiPilot-Agent

**L'agent qui transforme une note brute d'un responsable en un cahier des charges Ops exploitable — en quelques secondes plutôt qu'en plusieurs jours.**

OptiPilot-Agent analyse une directive brute, la structure et produit un résultat exploitable par une équipe Ops : analyse stratégique, cahier des charges technique, prompt système et notification Slack.

Le workflow actuel relie :

**Tally → Make → OptiPilot-Agent → Slack + Google Sheets**

---

## 🔗 Démonstration & ressources

### Démo live

**[Tester le formulaire OptiPilot](https://tally.so/r/yPODX4)**

### Agent API déployé

**[OptiPilot-Agent API](https://optipilot-agent-api.onrender.com/docs)**

### Code

**[Dépôt GitHub](https://github.com/HJuddith/OptiPilot-Agent)**

### Automatisation

**[Workflow Make](https://eu1.make.com/public/shared-scenario/oJmiTsAxSTd/opti-pilot-agent)**

### Documentation Make

**[Documentation complète](docs/WORKFLOW_MAKE.md)**

### Distribution Slack

**[Canal Slack](https://app.slack.com/client/T07KV2SSAE6/C0C2K1L8FHT)**

### Suivi Google Sheets

**[Google Sheets](https://docs.google.com/spreadsheets/d/14hZJsGDaJTAQZ6JnFPJCkfN4uXfCMMMMYipmG--CZeM/edit?gid=0#gid=0)**

![Aperçu du workflow](assets/MakeWorkflow.JPG)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LLM](https://img.shields.io/badge/LLM-Groq%20%7C%20GPT--OSS%20120B-f55036)
![Fallback](https://img.shields.io/badge/Fallback-Mistral%20UE-FF7000)
![Status](https://img.shields.io/badge/Status-PoC%20fonctionnel-success)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

> Projet portfolio conçu pour illustrer des compétences **Tech Ops / AI Builder** : cadrage d'un besoin IA, structuration d'un workflow, automatisation avec Make, intégration d'un LLM et restitution pédagogique pour des profils non techniques.

---

# 🎯 Pourquoi OptiPilot-Agent ?

Dans une entreprise, un responsable peut exprimer un besoin rapidement, parfois sous forme de note vocale, de message ou de directive informelle.

Le problème n'est pas forcément l'idée elle-même, mais le temps nécessaire pour la transformer en un besoin suffisamment structuré pour être exploité par une équipe Ops.

**OptiPilot-Agent sert d'interface entre l'intention métier et son cadrage opérationnel.**

| Sans OptiPilot-Agent                   | Avec OptiPilot-Agent                        |
| -------------------------------------- | ------------------------------------------- |
| Directive brute ou informelle          | Directive structurée                        |
| Reformulation manuelle du besoin       | Analyse automatisée                         |
| Informations importantes dispersées    | Analyse stratégique structurée              |
| Cadrage technique manuel               | Cahier des charges généré                   |
| Restitution technique difficile à lire | Notification Slack vulgarisée               |
| Risques RGPD pouvant être oubliés      | Identification des risques liés aux données |

Le projet cherche ainsi à démontrer une approche **IA + automatisation + pédagogie + contrôle humain**.

---

# 🏗️ Architecture

```text
┌─────────────────────────────┐
│        Tally                │
│  Formulaire de directive    │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│          Make               │
│        Webhook              │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│     OptiPilot-Agent         │
│                             │
│  • Prompt système           │
│  • Appel LLM                │
│  • Parsing JSON              │
│  • Validation                │
│  • Normalisation Slack       │
└──────────────┬──────────────┘
               │
               │ JSON structuré
               ▼
┌─────────────────────────────┐
│          Make               │
│       JSON Parse            │
└──────────────┬──────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
┌──────────────┐ ┌────────────────┐
│    Slack     │ │ Google Sheets  │
│ Restitution  │ │    Suivi       │
│ + actions    │ │   historique   │
└──────────────┘ └────────────────┘
```

L'API FastAPI constitue le point d'entrée HTTP utilisé par Make.

```text
POST /analyser
```

---

# 🔄 Workflow Make actuel

```text
Responsable
     │
     ▼
   Tally
     │
     ▼
   Make
     │
     │ HTTP POST
     ▼
OptiPilot-Agent API
     │
     │ JSON
     ▼
 JSON Parse
     │
     ├───────────────► Slack
     │                  │
     │                  ├── Synthèse
     │                  └── Boutons visuels
     │
     └───────────────► Google Sheets
                        │
                        └── Suivi de la demande
```

### Slack

La notification Slack est générée selon l'analyse et contient une synthèse ainsi que des actions adaptées au contexte.

Exemples :

- **Valider pour le Codex**
- **Demander relecture RH**
- **Reporter**
- **Demander clarification**
- **Annuler**

Les boutons sont actuellement affichés mais non interactifs.

Ils ne déclenchent donc pas encore de retour vers Make.

---

# 🧠 Fonctionnement de l'agent

OptiPilot-Agent transforme une directive brute en plusieurs niveaux de sortie.

### 1. Analyse stratégique

Identification notamment de :

- pôle cible ;
- urgence ;
- complexité ;
- parties prenantes ;
- risques ;
- données manipulées ;
- contraintes ;
- besoins d'automatisation ;
- livrables attendus.

### 2. Cahier des charges technique

Transformation du besoin en éléments exploitables par une équipe Ops :

- objectif ;
- données d'entrée ;
- traitement ;
- automatisations ;
- composants IA ;
- sorties ;
- intégrations ;
- sécurité ;
- critères de validation.

### 3. Prompt système

L'agent peut générer un prompt destiné à un autre agent IA chargé d'exécuter une tâche spécifique.

### 4. Notification Slack

Une version vulgarisée est produite pour permettre à un profil non technique de comprendre :

- ce qui a été préparé ;
- les principaux risques ;
- ce qui doit être fait ensuite.

---

# 👤 Adaptation au profil

L'analyse centrale constitue la **source de vérité**.

Elle peut ensuite être présentée selon différents profils :

- RH ;
- Ops / Automatisation ;
- Technique / IT ;
- Direction / Management ;
- Métier / Opérationnel ;
- Profil non technique.

Le contenu factuel ne doit pas changer.

Seuls peuvent varier :

- le vocabulaire ;
- le niveau de détail ;
- la présentation ;
- les éléments mis en avant.

Exemple :

```text
Même analyse
     │
     ├──► Profil RH
     │       confidentialité / RGPD / humain
     │
     ├──► Profil Ops
     │       processus / automatisation
     │
     ├──► Profil Technique
     │       architecture / données / intégrations
     │
     └──► Profil non technique
             synthèse / enjeux / décisions
```

---

# 🛠️ Stack technique

| Composant        | Choix                        | Rôle                          |
| ---------------- | ---------------------------- | ----------------------------- |
| Langage          | Python 3.10+                 | Logique de l'agent            |
| LLM principal    | Groq — `openai/gpt-oss-120b` | Analyse et génération JSON    |
| LLM fallback     | Mistral                      | Alternative de traitement     |
| API              | FastAPI + Uvicorn            | Endpoint HTTP                 |
| Hébergement      | Render                       | Déploiement de l'API          |
| Orchestration    | Make                         | Automatisation du workflow    |
| Formulaire       | Tally                        | Collecte de la directive      |
| Restitution      | Slack                        | Présentation de l'analyse     |
| Suivi            | Google Sheets                | Historisation des demandes    |
| Format d'échange | JSON                         | Contrat entre l'agent et Make |

---

# 📁 Structure du projet

```text
OptiPilot-Agent/
│
├── main.py
├── api.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── utils/
│   ├── __init__.py
│   ├── config.py
│   ├── prompt_loader.py
│   ├── validators.py
│   └── slack.py
│
├── prompts/
│   └── system_prompt.txt
│
├── samples/
│   ├── input_note_resp.txt
│   └── output_optipilot_result.json
│
├── assets/
│   └── MakeWorkflow.JPG
│   └── OptiPilot-Agent-api.JPG
│   └── Sheets.JPG
│   └── TallyForm.JPG
│   └── SlackMessage.JPG
│
└── docs/
    ├── CAHIER_DES_CHARGES.md
    └── WORKFLOW_MAKE.md
```

---

# 🚀 Installation

## Installation locale

```bash
pip install -r requirements.txt
```

Copier le fichier de configuration :

```bash
cp .env.example .env
```

Le mode `demo` permet de tester l'agent sans clé API.

```bash
python main.py --input samples/input_note_resp.txt --provider demo
```

---

## Utilisation avec Groq

Configurer :

```text
GROQ_API_KEY=...
GROQ_MODEL=openai/gpt-oss-120b
```

Puis :

```bash
python main.py \
  --input samples/input_note_resp.txt \
  --provider groq \
  --output resultat.json
```

---

## Utilisation avec Mistral

Configurer :

```text
MISTRAL_API_KEY=...
MISTRAL_MODEL=mistral-small-latest
```

Puis :

```bash
python main.py \
  --input samples/input_note_resp.txt \
  --provider mistral \
  --output resultat.json
```

---

# 🌐 API

L'API expose notamment :

```text
POST /analyser
```

Pour lancer l'API localement :

```bash
uvicorn api:app --reload --port 8000
```

Documentation Swagger :

```text
http://localhost:8000/docs
```

L'API de démonstration est également déployée sur Render :

```text
https://optipilot-agent-api.onrender.com/docs
```

---

# 📄 Exemple de cas d'utilisation

Le fichier :

```text
samples/input_note_resp.txt
```

contient une note informelle concernant un audit QVT.

Le besoin exprimé concerne notamment :

- une synthèse par pôle ;
- des centaines de verbatims ;
- la présence potentielle de noms dans les commentaires ;
- l'anonymisation ;
- une échéance de trois semaines ;
- une restitution synthétique sur Slack ;
- une validation humaine avant diffusion.

L'agent transforme cette directive en résultat JSON structuré.

Le résultat complet est disponible dans :

```text
samples/output_optipilot_result.json
```

---

# 🔒 Sécurité et confidentialité

Le projet intègre plusieurs garde-fous :

| Mesure                                                  | Objectif                              |
| ------------------------------------------------------- | ------------------------------------- |
| Limitation de la taille des entrées                     | Réduire les abus                      |
| Validation du JSON retourné                             | Garantir le contrat d'interface       |
| Variables d'environnement pour les clés                 | Ne pas exposer les secrets            |
| Timeout des appels LLM                                  | Éviter les blocages                   |
| Détection des risques liés aux données personnelles     | Sensibiliser au RGPD                  |
| Anonymisation demandée avant analyse lorsque nécessaire | Réduire le risque d'exposition        |
| Validation humaine                                      | Maintenir un contrôle avant diffusion |

### Limite importante

Dans la version actuelle, l'anonymisation n'est **pas encore réalisée par un véritable moteur NER local avant l'appel au LLM**.

Une version de production devrait mettre en place un pré-traitement dédié avant toute transmission de données sensibles à un modèle externe.

---

# 🧪 Tests

### Vérification syntaxique

```bash
python -m py_compile main.py api.py
```

### Lint

```bash
python -m ruff check main.py api.py
```

### Test en mode Demo

```bash
python main.py \
  --input samples/input_note_resp.txt \
  --provider demo
```

### Test API local

```bash
uvicorn api:app --reload --port 8000
```

Puis :

```bash
curl -X POST http://localhost:8000/analyser \
  -H "Content-Type: application/json" \
  -d '{"note":"Test de directive","provider":"demo"}'
```

---

# ⚠️ Limites actuelles du PoC

Le projet est volontairement limité à une première version fonctionnelle.

### Actuellement fonctionnel

- [x] Formulaire Tally
- [x] Workflow Make
- [x] API FastAPI
- [x] Déploiement Render
- [x] Providers Demo / Groq / Mistral
- [x] Prompt système structuré
- [x] Analyse LLM
- [x] Validation et normalisation JSON
- [x] Génération du payload Slack
- [x] Restitution Slack
- [x] Suivi Google Sheets
- [x] Actions Slack affichées

### Pas encore implémenté

- [ ] Boutons Slack interactifs
- [ ] Retour Slack → Make
- [ ] Router Make basé sur l'action sélectionnée
- [ ] Sélection dynamique du profil depuis Slack
- [ ] Génération de PDF
- [ ] Téléchargement du PDF depuis Slack
- [ ] Anonymisation locale avant appel LLM
- [ ] Transcription automatique d'une note vocale
- [ ] Tests automatisés complets
- [ ] Rate limiting applicatif
- [ ] Gestion multi-tenant

---

# 🔮 Roadmap

## V1 — PoC actuel

```text
Tally
  ↓
Make
  ↓
OptiPilot-Agent
  ↓
Slack + Google Sheets
```

Objectif : valider la chaîne d'analyse et de restitution.

## V2 — Interactions Slack

```text
Slack
  ↓
Action utilisateur
  ↓
Make
  ↓
Router
  ├── Valider
  ├── Relecture RH
  └── Reporter
```

## V3 — Restitution avancée

```text
Analyse centrale
      ↓
Choix du profil
      ↓
Restitution adaptée
      ↓
Génération PDF
      ↓
Slack
```

Les profils pourront notamment être adaptés à :

- RH ;
- Ops ;
- Technique ;
- Management ;
- Métier.

## V4 — Sécurisation avancée

- anonymisation locale ;
- NER ;
- tests automatisés ;
- contrôle des données avant appel LLM ;
- rate limiting ;
- observabilité.

---

# 💡 Ce que démontre le projet

OptiPilot-Agent ne cherche pas uniquement à produire du texte avec une IA.

Le projet démontre une approche complète :

**Comprendre → structurer → automatiser → contrôler → restituer.**

Les compétences mises en pratique sont notamment :

- analyse de besoin ;
- prompt engineering ;
- intégration LLM ;
- développement Python ;
- API REST ;
- validation de données ;
- automatisation Make ;
- intégration Slack ;
- Google Sheets ;
- gestion des erreurs ;
- prise en compte de la confidentialité ;
- conception de workflows Ops ;
- vulgarisation pour les profils non techniques.

---

# 🎓 Ce que j'ai appris

### Contrat d'interface JSON

Définir une structure de sortie stable permet à Make de consommer les résultats de l'agent sans dépendre directement de la formulation du prompt.

### Gestion des providers

Le projet permet de changer de fournisseur LLM sans modifier l'ensemble du workflow.

### Validation des sorties IA

Une réponse générée par un LLM ne doit pas être considérée comme valide simplement parce qu'elle contient du JSON.

La réponse est donc contrôlée avant d'être transmise aux étapes suivantes.

### Sécurité dès le PoC

Les clés API sont externalisées, les entrées sont contrôlées et les erreurs sont traitées sans exposer inutilement d'informations sensibles.

### Conception progressive

Les fonctionnalités plus complexes — interactions Slack, génération PDF, anonymisation avancée — sont volontairement séparées de la première version afin de conserver un workflow simple et testable.

---

# ⚠️ Limites assumées

OptiPilot-Agent est un **Proof of Concept** et non une solution prête pour une utilisation en production avec des données sensibles.

En particulier :

- les boutons Slack sont actuellement non interactifs ;
- l'anonymisation locale n'est pas encore implémentée ;
- la transcription vocale n'est pas encore automatisée ;
- le workflow reste mono-tenant ;
- la génération PDF n'est pas encore implémentée ;
- le contrôle humain reste indispensable avant diffusion de résultats sensibles.

---

## 🚀 Vision

À terme, OptiPilot-Agent pourra évoluer vers un véritable assistant Ops :

```text
Directive brute
      ↓
Analyse IA
      ↓
Cadrage du besoin
      ↓
Adaptation au destinataire
      ↓
Slack
      ↓
Décision humaine
      ↓
Make
      ↓
Action automatisée
      ↓
Suivi
```

L'objectif n'est pas de remplacer la décision humaine, mais de **réduire le travail de structuration et faciliter le passage d'une idée métier à une action opérationnelle**.

---

_Projet portfolio réalisé dans le cadre d'un apprentissage orienté Tech Ops / AI Builder._
