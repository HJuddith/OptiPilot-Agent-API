# Cahier des charges — OptiPilot-Agent

## 1. Présentation

**OptiPilot-Agent** est un prototype d'outil permettant de transformer une directive métier exprimée en langage naturel en une **analyse structurée, contextualisée et exploitable**, adaptée au profil du destinataire.

L'objectif est de réduire le temps entre une idée métier et sa transformation en spécification, tout en conservant une **validation humaine avant les actions importantes**.

---

## 2. Objectifs

L'outil doit permettre de :

- comprendre et structurer une directive métier ;
- identifier objectifs, contraintes, risques, données et priorités ;
- adapter la restitution au profil du destinataire : **Tech, Ops, RH, Direction ou non-technique** ;
- générer un cahier des charges technique ;
- proposer un workflow d'automatisation ;
- générer un prompt système pour un agent IA spécialisé ;
- présenter une synthèse compréhensible dans Slack ;
- permettre à un utilisateur de prendre une décision directement depuis Slack ;
- générer un document PDF correspondant au profil sélectionné ;
- assurer le suivi du traitement dans Google Sheets.

---

## 3. Fonctionnement

Le workflow principal est :

**Tally → Make → OptiPilot-Agent → Slack → décision → Make → Google Sheets**

### 3.1 Collecte

**Tally** permet de recueillir :

- la directive métier ;
- le destinataire ;
- le profil du destinataire lorsque celui-ci est connu.

### 3.2 Analyse IA

**Make** transmet la directive à OptiPilot-Agent.

L'agent :

- analyse la directive ;
- identifie les besoins, contraintes et risques ;
- distingue les informations connues des informations non précisées ;
- génère une analyse complète ;
- prépare plusieurs niveaux de restitution selon le profil.

Les profils peuvent notamment être :

- Technique / IT ;
- Ops / Automatisation ;
- RH ;
- Direction / Management ;
- Métier / Non-technique.

La base factuelle reste identique : seul le **niveau de détail, le vocabulaire et les informations mises en avant** sont adaptés au profil.

### 3.3 Restitution et décision

Le résultat est envoyé dans **Slack**.

Slack présente :

- une synthèse adaptée ;
- les informations importantes ;
- les points d'attention ;
- la décision attendue ;
- un sélecteur permettant de choisir le profil du document ;
- une action de génération de PDF ;
- des actions de validation.

Exemple :

**Profil du document :** `RH ▼`

**[ Générer le PDF ]**

**[ Valider ] [ Relecture RH ] [ Reporter ]**

Les boutons permettent de déclencher différentes branches du workflow.

---

## 4. Génération documentaire

Après sélection d'un profil, Make peut demander à OptiPilot-Agent de générer la restitution correspondante.

Le système peut produire un **PDF prêt à être téléchargé ou partagé**.

Le contenu du PDF est adapté au profil sélectionné.

Exemples :

- **Technique** : architecture, flux, données, intégrations et contraintes ;
- **Ops** : processus, automatisations, déclencheurs et contrôles ;
- **RH** : enjeux humains, confidentialité, RGPD et validations nécessaires ;
- **Direction** : synthèse, enjeux, risques, délais et décisions attendues ;
- **Non-technique** : explication simple du besoin, bénéfices et prochaines étapes.

---

## 5. Suivi dans Google Sheets

Google Sheets sert de **tableau de suivi du workflow**.

Structure minimale :

| Date       | Pole_cible | Urgence | Titre              | Profil | Statut     | Décision |
| ---------- | ---------- | ------- | ------------------ | ------ | ---------- | -------- |
| 18/09/2026 | QVT        | Haute   | Synthèse audit QVT | RH     | En attente | —        |

Les informations de suivi peuvent être mises à jour après chaque interaction Slack.

Exemples :

- `Validé`
- `Relecture RH`
- `En attente`
- `Reporté`
- `PDF généré`

---

## 6. Architecture technique

Le prototype utilise :

- **Python** pour la logique métier ;
- **FastAPI** pour exposer l'API REST ;
- **Groq / Mistral** comme fournisseurs LLM ;
- un mode **Demo** sans clé API ;
- **Make** pour l'orchestration ;
- **Tally** pour la collecte ;
- **Slack** pour la restitution et les décisions humaines ;
- **Google Sheets** pour le suivi ;
- **Git/GitHub** pour le versionnement ;
- **Render** pour le déploiement.

L'architecture Python est organisée notamment autour de :

```text
OptiPilot-Agent/
├── main.py
├── utils/
│   ├── config.py
│   ├── prompt_loader.py
│   ├── validators.py
│   └── slack.py
├── prompts/
│   └── system_prompt.txt
└── samples/
```

---

## 7. API

### `GET /health`

Vérifie que l'API fonctionne.

### `POST /analyser`

Entrée :

```json
{
  "note": "Nous devons automatiser le traitement des demandes reçues par l'équipe.",
  "provider": "demo"
}
```

Sortie : JSON structuré contenant notamment :

- métadonnées ;
- profil du destinataire ;
- analyse stratégique ;
- restitution adaptée ;
- cahier des charges technique ;
- risques et contraintes ;
- prompt système ;
- notification Slack ;
- actions disponibles.

Les fournisseurs autorisés sont :

`demo`, `groq`, `mistral`.

---

## 8. Sécurité et gouvernance

Le prototype doit :

- éviter l'exposition de données inutiles au modèle IA ;
- ne jamais stocker de clé API dans le code ;
- prévoir l'anonymisation ou la pseudonymisation lorsque nécessaire ;
- éviter de reproduire des données personnelles dans les restitutions ;
- distinguer les informations présentes dans la directive des propositions techniques ;
- ne pas inventer de dates, délais, outils, volumes ou contraintes ;
- conserver une architecture stateless par défaut ;
- maintenir une **validation humaine avant les actions importantes**.

---

## 9. Périmètre du prototype

### Inclus

- formulaire Tally ;
- orchestration Make ;
- CLI Python ;
- API FastAPI ;
- intégration LLM ;
- mode Demo ;
- Groq et Mistral ;
- génération JSON structurée ;
- adaptation des restitutions aux profils ;
- notification Slack ;
- interactions Slack ;
- génération de PDF ;
- suivi Google Sheets ;
- documentation technique.

### Non inclus

- interface graphique complète dédiée ;
- authentification multi-utilisateur ;
- base de données applicative persistante ;
- exécution automatique d'actions métier sensibles sans validation humaine ;
- système complet de gestion documentaire.

---

## 10. Évolution

À terme, OptiPilot-Agent pourra évoluer vers une architecture agentique capable de :

**comprendre → analyser → adapter → demander une clarification → utiliser des outils → générer des livrables → demander une validation → déclencher un workflow.**

L'architecture pourra également intégrer davantage d'outils et de connecteurs selon les besoins métier.

---

## 11. Critères de réussite

Le prototype est considéré comme fonctionnel si :

- une directive peut être collectée depuis Tally ;
- Make peut transmettre la directive à l'API ;
- l'IA produit une réponse JSON structurée ;
- les informations sont adaptées au profil du destinataire ;
- le mode Demo fonctionne sans clé API ;
- Groq et Mistral peuvent être utilisés séparément ;
- les risques et contraintes sont identifiés ;
- un cahier des charges exploitable est généré ;
- une restitution adaptée peut être affichée dans Slack ;
- les actions Slack peuvent être interprétées par Make ;
- un PDF peut être généré selon le profil sélectionné ;
- le statut et la décision peuvent être enregistrés dans Google Sheets ;
- les fournisseurs invalides sont rejetés ;
- aucune action métier importante n'est exécutée sans validation humaine.
