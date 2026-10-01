<a id="laboratoires-cahiers-de-tp"></a>

# Laboratoires — cahiers de TP

Les [quatre TP guidés du parcours de découverte](#premiers-tp-guides)
précèdent l’épilogue. Les fiches suivantes prolongent leurs questions selon
les outils et prérequis indiqués. Le [guide autonome](premiers_pas_reseaux_fr.md)
reste disponible dans le dépôt compagnon.

<a id="premiers-tp-guides"></a>

## Choisir ses premiers TP

| Question | Fiche | Support |
|---|---|---|
| Le plus grand débit gagne-t-il toujours ? | L02 / G01 | calcul et script |
| Que coûte une file plus grande ? | L03 / G02 | chronologie et script |
| Quand une adresse connue devient-elle fausse ? | L04 / G03 | cache simulé |
| Faut-il minimiser les relais ou le coût ? | L05 / G04 | graphe et script |

Les autres fiches L01 à L19 sont des **projets à construire** selon leurs
outils et prérequis. Un **notebook** est un document exécutable qui réunit
explications, code et résultats. Les trois notebooks cœur réseau portent sur
la latence/QoS, la stabilisation des chemins et les annonces échangées entre
réseaux autonomes (BGP). Ils apportent des modèles complémentaires ; ils n’exécutent
pas de pile TCP, OSPF ou BGP réelle. Les fiches avancées indiquent leur
support disponible et ce qui reste à réaliser. Le nombre de fiches ne
désigne donc pas un nombre identique de procédures autonomes.

<a id="l00-construire-le-banc"></a>

## L00 — Construire le banc

Pour les quatre premiers TP : une feuille ou Python 3.10 ou plus.

Pour les projets avancés, choisir les outils demandés par le montage :

- Linux ;
- Wireshark ;
- tcpdump ;
- iproute2 / `tc` ;
- iperf3 ;
- Python ;
- FRRouting ;
- containerlab ;
- GNS3 selon les images disponibles ;
- un dépôt Git.

Règles :

- employer des plages privées ou de documentation ;
- isoler les expériences ;
- ne pas annoncer de routes externes ;
- ne pas émettre de brouillage ;
- obtenir l’autorisation du réseau ;
- capturer uniquement le trafic du laboratoire ;
- documenter les hypothèses et limites.

<a id="l01-du-signal-au-débit-utile"></a>

## L01 — Du signal au débit utile

**Projet à construire.** Choisir un banc et documenter ses versions, commandes et résultats.

Mesurer :

- débit nominal ;
- débit TCP ;
- débit UDP ;
- surcharge ;
- taille de paquet ;
- pertes.

Question : où part la différence entre débit physique et utile ?

**Réponse attendue.** Elle est consommée par le codage physique, les gardes,
préambules et en-têtes, les accusés, la contention, les retransmissions, les
en-têtes de liaison/réseau/transport et les temps où le support ne transporte
pas la charge utile mesurée.

<a id="laboratoire-decouverte-latence"></a>

## L02 — Budget de latence

**TP guidé G01.** **Durée :** 20 minutes. **Prérequis :** multiplication et division ; Python 3.10 ou plus pour exécuter. Une feuille suffit pour chercher.

Dessinez deux liaisons : A à 1 Mbit/s et 2 ms de propagation ; B à 100 Mbit/s et 250 ms. Aucune file ni aucun en-tête n’est modélisé.

1. Prédisez la liaison la plus rapide pour 100 octets, puis pour 1 Mo décimal.
2. Calculez la durée nécessaire pour émettre les bits : taille en octets × 8 / débit en bits/s.
3. Ajoutez la propagation, dans la même unité.
4. Exécutez la commande et comparez vos valeurs.
5. Modifiez une taille dans une copie du script et cherchez le changement de classement.

**Pour interpréter après la recherche :** le petit message prend 2,8 ms sur A et 250,008 ms sur B ; le fichier prend 8 002 ms sur A et 330 ms sur B. Le plus grand débit ne gagne donc pas pour toutes les tailles.

**À conserver :** prédiction, deux calculs avec unités et une phrase expliquant le changement. **Limite :** une conversation comporte aussi des réponses, des traitements et des attentes. Ce calcul ne mesure pas une liaison réelle.

Depuis la racine du dépôt compagnon :

~~~bash
python3 -m core_network_labs.premiers_pas_reseaux_fr latence
~~~

Le script ne modifie aucun fichier ; relancez-le pour recommencer.

<a id="laboratoire-decouverte-files"></a>

## L03 — Files et QoS

**TP guidé G02.** **Durée :** 25 minutes. **Prérequis :** addition ; G01 conseillé.

Quatre paquets de 100 octets arrivent ensemble sur un lien à 8 000 bit/s. Trois paquets de fichier passent avant un paquet voix. Chaque transmission dure 100 ms. Une place en cours de service n’est pas comptée dans les places d’attente.

1. Dessinez les départs avec une seule place d’attente. Notez les paquets refusés.
2. Recommencez avec trois places. Le paquet voix arrive-t-il avant une échéance fictive de 250 ms ?
3. Prédisez l’effet d’une priorité donnée à la voix parmi les paquets en attente ; le paquet déjà en transmission continue.
4. Exécutez la commande. Expliquez chaque différence.
5. Imaginez des arrivées voix permanentes : quel autre risque faudrait-il tester ?

**Pour interpréter après la recherche :** la petite file perd deux paquets, dont la voix. La grande file livre les quatre, mais la voix termine à 400 ms. Avec priorité, elle termine à 200 ms. Une meilleure livraison ne garantit pas le respect de l’échéance.

**À conserver :** trois chronologies, pertes et délai de la voix. **Limite :** le petit lot fini ne démontre ni stabilité sous charge durable ni absence de famine. Le script réemploie le modèle de file du compagnon.

Depuis la racine du dépôt compagnon :

~~~bash
python3 -m core_network_labs.premiers_pas_reseaux_fr files
~~~

Le script ne modifie aucun fichier ; relancez-le pour recommencer.

<a id="laboratoire-decouverte-cache"></a>

## L04 — Découverte

**TP guidé G03.** **Durée :** 20 minutes. **Prérequis :** savoir lire une chronologie.

Un annuaire donne l’adresse 203.0.113.10 à t = 0 s. À t = 10 s, son adresse de référence devient 203.0.113.20. Un client conserve chaque réponse pendant 30 secondes, durée appelée TTL. L’expérience ne contacte aucun serveur.

1. Avant d’exécuter, écrivez la réponse attendue aux instants 0, 20 et 31 secondes.
2. Distinguez l’adresse de référence et celle que le cache rend au client.
3. Exécutez la commande, puis repérez les consultations de l’annuaire.
4. Dans une copie du script, remplacez la durée par 5 secondes. Que deviennent fraîcheur et nombre de consultations ?
5. Cherchez le résultat exactement à l’instant d’expiration.

**Pour interpréter après la recherche :** avec un TTL de 30 secondes, le client garde l’ancienne adresse à t = 20 s et obtient la nouvelle à t = 31 s. Le cache expire dès que sa limite est atteinte.

**À conserver :** une chronologie et une explication du compromis entre fraîcheur et consultations. **Limite :** ce modèle d’annuaire illustre un cache ; il n’exécute pas les protocoles réels de découverte et de résolution d’adresses présentés plus loin. Leur capture est un prolongement distinct.

Depuis la racine du dépôt compagnon :

~~~bash
python3 -m core_network_labs.premiers_pas_reseaux_fr decouverte
~~~

Le script ne modifie aucun fichier ; relancez-le pour recommencer.

<a id="laboratoire-decouverte-chemins"></a>

## L05 — Dijkstra

**TP guidé G04.** **Durée :** 25 minutes. **Prérequis :** addition ; lecture de Python facultative.

Dessinez quatre sommets A, B, C et D. Le lien direct A–D coûte 15 ; A–B, B–C et C–D coûtent chacun 2. Les liens fonctionnent dans les deux sens et les coûts s’additionnent.

1. Choisissez un chemin en minimisant le nombre de liens.
2. Choisissez-en un en minimisant le coût total.
3. Prédisez le résultat après suppression du lien B–C.
4. Exécutez la commande et comparez.
5. Si vous lisez Python, suivez la liste des candidats dans la fonction de Dijkstra. Sinon, énumérez les chemins sur papier.

**Pour interpréter après la recherche :** A–B–C–D coûte 6, contre 15 pour A–D. Après la coupure de B–C, le lien direct reste disponible.

**À conserver :** carte, deux critères et résultats avant/après coupure. **Limite :** Dijkstra suppose ici une carte disponible, cohérente et des coûts positifs. Il ne décrit ni l’échange des annonces ni leur vieillissement. La convergence OSPF appartient au second niveau.

Depuis la racine du dépôt compagnon :

~~~bash
python3 -m core_network_labs.premiers_pas_reseaux_fr chemins
~~~

Le script ne modifie aucun fichier ; relancez-le pour recommencer.

<a id="l06-convergence"></a>

## L06 — Convergence

**Projet à construire.** Choisir un banc et documenter ses versions, commandes et résultats.

Couper un lien OSPF/IS-IS et mesurer :

- détection ;
- recalcul ;
- installation ;
- perte applicative.

Ajouter un flux audio pour observer la différence entre convergence réseau et service perçu.

<a id="l07-tcp-et-bufferbloat"></a>

## L07 — TCP et bufferbloat

**Projet à construire.** Choisir un banc et documenter ses versions, commandes et résultats.

Comparer :

- RTT au repos ;
- RTT sous saturation ;
- CUBIC ;
- discipline de file ;
- perte et débit.

Ne conclure à la supériorité d’un mécanisme qu’après plusieurs profils.

<a id="l08-média-temps-réel"></a>

## L08 — Média temps réel

**Projet à construire.** Choisir un banc et documenter ses versions, commandes et résultats.

Générer un flux RTP ou utiliser une application de laboratoire. Ajouter :

- délai ;
- gigue ;
- perte aléatoire ;
- perte par rafale.

Observer le tampon, les paquets tardifs et l’adaptation.

<a id="l09-mini-internet-bgp"></a>

## L09 — Mini-Internet BGP

**Projet à construire.** Choisir un banc et documenter ses versions, commandes et résultats.

Créer plusieurs AS, politiques, peering et transit. Simuler dans le laboratoire :

- panne ;
- fuite ;
- annonce plus spécifique ;
- filtrage.

<a id="l10-tls-et-identité"></a>

## L10 — TLS et identité

**Projet à construire.** Choisir un banc et documenter ses versions, commandes et résultats.

Lire une chaîne de certificats, tester un nom incorrect et une horloge fausse dans une VM.

Distinguer identité du serveur et autorisation applicative.

<a id="l11-équilibrage-et-retries"></a>

## L11 — Équilibrage et retries

**Projet à construire.** Choisir un banc et documenter ses versions, commandes et résultats.

Créer une dépendance lente. Faire varier :

- algorithme ;
- dépassement de délai ;
- retries ;
- concurrence ;
- circuit breaker.

Mesurer le travail utile.

<a id="l12-mise-à-léchelle-automatique-simulée"></a>

## L12 — Mise à l’échelle automatique simulée

**Projet à construire.** Choisir un banc et documenter ses versions, commandes et résultats.

Écrire une boucle simple :

```python
desired = ceil(queue_depth / target_messages_per_worker)
```

Ajouter :

- délai de démarrage ;
- lissage ;
- plafond ;
- descente prudente.

Tracer la charge, la capacité et la queue. Observer les oscillations.

<a id="l13-multicast"></a>

## L13 — Multicast

**Projet à construire.** Choisir un banc et documenter ses versions, commandes et résultats.

Exécuter l’émetteur et plusieurs récepteurs locaux. Perdre des paquets. Concevoir :

- numéro de séquence ;
- détection de trou ;
- réparation ;
- FEC conceptuelle ;
- contrôle d’accès.

<a id="l14-anycast-de-laboratoire"></a>

## L14 — Anycast de laboratoire

**Projet à construire.** Choisir un banc et documenter ses versions, commandes et résultats.

Faire annoncer la même adresse par deux nœuds BGP. Retirer l’un et mesurer :

- convergence ;
- sessions ;
- chemin ;
- trou applicatif.

<a id="l15-ddil"></a>

## L15 — DDIL

**Projet à construire.** Choisir un banc et documenter ses versions, commandes et résultats.

Créer une partition de vingt minutes :

- écrire localement ;
- stocker ;
- expirer certaines données ;
- réconcilier.

Documenter les conflits.

<a id="l16-pace-applicatif"></a>

## L16 — PACE applicatif

**Projet à construire.** Choisir un banc et documenter ses versions, commandes et résultats.

Définir quatre profils de liaison et la fonction conservée à chaque niveau. Automatiser une bascule simulée et vérifier l’information utilisateur.

<a id="laboratoire-chaine-reseau"></a>

## L17 — Chaîne réseau

**Projet à construire — deux séances de 90 minutes au minimum.**
Prérequis : L05, L06 et administration d’un banc Linux isolé. Le dépôt ne
fournit pas ici de configuration FRRouting prête à déployer.

**Question :** comment vérifier puis annuler un changement de route ?
Commencez sur papier avec A–B–D comme chemin primaire et A–C–D comme secours.
Une modification augmente le coût de B–D. Définissez le chemin attendu
avant de choisir les commandes.

1. Figer la topologie, les adresses privées, les versions de FRRouting et les
   configurations initiales dans un dossier de travail.
2. Vérifier la connectivité initiale et conserver table de routage, captures
   utiles et mesure applicative de référence.
3. Préparer la configuration modifiée et sa configuration de retour.
4. Contrôler sa syntaxe avec la procédure de la version retenue, puis
   comparer le changement ligne par ligne.
5. Appliquer d’abord le changement à un seul équipement du banc.
6. Observer chemin, pertes et délai ; décider à l’avance du seuil d’arrêt.
7. Déclencher le retour arrière, puis vérifier le rétablissement du service,
   même si la commande d’annulation a réussi.
8. Recommencer en introduisant une erreur volontaire dans une copie de la
   configuration et expliquer où elle aurait dû être détectée.

**Livrables :** dessin annoté, versions, configurations avant/après,
chronologie, mesures et décision de poursuite ou d’arrêt.
**Réussite :** un autre lecteur peut distinguer intention, configuration
acceptée et effet observé. **Limite :** ce projet demande l’instanciation
du banc et des commandes adaptées à sa version ; le dessin seul ne valide
pas un déploiement.

<a id="l18-projet-iaréseau"></a>

## L18 — Projet IA/réseau

**Projet à construire.** Choisir un banc et documenter ses versions, commandes et résultats.

Simuler des workers synchrones. Ajouter un retardataire et un incast. Tester :

- placement ;
- limitation ;
- hiérarchie ;
- taille de groupe ;
- reprise.

<a id="l19-swap-c-mini-drones-et-relais-mobile"></a>

## L19 — SWaP-C, mini-drones et relais mobile

**Projet à construire.** Choisir un banc et documenter ses versions, commandes et résultats.

Construire un simulateur abstrait de cinq nœuds, sans émission radio réelle.

Chaque nœud possède :

- une énergie restante ;
- une puissance de veille, réception, émission et calcul ;
- une capacité de stockage ;
- une température ;
- une qualité de liaison variable ;
- un rôle possible : capteur, relais, nœud de calcul en périphérie ou passerelle.

Injecter :

- commande et télémétrie à échéance ;
- vidéo adaptative ;
- alertes ;
- fichiers différables ;
- une mise à jour multicast.

Comparer :

1. le meilleur lien seulement ;
2. un relais fixe ;
3. un relais tournant ;
4. une politique SWaP-aware avec hystérésis.

Mesurer l’effet utile, l’énergie par type de trafic, la gigue, les échéances manquées, la durée de vie du relais et les oscillations d’orchestration.

<a id="laboratoire-rl-retour-td"></a>

## L20 — Retour, Q, avantage et erreur TD

**Public :** première découverte du RL. **Durée :** 45 à 60 minutes.
**Prérequis :** Python élémentaire ; aucune connaissance de PyTorch.

Ce TP rend calculables les notions du chapitre avant d'introduire un réseau de
neurones. Deux relais produisent les récompenses suivantes :

- A : (1 ; 0,5 ; −4), gain immédiat puis débordement ;
- B : (0,2 ; 0,8 ; 1), gain initial modeste puis service stable.

Le notebook exécutable se trouve dans
`machine_learning_labs/notebooks/tp_rl_retour_q_td.ipynb`.

<a id="déroulé"></a>

### Déroulé

1. calculer les deux retours pour γ = 0,9 ;
2. les interpréter comme Q(s, A) et Q(s, B) ;
3. calculer V(s) pour une politique équiprobable, puis les avantages ;
4. faire varier γ et repérer le changement de classement ;
5. comparer l'erreur TD d'une transition en cours à celle d'une vraie
   terminaison ;
6. expliquer pourquoi une troncature temporelle conserve le bootstrap.

**Résultat attendu.** Q(s, A) = −1,79, Q(s, B) = 1,73,
V(s) = −0,03, avec des avantages de −1,76 et +1,76.
Le lecteur doit surtout expliquer pourquoi la récompense immédiate classe mal
les actions.

<a id="critères-de-réussite"></a>

### Critères de réussite

- les calculs passent les assertions du notebook ;
- terminaison et troncature ne sont pas confondues ;
- une pénalité de récompense n'est pas présentée comme une contrainte dure ;
- la conclusion contient une interprétation causale, pas seulement les nombres.

<a id="laboratoire-rl-dqn-relais"></a>

## L21 — DQN pour un choix de relais

**Public :** première pratique du deep RL. **Durée :** 75 à 90 minutes.
**Prérequis :** L20 et lecture de Python.

Le notebook `machine_learning_labs/notebooks/tp_rl_dqn_relais.ipynb` utilise un
environnement Gymnasium synthétique : deux files, deux relais, une capacité
variable et une limite externe de durée des épisodes. Il met volontairement le mécanisme à nu : réseau
Q, rejeu d'expérience, réseau cible, exploration ε-greedy et arrêt du
bootstrap lors d'une vraie terminaison seulement.

Le problème reste partiellement observable : le vecteur ne contient pas le
budget de pertes restant, alors que son épuisement provoque une terminaison.
Deux historiques peuvent donc présenter la même observation et la même action,
mais des probabilités de terminaison différentes. Le DQN sans mémoire est ici
une approximation sur les observations, pas une démonstration d'un état markovien
complet. Cette limite est commune aux trois contrôleurs.

La limite de durée interrompt la collecte d'une tâche qui pourrait continuer :
elle est traitée comme une troncature et conserve le bootstrap. Un horizon fini
intrinsèque à la tâche demanderait une autre spécification, avec le temps restant
dans l'état et une terminaison à son échéance.

Depuis `machine_learning_labs/` :

```bash
uv sync --python 3.12
uv run jupyter lab notebooks/
```

<a id="déroulé-1"></a>

### Déroulé

1. inspecter les valeurs renvoyées par `reset` et `step` ;
2. mesurer une politique aléatoire et l'heuristique `projected_queue` ;
3. entraîner le DQN sur CPU avec un seed fixé ;
4. évaluer les trois politiques sur les mêmes 40 seeds tenus à l'écart ;
5. comparer retour, paquets livrés et paquets perdus ;
6. transformer une indisponibilité de relais en masque d'action, et non en
   simple pénalité.

<a id="critères-de-réussite-1"></a>

### Critères de réussite

- le DQN et les baselines sont comparés sur des graines appariées, avec
  intervalles de confiance et publication explicite des compromis observés sur
  le retour, les pertes et le débit sur le banc
  fourni ;
- l'heuristique reste visible lorsqu'elle domine un KPI ;
- la courbe d'entraînement n'est pas utilisée comme résultat de test ;
- aucun résultat synthétique n'est extrapolé à un déploiement réel.

Le contrôle automatisé exécute les deux notebooks dans un répertoire temporaire
et vérifie que les versions suivies restent sans sorties :

```bash
uv run python verify_notebooks.py --execute
uv run pytest -q
```

<a id="laboratoire-rl-ppo-gnn-ilp"></a>

## L22 — PPO-GNN, ILP et protocole de référence

**Public :** lecteur ayant terminé L21. **Durée :** environ 120 minutes hors
temps de calcul. **Surface opérateur :** `apps/routing_training_project`.

Ce TP ne remplace pas le DQN par « un algorithme plus fort ». Il change
d'échelle méthodologique : PPO-GNN est une politique acteur-critique apprise,
l'ILP est une référence d'optimisation centralisée, et le contrôleur
OLSRv2-like est une référence protocolaire. Ils ne partagent pas les mêmes
hypothèses ; la comparaison n'a de sens que sur un contrat d'entrée et de
preuve explicite.

<a id="geler-le-contrat-avant-le-calcul"></a>

### 1. Geler le contrat avant le calcul

Consigner dans le compte rendu :

- identifiant de scénario, seed et empreinte de topologie ;
- connaissance de topologie autorisée à chaque contrôleur ;
- classes de trafic, capacités, délais et contraintes impératives ;
- ensemble de scénarios d'entraînement et ensemble tenu à l'écart ;
- KPI : livraison, latence, pertes, violations et coût de décision.

Une comparaison est invalide si un contrôleur voit une topologie, une demande
ou un budget différent.

<a id="construire-le-plan-guidé"></a>

### 2. Construire le plan guidé

Dans la page de planification, ajouter :

1. `Train learned route scorer • PPO-GNN` ;
2. `Compute optimization reference • ILP` ;
3. `Compare controllers • OLSRv2-like baseline vs PPO-GNN`.

La configuration prédéfinie ILP impose `allow_ilp_fallback=false` : une solution non optimale
échoue au lieu d'être étiquetée « référence ». La comparaison de contrôleurs
est optionnelle et désactivée par défaut ; l'activer explicitement. Sauvegarder
ou sélectionner une configuration prédéfinie **n'exécute pas** le calcul : lancer ensuite l'action
WORKFLOW prévue par l'application.

Pour un exercice de bout en bout, utiliser un modèle de confiance produit par
l'étape PPO-GNN. Quand ce modèle n'est pas disponible, travailler sur une paire
d’instantanés déjà produite et déclarer cette limite ; ne jamais substituer un
modèle factice à une preuve d'inférence.

<a id="vérifier-les-artefacts"></a>

### 3. Vérifier les artefacts

L'allocation ILP canonique est attendue sous :

`routing_training/pipeline/trainer_fcas_routing_ilp/allocations_steps.json`

La valider depuis la racine du dépôt :

```bash
python3 apps/routing_training_project/tools/verify_allocations.py \
  --alloc-file routing_training/pipeline/trainer_fcas_routing_ilp/allocations_steps.json
```

Conserver aussi les allocations candidate/référence, les résumés de routage,
les manifests de modèle et les preuves du scénario. Une sortie sans provenance
de topologie ou sans correspondance décision-réalisation ne vaut pas résultat.

<a id="interpréter-sans-faux-classement-universel"></a>

### 4. Interpréter sans faux classement universel

Présenter un tableau par scénario et un agrégat sur l'ensemble tenu à l'écart.
Le minimum est : taux de livraison, latence, pertes, violations de contraintes
et temps de décision. Toute amélioration doit être rapportée à sa référence et
à son hypothèse d'information.

<a id="critères-de-réussite-2"></a>

### Critères de réussite

- mêmes scénario, seed, topologie et demandes pour chaque comparaison ;
- ILP strict confirmé, sans repli silencieux ;
- artefacts vérifiés et provenance conservée ;
- au moins un scénario tenu à l'écart ;
- conclusion séparant performance, faisabilité et coût de calcul ;
- aucune phrase « PPO bat l'ILP » fondée sur un scénario unique.

<a id="sources-pédagogiques-et-reproductibilité"></a>

### Sources pédagogiques et reproductibilité

Les notebooks sont des créations originales, inspirées par la progression de
FIDLE mais modernisées pour Gymnasium. Les versions consultées, les liens et la
prudence de licence sont consignés dans `machine_learning_labs/SOURCES.md` ; le
verrou `machine_learning_labs/uv.lock` fige l'environnement reproductible.

<a id="laboratoire-ml-classification-rare"></a>

## Laboratoire L23 — Classification rare sans fuite de test

**Question.** Une exactitude élevée suffit-elle lorsque l'événement important
est rare et que le coût d'une omission dépasse celui d'une fausse alerte ?

Le notebook `machine_learning_labs/notebooks/tp_ml_classification_rare.ipynb`
construit trois partitions disjointes et identifiables. Il ajuste le modèle sur
l'entraînement, compare les seuils exclusivement sur la validation avec un coût
pondéré, puis évalue le test selon le protocole final déclaré. Les empreintes
SHA-256 identifient les partitions ; le champ `test_open_count = 1` est une
assertion de protocole, pas un compteur d'accès instrumenté. Ni ce champ ni les
empreintes ne prouvent l'absence de consultations ou de réglages lors d'exécutions
antérieures. L'ordre ajustement → sélection → évaluation reste à vérifier dans
le code et à respecter par le lecteur.

Depuis `machine_learning_labs/`, exécuter :

```bash
uv sync --locked
uv run --locked jupyter nbconvert --to notebook --execute \
  --inplace notebooks/tp_ml_classification_rare.ipynb
uv run --locked python run_benchmarks.py
uv run --locked python build_manifest.py
uv run --locked python verify.py --execute-notebooks
```

Le compte rendu doit comparer le seuil par défaut au seuil choisi, publier la
matrice de confusion, la précision, le rappel et le coût pondéré, puis expliquer
pourquoi le test ne peut pas servir à sélectionner le seuil. Un résultat est
recevable seulement si les partitions sont disjointes, si le seuil retenu diffère
de `0,5`, si le coût de validation baisse, et si le test n'est ouvert qu'une fois.

Les résultats DQN du même paquet suivent une règle analogue : cinq graines
d'entraînement, quarante épisodes appariés par politique, intervalles de confiance
sur les écarts par rapport à la méthode de référence, filtrage des actions qui refuse d’agir en cas d’incertitude et manifeste
d'empreintes. La méthode de référence de charge projetée ne lit que l'observation publiée ;
elle n'accède plus à l'état privé de l'environnement.

<a id="laboratoire-rl-dqn-contraint"></a>

## Laboratoire L24 — DQN contraint par les pertes

**Question.** Une pénalité de perte plus forte à l'entraînement peut-elle
supprimer la régression de paquets perdus observée en L21, tout en conservant
un gain de retour et zéro action interdite ?

L'expérience `machine_learning_labs/run_constrained_dqn_experiment.py` balaie
les pénalités d'entraînement (4, 6, 8, 12, 16). Chaque configuration réutilise
les cinq graines d'entraînement canoniques et les quarante scénarios tenus à
l'écart. L'évaluation conserve toujours la récompense canonique avec une
pénalité de 4 : les retours restent donc comparables entre configurations.

La porte est fixée avant lecture du résultat. Par rapport à la politique
aléatoire disponible, la borne supérieure à 95 % de la différence de pertes
doit être inférieure ou égale à zéro, la borne inférieure à 95 % du gain de
retour doit être strictement positive, et le filtre doit appliquer zéro action
interdite. Une hypothèse rejetée reste un résultat valide du laboratoire.

| Pénalité d'entraînement | Différence de retour vs aléatoire | Différence de pertes vs aléatoire | Porte |
|---:|---:|---:|:---:|
| 4 | +8,02 ± 4,81 | +3,65 ± 3,39 | rejetée |
| 6 | +3,11 ± 1,25 | -1,72 ± 0,24 | franchie |
| 8 | +3,22 ± 1,28 | -1,82 ± 0,07 | franchie |
| 12 | +2,04 ± 2,05 | -1,72 ± 0,21 | rejetée |
| 16 | +2,81 ± 0,90 | -1,81 ± 0,10 | franchie |

La sélection lexicographique retient la pénalité 8 : elle améliore le retour
de 3,22 ± 1,28 et réduit les pertes de 1,82 ± 0,07 face à l'aléatoire. Elle ne
domine toutefois pas robustement l'heuristique de charge projetée : +0,22 ±
1,28 de retour et +0,01 ± 0,07 paquet perdu. Cette heuristique, plus simple,
reste donc la préférence pour ce scénario synthétique. La conclusion ne vaut
ni preuve RF, ni performance terrain, ni autorité de déploiement.

Ces intervalles sont exploratoires : les mêmes observations servent à choisir
la pénalité parmi cinq candidates et à décrire son résultat. Les intervalles à
95 % calculés candidate par candidate ne garantissent pas une couverture à
95 % après cette sélection. Une conclusion confirmatoire demanderait de figer
la configuration, puis de l'évaluer sur de nouvelles graines ; une affirmation
sur l'algorithme d'apprentissage demanderait aussi de nouveaux entraînements.
La règle de sélection fixée à l'avance ne remplace pas cette confirmation.

Depuis `machine_learning_labs/` :

```bash
uv run python run_constrained_dqn_experiment.py
uv run python run_constrained_dqn_experiment.py --check
uv run python verify.py
```

Le JSON retient les exécutions, les différences appariées, les intervalles, la
porte et la conclusion. Le CSV fournit les lignes auditables par graine ; le
schéma et `manifest.json` lient ces artefacts au code qui les a produits.

<a id="laboratoire-rl-robustesse-decalage"></a>

## Laboratoire L25 — Robustesse sous décalage

**Question.** Le DQN à pénalité 8 retenu en L24 domine-t-il robustement
l'heuristique de charge projetée lorsque les conditions d'exploitation
s'écartent du banc nominal ?

Le candidat est gelé avant l'expérience : cinq modèles sont réentraînés avec
les mêmes graines et la configuration L24, uniquement sur le scénario nominal.
Aucun seuil, poids ou hyperparamètre n'est ajusté après lecture des scénarios
décalés. Chaque régime réutilise les quarante graines d'évaluation appariées :

- arrivées plus concentrées, à demande moyenne inchangée ;
- indisponibilités de relais prolongées ;
- files réduites de dix à six paquets ;
- asymétrie de service déplacée entre relais et phases.

Un défi composite combine rafales, petites files, service déplacé et
indisponibilités alternées. Son empreinte est fixée avant l'évaluation ; il est
ouvert une fois et n'intervient ni dans la sélection ni dans un nouvel
entraînement.

La porte de pire cas reprend le niveau de confiance de L24, mais compare cette
fois à la méthode de référence `projected_queue` : borne supérieure à 95 % de la différence
de pertes inférieure ou égale à zéro, borne inférieure à 95 % du gain de retour
strictement positive et zéro action interdite, dans chaque régime.

| Régime | Différence de retour vs charge projetée | Différence de pertes vs charge projetée | Porte |
|---|---:|---:|:---:|
| contrôle nominal | +0,22 ± 1,28 | +0,01 ± 0,07 | rejetée |
| arrivées en rafales | +0,37 ± 0,32 | -0,13 ± 0,25 | rejetée |
| indisponibilités prolongées | 0,00 ± 0,00 | 0,00 ± 0,00 | rejetée |
| capacité réduite | +4,46 ± 5,47 | +0,71 ± 0,94 | rejetée |
| asymétrie de service déplacée | +1,36 ± 2,75 | +0,22 ± 0,12 | rejetée |
| défi composite scellé | -0,34 ± 0,89 | +0,09 ± 0,23 | rejetée |

Toutes les exécutions appliquent zéro action interdite. Sous arrivées en
rafales, le gain de retour est positif à 95 %, mais la réduction moyenne des
pertes reste inconclusive. Avec les indisponibilités prolongées, le masque ne
laisse qu'une action autorisée à chaque phase : les politiques deviennent
identiques, ce qui sépare correctement autorité de décision et performance.
Le défi composite ne révèle aucun avantage du DQN.

L25 ne prouve pas que l'heuristique est universellement supérieure ; il rejette
la supériorité robuste du DQN gelé sur ce périmètre synthétique. En l'absence de
gain robuste et compte tenu de sa simplicité, l'heuristique reste la préférence
pour ces scénarios. Aucune extrapolation RF, terrain ou production n'est admise.

Depuis `machine_learning_labs/` :

```bash
uv run python run_l25_robustness_experiment.py
uv run python run_l25_robustness_experiment.py --check
uv run python verify.py
```

Le JSON conserve les cinq entraînements gelés, les résultats par régime, les
différences appariées, les portes, l'empreinte et le compteur d'ouverture du
défi. Le CSV, le schéma et `manifest.json` rendent l'ensemble auditable.

<a id="laboratoire-rl-abstention-desaccord"></a>

## Laboratoire L26 — Abstention sur désaccord

**Question.** Le désaccord entre les cinq DQN de L25 permet-il de détecter les
décisions fragiles et de se replier assez tôt sur l'heuristique de charge
projetée pour éviter les régressions sous décalage ?

Le panel reste gelé : mêmes cinq graines, pénalité d'entraînement 8 et scénario
nominal. À chaque décision, les cinq modèles votent parmi les actions
autorisées. Le DQN majoritaire agit seulement si sa part des votes atteint le
seuil ; sinon, le contrôleur s'abstient et applique l'heuristique de charge
projetée. Trois seuils sont fixés avant exécution : 0,6 (majorité simple), 0,8
(quatre voix sur cinq) et 1,0 (unanimité).

Le taux d'accord n'est pas une probabilité calibrée de correction. Il mesure
seulement le désaccord de cinq entraînements du même modèle synthétique. La
porte demande, face au repli lui-même, zéro action interdite, une borne
inférieure à 95 % de la différence de retour supérieure ou égale à zéro et une
borne supérieure à 95 % de la différence de pertes inférieure ou égale à zéro.
Les intervalles sont calculés sur les quarante graines d'évaluation appariées,
pour le panel gelé.

La sélection utilise seulement le contrôle nominal et les quatre décalages
déclarés. Elle minimise d'abord le nombre de régimes qui échouent, puis la pire
borne supérieure de pertes, maximise la pire borne inférieure de retour et
préfère enfin le seuil le plus élevé. Le défi final combine, sous une nouvelle
empreinte, rafales décalées, files de sept paquets, service déplacé et
indisponibilités alternées ; il est ouvert une fois après la sélection.

| Seuil d'accord | Régimes déclarés en échec | Taux moyen de repli | Pire borne sup. de pertes | Pire borne inf. de retour |
|---:|---:|---:|---:|---:|
| 0,6 | 4 sur 5 | 0,00 % | +0,83 | -0,24 |
| 0,8 | 4 sur 5 | 7,74 % | +0,48 | -0,33 |
| 1,0 | 3 sur 5 | 20,22 % | +0,48 | -3,72 |

L'unanimité est donc sélectionnée avant ouverture du défi, sans franchir la
porte sur tous les régimes déclarés. Son détail reste nécessaire pour ne pas
confondre moyenne favorable et non-régression démontrée :

| Régime | Différence de retour vs repli | Différence de pertes vs repli | Taux de repli | Porte |
|---|---:|---:|---:|:---:|
| contrôle nominal | 0,00 ± 0,00 | 0,00 ± 0,00 | 18,33 % | franchie |
| arrivées en rafales | +0,34 ± 0,67 | -0,05 ± 0,07 | 28,70 % | rejetée |
| indisponibilités prolongées | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 % | franchie |
| capacité réduite | +1,16 ± 0,86 | -0,10 ± 0,12 | 27,57 % | rejetée |
| asymétrie de service déplacée | -2,41 ± 1,30 | +0,25 ± 0,23 | 26,52 % | rejetée |
| défi final tenu à l'écart | +0,04 ± 0,05 | 0,00 ± 0,00 | 3,93 % | rejetée |

Toutes les exécutions appliquent zéro action interdite. L'abstention réduit
certaines régressions moyennes, mais ne certifie pas la non-régression : les
bornes de pertes restent légèrement positives sous rafales et capacité réduite,
l'asymétrie déplacée dégrade les deux objectifs, et le gain du défi final est
inconclusif. L'heuristique de charge projetée reste donc la préférence sur ce
périmètre. Ce résultat ne calibre pas l'incertitude, ne mesure pas le coût de
l'ensemble et n'autorise aucune extrapolation RF, terrain ou production.

Depuis `machine_learning_labs/` :

```bash
uv run python run_l26_abstention_experiment.py
uv run python run_l26_abstention_experiment.py --check
uv run python verify.py
```

Le JSON conserve le panel, les votes agrégés, les décisions de repli, les
différences appariées, la règle de sélection et le défi final. Le CSV fournit
les lignes par graine ; le schéma et `manifest.json` lient les artefacts au code
qui les a produits.

<a id="laboratoire-rl-garde-support"></a>

## Laboratoire L27 — Garde de support nominal

**Question.** Une distance au support observable nominal, ajoutée à l'unanimité
de L26, peut-elle détecter les décisions fragiles que le seul désaccord des DQN
n'a pas interceptées ?

Le moniteur ne voit ni état privé ni résultat futur. Sa référence réunit les
observations de quarante trajectoires nominales aléatoires et quarante
trajectoires nominales de l'heuristique. Après déduplication, elle contient 288
vecteurs. Pour chaque observation, le score est la distance euclidienne au plus
proche vecteur de référence, dans l'espace déjà normalisé de l'environnement.

Les graines de référence 100 à 139 réutilisent ici des conditions initiales
d'entraînement : les cinq graines de modèle 7, 19, 31, 43 et 59 engendrent,
sur 180 épisodes par modèle, des graines d'environnement allant de 7 à 238
selon `graine_modèle + indice_épisode`. Cette réutilisation est déclarée et
admise pour construire le support nominal ; elle n'est pas une évaluation
indépendante. Le contrat distingue ces rôles et vérifie les graines de chaque
épisode, plutôt que les seuls germes des modèles. Des graines distinctes ne
garantissent d'ailleurs pas des observations distinctes dans ce simulateur fini.

Quarante nouvelles graines par politique, disjointes de la référence, des
entraînements et de l'évaluation, calibrent le seuil au quantile supérieur 95 %
du score maximal par épisode. Le seuil obtenu vaut 0,10 et signale 2,5 % des
épisodes de calibration. Aucun régime décalé ni défi final n'intervient dans ce
calcul.

La correction de cette déclaration est conservée dans
`machine_learning_labs/results/l27_seed_contract_correction.json`, avec
l'empreinte et la révision du reçu initial. Elle ne modifie ni les observations
retenues ni les résultats numériques et ne correspond pas à un nouvel entraînement.

L'autorité suit alors une cascade fixée avant l'évaluation : hors support,
repli immédiat vers l'heuristique ; dans le support, action DQN seulement si les
cinq modèles sont unanimes ; sinon, même repli. La porte reprend la
non-régression à 95 % de L26 sur retour, pertes et action interdite, dans tous
les régimes. Elle exige en plus un bénéfice de Pareto strict dans au moins un
régime déclaré, afin qu'un contrôleur qui se replie toujours ne soit pas compté
comme un progrès utile.

| Régime | Différence de retour vs heuristique | Différence de pertes vs heuristique | Repli hors support | Autorité DQN | Porte |
|---|---:|---:|---:|---:|:---:|
| contrôle nominal | 0,000 ± 0,000 | 0,000 ± 0,000 | 0,00 % | 81,67 % | franchie |
| arrivées en rafales | +0,340 ± 0,670 | -0,050 ± 0,071 | 0,94 % | 70,42 % | rejetée |
| indisponibilités prolongées | 0,000 ± 0,000 | 0,000 ± 0,000 | 50,00 % | 50,00 % | franchie |
| capacité réduite | 0,000 ± 0,000 | 0,000 ± 0,000 | 100,00 % | 0,00 % | franchie |
| asymétrie de service déplacée | -0,005 ± 0,009 | 0,000 ± 0,000 | 65,28 % | 27,61 % | rejetée |
| défi final tenu à l'écart | 0,000 ± 0,000 | 0,000 ± 0,000 | 100,00 % | 0,00 % | franchie |

Toutes les exécutions appliquent zéro action interdite. Par rapport à
l'unanimité seule de L26, la garde récupère 2,41 ± 1,31 de retour et réduit les
pertes de 0,25 ± 0,23 dans le régime d'asymétrie déplacée. Elle neutralise aussi
le régime de capacité réduite et le nouveau défi en revenant entièrement à
l'heuristique. Ces protections ne constituent toutefois aucun bénéfice propre
face au repli qui les fournit.

Le régime en rafales révèle la limite centrale : ses observations ponctuelles
restent presque toutes proches du support nominal, alors que leur séquence
change. La garde ponctuelle ne franchit donc pas la porte sur tous les régimes
et ne démontre aucun bénéfice de Pareto strict. L'heuristique demeure la
préférence. La distance n'est ni une probabilité calibrée de correction, ni une
preuve OOD opérationnelle ; le banc ne couvre ni temporalité longue, ni coût du
moniteur, ni RF, terrain ou production.

Depuis `machine_learning_labs/` :

```bash
uv run python run_l27_support_guard_experiment.py
uv run python run_l27_support_guard_experiment.py --check
uv run python verify.py
```

Le JSON conserve les graines disjointes, l'empreinte de la référence, la
calibration, les distances, les décisions d'autorité et de repli, les
différences appariées et le défi final. Le CSV fournit les lignes par graine ;
le schéma et `manifest.json` lient les artefacts au code qui les a produits.

<a id="laboratoire-chiffrement-homomorphe"></a>

## L28 — Agréger des mesures sans les déchiffrer

**Durée indicative : 45 minutes.** Prérequis : Python et arithmétique modulo
un entier. Le support est autonome, en bibliothèque standard, sans donnée
réelle ni accès réseau.

**Question :** comment additionner trois compteurs chiffrés sans connaître
leurs valeurs ni la clé privée ?

1. Prédire la somme et la moyenne des mesures synthétiques 12, 18 et 30.
2. Exécuter le code ci-dessous et repérer les rôles : producteurs, calculateur
   muni de la seule clé publique, destinataire autorisé à déchiffrer.
3. Vérifier la somme 60, la moyenne 20 calculée après déchiffrement et la somme
   pondérée $2\times12+18=42$.
4. Chiffrer 12 avec un autre aléa ; comparer les chiffrés puis les messages
   déchiffrés.
5. Expliquer le résultat 77 pour $200+200$ modulo 323 et en déduire une
   contrainte sur les plages de valeurs.
6. Montrer que publier les sommes de deux groupes emboîtés peut révéler le
   compteur d'un site. Expliquer pourquoi l'homomorphisme ne l'empêche pas.

Depuis la racine du dépôt compagnon :

~~~bash
python3 -m chiffrement_homomorphe_labs.tp_paillier_agregation_fr
python3 -m chiffrement_homomorphe_labs.tp_paillier_agregation_fr --check
python3 -m unittest chiffrement_homomorphe_labs.test_paillier_agregation
~~~

**Preuve attendue :** JSON de l'expérience, prédictions, calcul modulaire
commenté et distinction entre confidentialité, intégrité et publication des
résultats. Les tests parcourent tous les messages du petit domaine ainsi
que des additions avec dépassement.

**Limite essentielle :** les facteurs 17 et 19 et les aléas fixes rendent ce
code impropre à toute protection de données. C'est un exemple arithmétique
original de Paillier partiellement homomorphe, pas un système FHE ni une
mesure de performance de la cryptographie actuelle.

**Prolongement :** choisir un exemple officiel OpenFHE ou Microsoft SEAL,
décrire son circuit, ses paramètres, sa précision et le coût complet. Une
exécution du jouet ne valide pas ce prolongement.

<a id="fiche-de-compte-rendu-commune"></a>

## Fiche de compte rendu commune

Chaque laboratoire répond aux sept questions :

1. problème ;
2. hypothèse ;
3. montage ;
4. mesure ;
5. résultat ;
6. explication ;
7. limite et généralisation.
