# Cahier des charges — OptiPilot-Agent

## 1. Présentation

**OptiPilot-Agent** est un prototype d’outil permettant de transformer une consigne métier exprimée en langage naturel en une **analyse structurée et directement exploitable par une équipe Ops ou technique**.

L’objectif est de réduire le temps entre une idée métier et sa transformation en spécification exploitable pour une automatisation.

## 2. Objectifs

L’outil doit permettre de :

- comprendre et structurer une demande métier ;
- identifier les objectifs, contraintes, risques et priorités ;
- générer un cahier des charges technique simplifié ;
- proposer un workflow d’automatisation ;
- générer un prompt pour un agent IA spécialisé ;
- produire une restitution compréhensible par un utilisateur non technique.

## 3. Fonctionnement

Le flux principal est :

**Directive métier → Analyse IA → Spécification → Workflow → Action d’automatisation**

La directive peut provenir d’un email, d’un message, d’une réunion ou d’une transcription.

Exemple :

> « Nous devons automatiser le traitement des demandes reçues par l’équipe. »

L’outil transforme cette demande en informations structurées :

- objectif ;
- données nécessaires ;
- étapes du traitement ;
- contraintes ;
- risques ;
- niveau de priorité ;
- actions recommandées.

## 4. Architecture technique

Le prototype utilise :

- **Python** pour la logique métier ;
- **FastAPI** pour exposer l’API REST ;
- **Groq / Mistral** comme fournisseurs LLM ;
- un mode **Demo** sans clé API ;
- **Make ou n8n** pour l’orchestration ;
- **Git/GitHub** pour le versionnement ;
- **Render** pour le déploiement.

## 5. API

### `GET /health`

Vérifie que l’API fonctionne.

### `POST /analyser`

Entrée :

```json
{
  "note": "Nous devons automatiser le traitement des demandes reçues par l'équipe.",
  "provider": "demo"
}
```

Sortie : JSON structuré contenant notamment :

- analyse stratégique ;
- cahier des charges technique ;
- risques et contraintes ;
- prompt système ;
- notification vulgarisée.

Les fournisseurs autorisés sont :

`demo`, `groq`, `mistral`.

## 6. Sécurité

Le prototype doit :

- éviter l’exposition de données inutiles au modèle IA ;
- ne jamais stocker de clé API dans le code ;
- prévoir l’anonymisation ou la pseudonymisation lorsque nécessaire ;
- conserver une architecture stateless par défaut ;
- permettre de choisir le fournisseur selon les contraintes de données.

## 7. Périmètre du prototype

### Inclus

- CLI Python ;
- API FastAPI ;
- intégration LLM ;
- mode Demo ;
- génération JSON structurée ;
- intégration Make/n8n ;
- documentation technique.

### Non inclus

- interface graphique complète ;
- authentification multi-utilisateur ;
- base de données persistante ;
- exécution automatique d’actions métier sensibles.

## 8. Évolution

À terme, OptiPilot-Agent pourra évoluer vers une architecture agentique capable de :

**comprendre → analyser → demander une clarification → utiliser des outils → valider → déclencher un workflow.**

## 9. Critères de réussite

Le prototype est considéré comme fonctionnel si :

- une directive métier peut être envoyée à l’API ;
- l’IA produit une réponse JSON structurée ;
- le mode Demo fonctionne sans clé API ;
- Groq et Mistral peuvent être utilisés séparément ;
- les risques et contraintes sont identifiés ;
- un cahier des charges exploitable est généré ;
- Make/n8n peut récupérer le résultat ;
- les fournisseurs invalides sont rejetés.
