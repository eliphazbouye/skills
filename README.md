# Skills

Des skills [Claude Code](https://claude.com/claude-code) qui encadrent le travail d'un agent sur un projet, du plan jusqu'à la livraison, et qui gardent en mémoire, dans le dépôt, ce qui a été décidé, construit et appris.

Chaque skill corrige une façon précise dont le travail avec un agent déraille : il devine des décisions qu'on n'a jamais prises, coche une étape qui « devrait marcher », relit son propre code avec ses propres œillères, repart de zéro à chaque session, répète une erreur déjà faite ailleurs…

## Le cycle

```
  projet existant
        │
       map ──▶ architect ──▶ build ──▶ review ──▶ build ──▶ ship
   cartographier  planifier    coder    vérifier  corriger   livrer (PR)
                    │  ▲
                    ▼  │
                   spike           en fin de session : remember ── en début : remember (reprise)
             tester une question
             avant de décider

  à tout moment :  imprint (cohérence UI) · recover (session bloquée) · tidy (context/ à jour)
```

## Les skills

### `map` : cartographier un projet existant

**Quand :** tu utilises ces skills sur un projet qui a déjà du code, et `context/` est vide ou n'est plus à jour.

**Ce qu'il fait :**
- Des sous-agents explorent le code en parallèle, en lecture seule : structure et frontières, données et intégrations, conventions, outillage.
- Il écrit `architecture.md` à partir de ce qu'il a trouvé, avec un chemin de fichier comme preuve pour chaque affirmation.
- Il propose des **ADR rétroactifs** pour les décisions visibles dans le code, et tu confirmes chacun.
- Il transforme les incohérences (deux façons de gérer les erreurs, par exemple) en questions : quelle façon est la bonne ?
- Il ajoute au `CLAUDE.md` les commandes du projet : test, lint, build…

Relancé plus tard, il signale les endroits où le code ne suit plus `architecture.md`. Il ne modifie jamais le code.

### `architect` : décider avant de coder

**Quand :** avant une fonctionnalité qui comporte des décisions non prises.

**Ce qu'il fait :**
- Il lit `context/`, repère les décisions encore ouvertes (périmètre, données, auth, erreurs, interfaces…) et te les pose **une à la fois**, via AskUserQuestion. Chaque question a une option recommandée, justifiée par le code du projet.
- Il te présente le plan, puis, une fois que tu l'as validé, il écrit :
  - `features/<slug>/use-cases.md`, `spec.md` et `build-plan.md`, selon la taille de la fonctionnalité ;
  - un ADR par décision importante ;
  - une mise à jour d'`architecture.md` si la structure change.

Sur un projet neuf, il crée la structure `context/`. Sur un projet existant sans contexte, il propose de lancer `/map` d'abord. Il s'arrête une fois le plan écrit, et c'est `build` qui prend la suite.

### `build` : exécuter le plan

**Quand :** après `architect`, pour reprendre une implémentation interrompue, ou pour corriger les problèmes trouvés par une review.

**Ce qu'il fait :**
- Il déroule `build-plan.md` étape par étape. Pour chaque étape :
  - il écrit d'abord le test tiré du critère d'acceptation, et le voit échouer ;
  - il écrit le code et vérifie ;
  - il coche l'étape, seulement avec une preuve.
- Il s'arrête et te pose la question dès qu'une décision non prévue par le plan apparaît.
- Si le plan est faux, il propose de le modifier plutôt que de contourner en silence.
- Il lance les tests avant de commencer, pour ne pas confondre les échecs qui existaient déjà avec les nouveaux.

Les cases cochées du plan servent d'état : n'importe quelle session peut reprendre là où la précédente s'est arrêtée.

### `review` : vérifier avant de faire confiance

**Quand :** après `build`, avant de commiter, ou après des corrections (re-review).

**Ce qu'il fait :**
- La review est confiée à un **sous-agent vierge**, qui n'a jamais vu le raisonnement de l'auteur du code.
- Le sous-agent lance les tests, le typecheck et le lint.
- Il vérifie le code sous trois angles : respect du plan (chaque critère `AC-n`, les ADR), respect de l'architecture, capacité à tenir en production. Il vérifie aussi que les tests prouvent vraiment quelque chose.
- Chaque problème est prouvé par un extrait de code et classé 🔴 / 🟡 / ⚪.
- Les problèmes encore ouverts sont suivis dans `build-plan.md`.
- Les erreurs qui peuvent se reproduire ailleurs deviennent des **leçons** dans `lessons.md`. Une leçon qui revient souvent devient une règle de lint ou un test.

Il ne corrige rien sans ton accord.

### `spike` : répondre à une question technique en essayant

**Quand :** une décision ne peut pas se trancher en discutant (« cette librairie gère-t-elle le streaming dans notre runtime ? », « cette requête tient-elle sur 1 million de lignes ? »). Souvent appelé depuis `architect`.

**Ce qu'il fait :**
- Il formule **une seule question**, avec un critère de réussite et un budget (en tentatives ou en temps) fixés avant de commencer.
- Il expérimente dans un worktree ou une branche `spike/<slug>` isolée, qui n'est jamais mergée.
- Il rapporte des faits observés : commandes lancées, résultats, mesures, versions.
- Il enregistre la réponse là où vit la décision (l'ADR, la spec, ou les pistes écartées de `memory.md`), puis supprime le code.

### `ship` : livrer la fonctionnalité

**Quand :** la fonctionnalité est construite et relue, et elle est prête pour une PR.

**Ce qu'il fait :**
- **Il vérifie que tout est prêt**, et s'arrête sinon :
  - le build plan est à `done` ;
  - aucun problème 🔴/🟡 n'est ouvert ;
  - la dernière review est plus récente que le dernier changement de code ;
  - les tests, le typecheck, le lint et le build passent ;
  - le diff ne contient ni debug oublié, ni `.only`, ni secret.
- Il propose de nettoyer les commits qui n'ont pas encore été poussés.
- Il rédige les notes de migration (schéma, variables d'environnement, dépendances, changements cassants) et l'entrée du changelog.
- Il écrit la description de la PR à partir de la spec, des critères d'acceptation, des ADR et de la review.

Il ne pousse et n'ouvre la PR qu'après ta validation du texte.

### `remember` : garder le fil entre les sessions

**Quand :** en fin de session (« on s'arrête là »), ou en début de session (« où on en était ? »).

**En fin de session, il range ce qui s'est passé au bon endroit :**
- il coche les étapes du plan, après les avoir vérifiées dans le code ;
- il ajoute les nouvelles conventions à `architecture.md` ;
- il met tes préférences personnelles dans `CLAUDE.local.md` ;
- il ne garde dans `memory.md` que le reste : où reprendre, l'état git, les pistes écartées, les petites décisions.

Il te montre tout avant d'écrire.

**En début de session,** il relit tout ça, te résume où en est le projet et te propose la prochaine action.

### `imprint` : garder une UI cohérente

**Quand :** après plusieurs sessions de travail sur l'UI, quand les boutons, les espacements ou les couleurs commencent à diverger.

**Ce qu'il fait :**
- Il relève les patterns UI réellement utilisés et les écrit dans `ui-registry.md`, qui devient la référence.
- Il liste les endroits où le code s'en écarte.

Il ne modifie pas le code en masse.

### `recover` : sortir d'une session qui tourne en rond

**Quand :** les tentatives échouent les unes après les autres et on ne sait plus pourquoi.

**Ce qu'il fait :** il arrête de coder et cherche d'abord quel type de problème on a :
- **un contexte pollué** par des informations périmées : il faut repartir des faits ;
- **une supposition fausse** faite plus tôt : il faut revérifier les prémisses ;
- **un vrai bug caché** : il faut réduire et isoler le problème.

Chaque cas demande une correction différente, et il ne recommence à corriger qu'une fois le diagnostic posé.

### `tidy` : garder `context/` juste

**Quand :** toutes les quelques semaines, avant une grosse fonctionnalité, ou quand les agents semblent suivre des consignes périmées.

**Ce qu'il cherche :**
- des références cassées (`UC-n`, `AC-n`, `ADR-NNNN`, `L-NNN`) ;
- des ADR que le code ne respecte plus ;
- des build plans dont le statut ne correspond pas à la réalité ;
- des leçons en double, déjà vérifiées par un lint, ou qui reviennent sans avoir été automatisées ;
- un `memory.md` trop long ou périmé ;
- des commandes de `CLAUDE.md` qui n'existent plus.

**Ce qu'il fait des problèmes :**
- Il les classe en *faux*, *périmé* ou *superflu*.
- Il n'applique que les corrections que tu choisis.
- Il renvoie le reste au skill responsable (`/map`, `/architect`, `/build`…).

Il ne touche jamais au code.

## Le dossier `context/`

Les skills partagent un dossier `context/` à la racine du projet. Il est commité avec le code :

```
context/
├── README.md                  ← organisation du dossier
├── project/                   ← ce qui vaut pour tout le projet
│   ├── architecture.md        ← modules, couches, frontières     (architect, map)
│   ├── memory.md              ← reprise, pistes écartées          (remember)
│   ├── ui-registry.md         ← patterns UI de référence          (imprint)
│   ├── lessons.md             ← erreurs déjà faites, en règles    (review)
│   └── adr/
│       └── 0001-<decision>.md ← une décision importante par fichier (architect, map, build)
└── features/                  ← un dossier par fonctionnalité, nom stable
    └── <slug>/
        ├── use-cases.md       ← qui fait quoi                     (architect)
        ├── spec.md            ← quoi + critères d'acceptation     (architect, build)
        └── build-plan.md      ← étapes, statut, problèmes de review, lien de PR (architect, build, review, ship)
```

**Les principes :**
- **Une seule source par information.** Les fichiers se citent par identifiant (`UC-1`, `AC-2`, `ADR-0003`, `L-004`) au lieu de se recopier.
- **Un ADR accepté s'impose.** Pour le changer, on écrit un nouvel ADR qui le remplace.
- **Les leçons sont des règles.** Elles sont relues avant de planifier, avant de coder et pendant les reviews.

## Installation

Les skills personnels de Claude Code se trouvent dans `~/.claude/skills/<nom>/SKILL.md`. Clone le dépôt, puis crée un lien pour chaque skill :

```bash
git clone https://github.com/eliphazbouye/skills.git ~/projects/tools/skills
mkdir -p ~/.claude/skills
for s in ~/projects/tools/skills/*/; do
  [ -f "$s/SKILL.md" ] && ln -sfn "$s" ~/.claude/skills/"$(basename "$s")"
done
```

Pour un seul projet, copie plutôt les dossiers voulus dans `.claude/skills/` à la racine de ce projet.

Ensuite, dans Claude Code, appelle un skill avec `/architect`, `/build`, `/review`… ou décris simplement ce que tu veux faire (« planifie cette feature », « où on en était ? ») : Claude choisit le bon skill d'après sa description.

## Démarrer

- **Nouveau projet :** `/architect` sur la première fonctionnalité. Il crée `context/`.
- **Projet existant :** `/map`, puis `/architect`.
- **Chaque fonctionnalité :** `/architect` (+ `/spike` si une question doit être testée) → `/build` → `/review` → `/build` (corrections) → `/review` (re-review) → `/ship`.
- **Chaque session :** « où on en était ? » au début, `/remember` à la fin.
- **De temps en temps :** `/tidy` pour garder `context/` juste, `/map` pour vérifier que `architecture.md` suit encore le code.
