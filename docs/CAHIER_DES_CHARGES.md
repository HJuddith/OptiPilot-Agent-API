# Cahier des Charges — OptiPilot-Agent

## 1. Contexte

Chez Qualisocial, le Directeur Général impulse une dynamique IA mais manque de temps pour formaliser et
transmettre ses idées aux équipes Ops. Résultat : des besoins IA/automatisation restent à l'état de note vocale
ou de phrase lancée en réunion, jamais traduits en spécification actionnable.

**OptiPilot-Agent** est un agent d'orchestration exécutif : il prend une directive brute du DG (texte ou
transcription de note vocale) et la transforme automatiquement en un paquet complet et exploitable par les Ops,
sans perdre le sens humain du message initial.

## 2. Objectifs

### 2.1 Objectifs business
- Réduire le délai entre "idée du DG" et "ticket Ops actionnable" de plusieurs jours à quelques minutes.
- Fournir au DG une restitution vulgarisée (Slack/Email) qui ne l'oblige pas à replonger dans le jargon technique.
- Donner aux Ops un cahier des charges structuré, réutilisable, et déjà pré-qualifié (pôle, urgence, complexité).
- Servir de brique réutilisable pour industrialiser le pipeline "directive → workflow Make/n8n" sur les 5 pôles
  (Sales, Marketing, Ops, RH, Finance).

### 2.2 Objectifs techniques (PoC)
- Un script Python autonome, sans dépendance lourde, exécutable en local en < 5 minutes.
- Une sortie strictement structurée en JSON (validable par schéma) pour permettre le branchement direct sur
  Make/n8n via webhook.
- Un prompt système versionné et réutilisable pour Claude 3.5 Sonnet (ou Mistral en fallback souverain).
- Un mode "démo" sans clé API pour permettre à un recruteur d'exécuter le projet immédiatement.

## 3. Spécifications fonctionnelles

### 3.1 Input
- Une note brute (texte) simulant une transcription de note vocale du DG.
- Champs de contexte optionnels : émetteur, date, canal d'origine (vocal/Slack/mail).
- Cas d'usage démonstrateur retenu : *anonymisation et analyse agrégée des résultats d'un audit QVT interne*
  (donnée sensible → cas volontairement choisi pour démontrer la sensibilité RGPD/QVT du poste).

### 3.2 Processing
1. **Nettoyage & structuration** de la note brute (suppression bruit, normalisation).
2. **Analyse stratégique** via LLM : identification du pôle cible, niveau d'urgence, complexité technique estimée,
   gain de temps estimé, drapeaux de risque (RGPD, données sensibles santé/QVT).
3. **Génération du cahier des charges technique** : objectif, inputs/outputs attendus, contraintes, jalons.
4. **Génération d'un prompt système optimisé**, prêt à être injecté dans un agent Claude/Mistral pour exécuter
   concrètement le besoin (ex: un agent d'anonymisation de verbatims).
5. **Génération d'une notification vulgarisée** (Slack Block Kit / Email HTML) avec des boutons d'action fictifs
   ("Valider", "Reporter", "Demander précision") pour le DG.

### 3.3 Output
- Un objet JSON unique, strictement typé (voir `samples/output_optipilot_result.json`), contenant :
  `meta`, `strategic_analysis`, `cahier_des_charges_technique`, `prompt_systeme_genere`, `notification`.
- Ce JSON est le contrat d'interface avec Make/n8n : un module HTTP/Webhook peut le consommer directement pour
  poster sur Slack, créer une ligne Google Sheet de suivi, ou ouvrir un ticket.

## 4. Périmètre & contraintes

### 4.1 Périmètre du PoC
- Inclus : script Python, prompt engineering, structuration JSON, exemple bout-en-bout, documentation d'intégration
  Make/n8n.
- Exclus (hors PoC, mentionné comme roadmap) : interface web, base de données persistante, authentification
  multi-utilisateurs, boutons Slack réellement interactifs (Slack Interactivity + backend d'écoute).

### 4.2 Contraintes RGPD / données sensibles (spécifiques QVT)
- **Minimisation** : le script ne doit jamais faire transiter de données nominatives vers le LLM. Le cas d'usage
  démo impose une étape d'anonymisation *avant* tout appel API (pseudonymisation des noms, suppression des
  identifiants directs).
- **Aucune donnée n'est stockée** par défaut : le script est stateless, aucune persistance disque des notes ou
  résultats sauf écriture explicite demandée par l'utilisateur.
- **Traçabilité** : chaque exécution horodate son résultat (`meta.timestamp`) pour audit.
- **Hébergement souverain envisageable** : fallback Mistral (Cloud EU / Le Chat) prévu pour les cas où la donnée
  ne doit pas sortir de l'UE ou transiter par un fournisseur non-européen.
- **Principe de proportionnalité** : seules des données agrégées/anonymisées sont analysées — jamais de verbatim
  individuel identifiable transmis à un tiers.

### 4.3 Contraintes techniques
- Stack légère : Python 3.10+, une seule dépendance LLM (anthropic ou mistralai), pas de framework web imposé.
- Doit pouvoir tourner en CLI pure, puis être exposé plus tard en API (FastAPI/Flask) pour être appelé par un
  webhook Make/n8n.
- Le prompt système impose une sortie JSON stricte (aucun texte libre autour) pour garantir un parsing fiable.

## 5. Critères de succès du PoC
- Exécution bout-en-bout en < 3 minutes en mode démo.
- JSON de sortie 100% valide et exploitable sans retouche manuelle.
- Lisibilité du README par un profil non-tech (RH, DG) en < 5 minutes.
- Démonstration explicite de la prise en compte RGPD/QVT dans le pipeline (pas juste dans le discours).
