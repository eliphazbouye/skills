# Skills

Des skills [Claude Code](https://claude.com/claude-code) qui encadrent le travail d'un agent sur un projet, du plan jusqu'à la livraison, et qui gardent en mémoire, dans le dépôt, ce qui a été décidé, construit et appris.

Chaque skill corrige une façon précise dont le travail avec un agent déraille : il devine des décisions qu'on n'a jamais prises, coche une étape qui « devrait marcher », relit son propre code avec ses propres œillères, repart de zéro à chaque session, répète une erreur déjà faite ailleurs…

## Le cycle

```
  /feature pilote tout le cycle d'une fonctionnalité, dans son worktree, de scope à land
  /endurance coordonne plusieurs fonctionnalités en parallèle, un worktree chacune

  projet existant    besoin flou
        │                │
       map ──────────▶ scope ──▶ architect ──▶ build ──▶ review ──▶ verify ──▶ ship ──▶ land
  cartographier       cadrer    planifier      coder    vérifier   recette    PR       merge
                                  │  ▲           ▲         │          │
                                  ▼  │           └─────────┴──────────┘
                                 spike            corriger les problèmes trouvés
                           tester une question

  un bug : fix ──▶ review ──▶ ship ──▶ land
  en fin de session : remember ── en début : remember (reprise)
  à tout moment :  imprint (cohérence UI) · recover (session bloquée) · tidy (context/ à jour)
```

## Les skills

### `feature` : mener une fonctionnalité de bout en bout

**Quand :** tu veux emmener une fonctionnalité jusqu'au merge sans te demander quelle est la prochaine étape, ou reprendre une fonctionnalité là où elle en est.

**Ce qu'il fait :**
- Il lit l'état de la fonctionnalité dans `context/` (brief, build plan, problèmes ouverts, recette, PR) et en déduit l'étape en cours.
- Il lance le skill de cette étape, puis passe tout seul au suivant : `scope` → `architect` → `build` → `review` → `verify` → `ship` → `land`.
- Il ne s'arrête que pour ce qui te revient : répondre aux questions, valider le plan, trancher une décision imprévue, choisir quoi corriger, faire les vérifications manuelles, valider le texte de la PR, pousser et merger.
- Les problèmes renvoient à l'étape d'avant (`build`, puis re-review), jamais en les contournant.
- **Chaque fonctionnalité a sa branche et son worktree**, créés avant `scope` et prêts à l'emploi : fichiers locaux copiés, un port et une base de données propres au worktree, dépendances installées. Plusieurs fonctionnalités peuvent donc avancer en parallèle, une session chacune.
- Il affiche où en est la fonctionnalité (`scope ✓ · architect ✓ · ▶ build · …`). Quand la session devient longue, il propose de sauvegarder et de reprendre dans une session neuve avec `/feature <slug>`.

### `endurance` : le tech lead de plusieurs fonctionnalités en parallèle

**Quand :** plusieurs fonctionnalités avancent en même temps, chacune dans son worktree, ou quand tu veux savoir combien de temps prend une livraison et comment la raccourcir.

**Ce qu'il fait, depuis le worktree principal :**
- **Un tableau de bord** de toutes les fonctionnalités en cours : étape, propriétaire, worktree, PR, questions en attente, messages non lus, sous-agent en cours. Il peut aussi le publier en page web.
- **Les conflits, attrapés le plus tôt possible :**
  - entre les **plans**, dès qu'`architect` en écrit un (les fichiers que chaque plan prévoit de toucher) ;
  - entre les **branches** (fichiers modifiés des deux côtés, même numéro d'ADR) ;
  - en **fusionnant toutes les branches actives** dans un worktree temporaire et en lançant les tests, ce qui repère ce que git ne voit pas, comme une fonction renommée d'un côté et encore appelée de l'autre.
- **Les dépendances :** une fonctionnalité qui a besoin d'une autre part de sa branche (PR empilées), puis elle est rebasée et sa PR reciblée quand la première est mergée.
- **Une limite de travail en cours** (3 par défaut) : il recommande de finir une fonctionnalité avant d'en commencer une nouvelle.
- **Le travail long délégué :** `build`, les corrections, `verify` et les mises à jour de branche tournent en sous-agents d'arrière-plan, un par worktree.
  - Ils **communiquent entre eux** par un canal de messages partagé : chacun annonce ce qu'il change et qui touche les autres (une signature, un fichier, un schéma), et lit ses messages à chaque étape.
  - Moins de sous-agents sont lancés quand des questions s'accumulent.
- **Les décisions**, posées une à la fois, avec l'extrait de code concerné et l'impact de chaque option. Les décisions sur un même sujet venant de plusieurs fonctionnalités sont regroupées en une seule question.
- **La surveillance** (avec `/loop`) : CI rouge, nouveaux commentaires, PR prête à merger, sous-agent bloqué. Il t'envoie une notification quand on a besoin de toi.
- **La mesure du temps de livraison :**
  - la durée totale de chaque fonctionnalité, et le temps de chaque étape (travail actif, attente de ta réponse, reprises) ;
  - les durées de CI et de mise en production ;
  - des indicateurs de qualité à côté (problèmes 🔴, échecs de recette, bugs après livraison).
- **L'accélération :** tous les 3 merges, il repère l'étape qui prend le plus de temps et propose des changements ciblés (découper plus petit, tests et CI plus rapides, mise en production plus courte, moins d'attente). Il ne supprime jamais une vérification. Chaque changement retenu passe par le cycle complet, et ses effets sont mesurés sur la vitesse **et** sur la qualité.
- **Un bilan après chaque merge**, dont les causes de lenteur qui peuvent se reproduire deviennent des leçons de processus.
- **Les branches des autres :** une branche dont les commits sont d'une autre personne reste en lecture seule.

Il ne décide jamais à ta place et ne merge jamais sans ta demande. L'état est sur le disque : `/endurance` reconstruit tout dans n'importe quelle session.

### `map` : cartographier un projet existant

**Quand :** tu utilises ces skills sur un projet qui a déjà du code, et `context/` est vide ou n'est plus à jour.

**Ce qu'il fait :**
- Des sous-agents explorent le code en parallèle, en lecture seule : structure et frontières, données et intégrations, conventions, outillage.
- Il écrit `architecture.md` à partir de ce qu'il a trouvé, avec un chemin de fichier comme preuve pour chaque affirmation.
- Il propose des **ADR rétroactifs** pour les décisions visibles dans le code, et tu confirmes chacun.
- Il transforme les incohérences (deux façons de gérer les erreurs, par exemple) en questions : quelle façon est la bonne ?
- Il ajoute au `CLAUDE.md` les commandes du projet : test, lint, build…

Relancé plus tard, il signale les endroits où le code ne suit plus `architecture.md`. Il ne modifie jamais le code.

### `scope` : lever les zones d'ombre avant de concevoir

**Quand :** avant une fonctionnalité ou un projet dont la demande est floue (« ajoute des notifications », « fais-moi un CRM »), ou quand tu ne sais pas encore bien ce que tu veux.

**Ce qu'il fait :**
- Il reformule la demande et dresse la liste de tout ce qui n'est pas clair : le problème, les utilisateurs, ce qu'est un succès, les scénarios concrets, ce qui est dedans et dehors, les contraintes, les suppositions, les mots ambigus. Si la demande est déjà claire, il le dit et propose de passer directement à `architect`. Il vérifie aussi que ce que la demande suppose existe vraiment dans le code (« ajoute un lien dans le menu » quand il n'y a pas de menu, ce n'est pas clair).
- Si la demande est déjà une solution (« ajoute un bouton export CSV »), il demande une fois quel problème elle règle, seulement si la réponse peut changer ce qu'on construit.
- Il classe chaque zone d'ombre par **impact** : *forte* (change ce qu'on construit) ou *faible* (un détail). Il pose les zones fortes **une à la fois**, via AskUserQuestion, avec une réponse recommandée. Les détails sont réglés par lots de choix par défaut que tu valides d'un coup.
- Une réponse vague (« simple », « rapide », « les utilisateurs ») entraîne une relance : un exemple réel, un chiffre, le cas exact. Une contradiction est signalée et tranchée.
- Il note **qui a dit quoi**. Quand tu parles pour quelqu'un d'autre (« les commerciaux veulent… »), c'est une supposition non vérifiée, et la question est ajoutée à la liste *à demander à d'autres*. Une supposition technique dont tout dépend est signalée pour `/spike`.
- Toutes les 5 questions environ, il fait un **point** : ce qui reste, continuer, prendre ses choix par défaut pour les détails, ou faire une pause.
- Il écrit le brief **en brouillon dès le début**, avec la liste des zones d'ombre dedans, et le met à jour à chaque point et avant toute pause : une interview interrompue reprend là où elle s'est arrêtée (y compris via `remember`).
- Il s'arrête quand aucune zone forte n'est ouverte, te relit le brief, puis le finalise dans `features/<slug>/brief.md`. Pour un projet entier, c'est `project/brief.md`, avec un découpage en fonctionnalités dans l'ordre de construction. Il passe ensuite la main à `architect`, qui ne repose pas les questions déjà tranchées.

`review` vérifie ensuite que rien de ce que le brief exclut n'a été construit, et `tidy` repère les éléments reportés dont l'échéance est passée.

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

### `verify` : vérifier dans l'application qui tourne

**Quand :** après `review`, avant `ship`. Les tests sont verts, mais tu veux voir la fonctionnalité marcher pour de vrai.

**Ce qu'il fait :**
- Il lance l'application en local (jamais en production), puis déroule chaque scénario promis par le brief, les cas d'usage et les critères d'acceptation, par la vraie interface : navigateur, API ou CLI.
- Pour chaque scénario, il note ce qu'il a fait et ce qu'il a observé : capture d'écran, requête et réponse, sortie de commande.
- Il te confie une courte liste de vérifications manuelles pour ce qu'il ne peut pas juger seul (rendu, ressenti, appareil réel).
- Chaque échec devient un problème `V-n` dans le build plan, que `build` corrige. `ship` bloque tant que la recette n'est pas passée.

Il ne corrige rien lui-même.

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

### `land` : amener la PR jusqu'au merge

**Quand :** après `ship`, quand la CI échoue sur la PR, ou quand des commentaires de relecture arrivent.

**Ce qu'il fait :**
- **La CI :** il lit les logs, reproduit l'échec en local, puis corrige (en commençant par un test) ou prouve que le test est instable. Il ne désactive jamais un test pour passer au vert.
- **Les commentaires :** il classe chacun (à corriger, à répondre, désaccord, hors périmètre) et rédige les corrections et les réponses. Tu choisis lesquelles appliquer.
- Il ne pousse et ne publie qu'après ta validation, et ne merge que si tu le demandes, avec les checks verts et des approbations à jour.
- **Après le merge :**
  - il passe le build plan à `shipped` ;
  - il planifie la vérification du succès défini dans le brief ;
  - il propose en leçons ce que les relecteurs ont dû signaler ;
  - il nettoie la branche.

### `fix` : corriger un bug proprement

**Quand :** un bug est signalé, en production ou ailleurs, en dehors d'une fonctionnalité en cours de construction.

**Ce qu'il fait :**
- Il note précisément le symptôme, le comportement attendu, l'environnement et depuis quand ça arrive.
- **Il reproduit le bug avant de toucher au code**, idéalement avec un test qui échoue. S'il n'arrive pas à le reproduire, il s'arrête et demande ce qui manque.
- Il cherche la cause et non le symptôme, avec `git bisect` pour une régression, puis vérifie si la même erreur existe ailleurs dans le code.
- Il applique la plus petite correction qui fait passer le test, sans rien casser d'autre.
- Il complète la spec si elle était fausse ou muette sur ce cas, et propose une leçon si l'erreur peut se reproduire ailleurs.
- Il passe ensuite la main à `review`, puis à `ship`.

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

**Quand :** les tentatives échouent les unes après les autres et on ne sait plus pourquoi, ou quand `build` s'arrête après plusieurs échecs sur la même étape.

**Ce qu'il fait :**
- Il arrête de coder, liste tout ce qui a été essayé, puis repart des faits : les fichiers et les sorties relus, l'environnement vérifié (cache, image Docker, versions, variables d'environnement), et ce que `context/` a dit à la session.
- Il demande un deuxième avis à un sous-agent vierge, qui n'a jamais vu la conversation.
- Il cherche quel type de problème on a, car chacun demande une correction différente :
  - **un contexte pollué** : repartir des faits, éventuellement avec `/clear` puis une reprise via `remember` ;
  - **une supposition fausse** : revérifier les prémisses, y compris celles qui viennent de `context/` ;
  - **un vrai bug caché** : un test qui échoue, puis `git bisect` ;
  - **un plan impossible** : retour à `/architect`.
- Il peut mettre de côté les tentatives à moitié faites et revenir au dernier état qui marchait.
- Il enregistre les pistes écartées dans `memory.md`, corrige la source d'une prémisse fausse, et propose une leçon si la cause peut se reproduire ailleurs.

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
│   ├── brief.md               ← quoi et pourquoi, projet entier   (scope)
│   ├── architecture.md        ← modules, couches, frontières     (architect, map)
│   ├── memory.md              ← reprise, pistes écartées          (remember)
│   ├── ui-registry.md         ← patterns UI de référence          (imprint)
│   ├── lessons.md             ← erreurs déjà faites, en règles    (review)
│   └── adr/
│       └── 0001-<decision>.md ← une décision importante par fichier (architect, map, build)
├── fixes/
│   └── <slug>.md              ← un bug corrigé : cause, test, review, PR (fix)
└── features/                  ← un dossier par fonctionnalité, nom stable
    └── <slug>/
        ├── brief.md           ← quoi et pourquoi, sans zone d'ombre (scope)
        ├── use-cases.md       ← qui fait quoi                     (architect)
        ├── spec.md            ← quoi + critères d'acceptation     (architect, build)
        └── build-plan.md      ← étapes, statut, problèmes, recette, PR, suivi (architect, build, review, verify, ship, land)
```

**Les principes :**
- **Une seule source par information.** Les fichiers se citent par identifiant (`UC-1`, `AC-2`, `ADR-0003`, `L-004`) au lieu de se recopier.
- **Un ADR accepté s'impose.** Pour le changer, on écrit un nouvel ADR qui le remplace.
- **Les leçons sont des règles.** Elles sont relues avant de planifier, avant de coder et pendant les reviews.
- **Un problème a un état.** Dans le build plan, un problème trouvé en review (`R`) ou en recette (`V`) est `[ ]` ouvert, `[~]` corrigé mais pas encore confirmé, ou `[x]` confirmé : par `review` pour les `R`, par `verify` pour les `V`, jamais par celui qui l'a corrigé. S'il est barré, c'est que tu as choisi de ne pas le corriger, avec la raison.
- **Chaque skill commite ce qu'il écrit dans `context/`** (`chore(context): …`), séparément du code, pour que l'état voyage avec la branche.

## Travailler en parallèle : les worktrees

Chaque fonctionnalité vit sur sa branche (`feat/<slug>`, ou `fix/<slug>` pour un bug), dans son propre worktree git (par défaut `../<repo>.worktrees/<slug>`). Ses fichiers `context/` sont commités sur cette branche, donc deux fonctionnalités ne se marchent pas dessus. Les règles communes sont dans [`feature/worktrees.md`](feature/worktrees.md), et le script [`feature/scripts/wt.py`](feature/scripts/wt.py) les applique (voir plus bas).

**Les principes :**
- **La préparation d'un worktree** est décidée une fois, avant le premier worktree, puis notée dans la section `## Worktrees` du `CLAUDE.md` du projet : les fichiers à copier, l'installation, et comment isoler le port et la base de données. Chaque worktree reçoit ses propres ports, notés dans son build plan, pour que les tests et l'application de deux fonctionnalités ne se gênent jamais.
- **Chaque étape travaille dans le worktree de sa fonctionnalité**, y compris quand c'est la session d'`endurance` qui la lance. Tous les chemins et toutes les commandes y sont ramenés, et `endurance` vérifie après chaque étape que le worktree principal n'a pas été touché.
- **La mise à jour par rapport à la branche principale** se fait avant la PR, avant le merge et après chaque autre merge. Les conflits dans `context/` gardent les deux côtés. Les numéros d'ADR ou de leçons en double sont renumérotés, uniquement dans les fichiers de la branche. Les migrations sont remises dans l'ordre.
- **La clôture** (`Status: shipped`, suivi du succès, leçons) est commitée sur la branche juste avant le merge. Elle arrive donc sur la branche principale avec le merge, sans avoir à y passer.
- **Où reprendre** est noté dans le build plan de chaque fonctionnalité, pas dans `memory.md`.
- **Les fonctionnalités dépendantes s'empilent :** B part de la branche de A (`**Depends on:** feat/a` dans son plan), et sa PR vise `feat/a`. Quand A est mergée, B est rebasée sur la branche principale et sa PR reciblée.
- **Les sous-agents se parlent** par un canal de messages partagé. Ils y annoncent ce qu'ils changent et qui touche les autres (une signature de fonction, un fichier, un schéma, un nouvel ADR), de préférence avant de le commiter, et lisent leurs messages avant chaque étape. Un message informe mais ne remplace jamais un plan ni une de tes décisions.

### Le script `wt.py`

Il évite à l'agent de retaper des commandes git délicates, et il a été testé sur un vrai dépôt git (remote, merge en squash, conflits, ADR en double). Ses données partagées (ports attribués, messages, journal des étapes) vivent dans le dossier git commun du dépôt, sous `.git/endurance/`. Tous les worktrees les voient, et elles ne sont jamais commitées.

| Commande | Rôle |
|---|---|
| `wt.py create <slug> [--fix] [--from feat/<autre>]` | crée le worktree et la branche (sans suivre la branche principale) et attribue les ports ; `--from` empile la fonctionnalité sur une autre |
| `wt.py board [--gh] [--json]` | le tableau de bord : étape, avancement, problèmes ouverts, questions en attente, messages non lus, propriétaire, fichiers pas commités, sous-agent en cours, PR |
| `wt.py overlap` | les conflits en préparation : fichiers prévus par les plans, fichiers modifiés des deux côtés, même numéro d'ADR |
| `wt.py integrate --test "<cmd>"` | fusionne toutes les branches actives dans un worktree temporaire et lance les tests |
| `wt.py stale <worktree> <HEAD>` | dit si une review ou une recette est périmée (le code de la fonctionnalité a changé depuis) |
| `wt.py renumber <worktree> [--apply]` | renumérote les ADR et les leçons en double après une mise à jour, et liste les références à vérifier à la main |
| `wt.py mail post / read / list` | le canal de messages entre sous-agents |
| `wt.py event <slug> <étape> start/wait/resume/end/shipped` | le journal des étapes, qui sert à mesurer le temps |
| `wt.py metrics [<slug>] [--gh] [--markdown]` | la durée totale de livraison, le temps par étape, les reprises, les durées de CI et de mise en production, les indicateurs de qualité |
| `wt.py ports [list/release <slug>]` | les ports attribués |

## Mesurer et accélérer la livraison

Chaque étape s'inscrit dans le journal : quand elle commence, quand elle attend ta réponse, quand elle reprend, quand elle finit, et le merge. `wt.py metrics` en tire :
- **la durée totale** de chaque fonctionnalité, et la médiane sur les fonctionnalités livrées ;
- **par étape** : le temps de travail actif, le temps passé à attendre ta décision, les reprises (un deuxième round de review, une recette ratée) ;
- **le temps mort** entre deux étapes, quand personne n'a fait avancer la fonctionnalité ;
- avec `--gh` : **la durée de la CI** par workflow, et celle des **workflows de mise en production** sur la branche principale ;
- **à côté, la qualité** : rounds de review, problèmes 🔴, échecs de recette, bugs corrigés plus tard dans le code de la fonctionnalité.

`land` écrit ces chiffres dans la section *Timeline* du build plan au moment de la clôture. Tous les 3 merges, ou à ta demande (« combien de temps pour livrer ? », « livrer plus vite »), `endurance` repère l'étape qui prend le plus de temps et propose des changements ciblés :

| Là où le temps part | Exemples de changements |
|---|---|
| L'attente de tes réponses | de meilleures questions pendant `scope`, les décisions regroupées, les notifications |
| Un build long | des fonctionnalités plus petites, les tests proches du changement pendant une étape et la suite complète à la fin, des tests plus rapides |
| Les reprises | les problèmes récurrents transformés en règles de lint ou en tests, des critères d'acceptation plus clairs |
| Une CI longue | le cache, des jobs en parallèle, seulement les tests concernés sur les PR, lint et typecheck en premier |
| Du merge à la production | un déploiement déclenché au merge, des déploiements plus petits et plus fréquents, des migrations séparées du déploiement, un retour arrière en une commande |
| Le temps mort | la surveillance avec notifications, la limite de travail en cours |

**Même qualité, toujours :** aucune vérification n'est supprimée pour gagner du temps. Chaque changement retenu passe par le cycle complet (avec un `/spike` si le gain est incertain). Ses effets sont mesurés sur la vitesse **et** sur les indicateurs de qualité, et un gain qui dégrade la qualité est annulé ou retravaillé. Après chaque merge, un bilan transforme les causes de lenteur qui peuvent se reproduire en leçons de processus.

## Installation

Les skills personnels de Claude Code se trouvent dans `~/.claude/skills/<nom>/SKILL.md`. Clone le dépôt, puis crée un lien pour chaque skill :

```bash
git clone https://github.com/eliphazbouye/skills.git ~/projects/tools/skills
mkdir -p ~/.claude/skills
for s in ~/projects/tools/skills/*/; do
  [ -f "$s/SKILL.md" ] && ln -sfn "$s" ~/.claude/skills/"$(basename "$s")"
done
```

**Prérequis :** git, et python3 pour `wt.py` (bibliothèque standard uniquement). Le CLI `gh` est optionnel mais conseillé : `ship`, `land`, et l'état des PR et des CI dans `endurance` s'en servent.

Pour un seul projet, copie plutôt les dossiers voulus dans `.claude/skills/` à la racine de ce projet.

Ensuite, dans Claude Code, appelle un skill avec `/architect`, `/build`, `/review`… ou décris simplement ce que tu veux faire (« planifie cette feature », « où on en était ? ») : Claude choisit le bon skill d'après sa description.

## Démarrer

- **Nouveau projet :** `/scope` pour cadrer le projet, puis `/feature` sur la première fonctionnalité.
- **Projet existant :** `/map`, puis `/feature`.
- **Plusieurs fonctionnalités en même temps :** `/endurance` depuis le worktree principal.
- **Chaque fonctionnalité :** `/feature <nom>` crée son worktree et enchaîne tout : `scope` → `architect` (+ `spike` si besoin) → `build` → `review` → `verify` → `ship` → `land`. Chaque skill peut aussi s'appeler seul.
- **Un bug :** `/fix`, puis `/review` → `/ship` → `/land`.
- **Chaque session :** « où on en était ? » au début, `/remember` à la fin. Ou simplement `/feature <nom>`, qui reprend là où la fonctionnalité en est.
- **De temps en temps :** `/tidy` pour garder `context/` juste, `/map` pour vérifier que `architecture.md` suit encore le code.
