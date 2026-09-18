# 📄 Documentation 🔄 Workflow Make — OptiPilot-Agent

Documentation technique du scénario Make qui orchestre le pipeline OptiPilot-Agent, depuis la saisie d'une directive par un responsable jusqu'à sa notification Slack et son archivage dans Google Sheets.

---

## 🎯 Vue d'ensemble

```
┌────────────────────────────┐
│  Formulaire Tally          │
│  (utilisable par non-tech) │
└─────────────┬──────────────┘
              │  Response soumise
              ▼
┌────────────────────────────┐
│  Module 1 — Tally          │
│  Watch New Responses       │
└─────────────┬──────────────┘
              │  { note: "..." }
              ▼
┌────────────────────────────┐
│  Module 2 — HTTP           │
│  POST /analyser (Render)   │
└─────────────┬──────────────┘
              │  JSON structuré
              ▼
┌────────────────────────────┐
│  Module 3 — JSON Parse     │
│  Data structure auto       │
└─────────────┬──────────────┘
              │
      ┌───────┴───────┐
      ▼               ▼
┌───────────┐   ┌────────────────┐
│  Module 4 │   │  Module 5      │
│  Slack    │   │  Google Sheets │
│  Notifie  │   │  Archive       │
└───────────┘   └────────────────┘
```

---

## 📦 Modules du scénario

### Module 1 — Tally : Watch New Responses

**Rôle** : capter chaque nouvelle réponse au formulaire Tally et déclencher le scénario.

| Paramètre  | Valeur                           |
| ---------- | -------------------------------- |
| App        | Tally                            |
| Trigger    | Watch New Responses              |
| Connection | Compte Tally (OAuth)             |
| Form ID    | `OptiPilot - Nouvelle directive` |

**Output** : un objet contenant le champ `note` (Variable name du formulaire Tally).

---

### Module 2 — HTTP : Make a request

**Rôle** : envoyer la note à l'API FastAPI déployée sur Render.

| Paramètre         | Valeur                                              |
| ----------------- | --------------------------------------------------- |
| URL               | `https://optipilot-agent-api.onrender.com/analyser` |
| Method            | `POST`                                              |
| Headers           | `Content-Type: application/json`                    |
| Body content type | `JSON (application/json)`                           |
| Body input method | `Direct`                                            |
| Body content      | voir ci-dessous                                     |

**Body content** :

```json
{
  "note": "{{escapeJSON(1.note)}}",
  "provider": "demo"
}
```

**Providers disponibles** :

- `demo` : rejoue un exemple figé (aucun appel LLM, aucun coût)
- `groq` : utilise Groq (`openai/gpt-oss-120b`) — nécessite `GROQ_API_KEY` sur Render
- `mistral` : utilise Mistral Large (hébergement UE) — nécessite `MISTRAL_API_KEY`

---

### Module 3 — JSON : Parse JSON

**Rôle** : transformer la réponse brute de l'API en champs mappables.

| Paramètre      | Valeur                                                  |
| -------------- | ------------------------------------------------------- |
| Data structure | `OptiPilotResult` (généré depuis un exemple de réponse) |
| JSON string    | `{{2.data}}` (ou `{{2.body}}`)                          |
| Strict         | No                                                      |

**Data structure** : générée automatiquement en collant un exemple de réponse API dans le Generator de Make.

**Champs exposés** :

- `meta.agent`, `meta.version`, `meta.provider`, `meta.processed_at`
- `strategic_analysis.pole_cible`, `.urgence`, `.complexite_technique`, `.gain_temps_estime`
- `strategic_analysis.risques_identifies[]`
- `cahier_des_charges_technique.objectif`, `.inputs[]`, `.processing[]`, `.outputs[]`
- `prompt_systeme_genere`
- `notification.canal`, `.destinataire`, `.titre`, `.message_vulgarise`
- `notification.actions_proposees[].label`, `.action_id`

---

### Module 4 — Slack : Create a Message

**Rôle** : notifier le responsable dans un canal Slack avec un message vulgarisé.

| Paramètre  | Valeur                         |
| ---------- | ------------------------------ |
| Connection | Slack (bot) — token `xoxb-...` |
| Channel    | `#optipilot-alerts`            |
| Blocks     | vide                           |
| Text       | voir ci-dessous                |

**Text** :

```
{{3.notification.titre}}{{newline}}{{newline}}

{{3.notification.message_vulgarise}}

Actions proposées :

• {{join(map(3.notification.actions_proposees; "label"); newline + "• ")}}{{newline}}

Bonne continuation à tous.
```

**Rendu Slack** :

```
Synthese Audit QVT prete a valider

Bonjour,

La synthese anonymisee de l'audit QVT par pole est prete pour le Codex.
Aucun nom ne sort nulle part, tout a ete verifie.

Vous pouvez valider directement ci-dessous, ou demander une relecture RH avant diffusion.

Actions proposées :

• Valider pour le Codex
• Demander relecture RH
• Reporter

Bonne continuation a tous.
```

---

### Module 5 — Google Sheets : Add a Row

**Rôle** : archiver chaque directive traitée dans un tableur, pour traçabilité.

| Paramètre                 | Valeur                                         |
| ------------------------- | ---------------------------------------------- |
| Connection                | Compte Google (OAuth)                          |
| Search Method             | By ID                                          |
| Spreadsheet ID            | `14hZJsGDaJTAQZ6JnFPJCkfN4uXfCMMMMYipmG--CZeM` |
| Sheet Name                | `Feuille 1` (ou nom exact de l'onglet)         |
| Table contains headers    | Yes                                            |
| Use column headers as IDs | Yes                                            |
| Unformatted               | Yes                                            |

**Mapping des colonnes** :

| Colonne        | Valeur                                |
| -------------- | ------------------------------------- |
| Date (A)       | `{{now}}`                             |
| Pole_cible (B) | `{{3.strategic_analysis.pole_cible}}` |
| Urgence (C)    | `{{3.strategic_analysis.urgence}}`    |
| Titre (D)      | `{{3.notification.titre}}`            |

---

## 💰 Coût du workflow

| Élément                     | Valeur                                   |
| --------------------------- | ---------------------------------------- |
| Plan Make                   | Gratuit                                  |
| Opérations par run          | 5 (Tally + HTTP + JSON + Slack + Sheets) |
| Quota mensuel gratuit       | 1 000 opérations                         |
| **Runs mensuels possibles** | **200 runs complets**                    |

Largement suffisant pour un PoC, une démo client, ou un usage interne à faible volume.

---

## 🔒 Sécurité

**Aucune clé API dans Make.** Toutes les clés (`GROQ_API_KEY`, `MISTRAL_API_KEY`) restent uniquement dans les variables d'environnement de Render.

**Sécurisation de l'API FastAPI** :

- Limite de taille sur le champ `note` (20 000 caractères) — anti-DoS
- Vérification de taille en entrée/sortie
- Refus d'écriture hors du répertoire courant (path traversal)
- Messages d'erreur génériques côté client — aucune fuite de secrets dans les logs publics
- Timeouts explicites sur les appels LLM

**Règle RGPD dans le prompt système** :

- Interdiction de citer un nom propre dans la sortie JSON
- Le champ `destinataire` doit être un canal ou un rôle, jamais une personne
- Le champ `message_vulgarise` commence par une formule neutre et se termine par une clôture collective

---

## 🧪 Tester le workflow

### Test rapide (mode demo)

1. Ouvrir le formulaire Tally
2. Remplir avec : `Il faut un rapport sur le stress au travail dans l'equipe Sales.`
3. Cliquer sur **Analyser**
4. Vérifier dans Make → History : 1 run, tous les modules verts
5. Vérifier Slack : le message doit apparaître
6. Vérifier Google Sheets : une ligne doit être ajoutée

---

## ⚠️ Pièges fréquents

| Piège                                      | Cause                              | Solution                                             |
| ------------------------------------------ | ---------------------------------- | ---------------------------------------------------- |
| **Webhook ne reçoit rien**                 | Scénario Make désactivé (OFF)      | Activer le toggle en bas à gauche                    |
| **`model_not_found` dans les logs Render** | Modèle Groq obsolète               | Mettre `GROQ_MODEL=openai/gpt-oss-120b`              |
| **`channel_not_found` dans Slack**         | Bot Make pas invité dans le canal  | Taper `/invite @OptiPilot` dans le canal             |
| **`Spreadsheet not found`**                | ID du Google Sheet incorrect       | Vérifier l'ID ou utiliser "By Path"                  |
| **`Sheet not found`**                      | Nom d'onglet différent             | Vérifier le nom exact en bas du Sheet                |
| **`references non-existing module`**       | Un module a été supprimé/réordonné | Re-sélectionner le bon champ dans le module concerné |
| **Cold start Render (50 s)**               | Free tier Render                   | Attendre, ou ping `/health` toutes les 14 min        |
| **Actions Slack collées**                  | Retours à la ligne absents         | Utiliser `{{newline}}{{newline}}` dans le Text       |

---

## 🔧 Variables d'environnement (côté Render)

| Variable             | Valeur                 | Obligatoire                                  |
| -------------------- | ---------------------- | -------------------------------------------- |
| `GROQ_API_KEY`       | `gsk_...`              | Pour `provider=groq`                         |
| `GROQ_MODEL`         | `openai/gpt-oss-120b`  | Recommandé (sinon valeur par défaut du code) |
| `MISTRAL_API_KEY`    | `...`                  | Pour `provider=mistral`                      |
| `MISTRAL_MODEL`      | `mistral-large-latest` | Optionnel                                    |
| `OPTIPILOT_PROVIDER` | `demo`                 | Optionnel (défaut : `demo`)                  |

---

## 📚 Fichiers liés

- [`README.md`](../README.md) — présentation du projet
- [`main.py`](../main.py) — logique LLM et CLI
- [`api.py`](../api.py) — API FastAPI exposée à Make
- [`samples/output_optipilot_result.json`](../samples/output_optipilot_result.json) — exemple de réponse API

---

_Documentation du workflow Make pour le PoC OptiPilot-Agent — Tech Ops / AI Builder._

```



## 📋 Ce que cette doc apporte

| Élément | Bénéfice |
|---|---|
| **Vue d'ensemble visuelle** | Compréhension immédiate du pipeline |
| **Config module par module** | Reproductible en 15 min |
| **Coût du workflow** | Rassure sur l'aspect financier |
| **Section sécurité** | Montre les garde-fous appliqués |
| **Pièges fréquents** | Gagne du temps au prochain bug |
| **Variables d'environnement** | Déploiement sans surprise |
| **Fichiers liés** | Navigation rapide dans le repo |

---
```
