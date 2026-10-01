# Laboratoires — cahiers de TP

Les fiches L00 à L19 définissent objectifs, mesures et questions, mais ne sont
pas toutes des procédures autonomes. Une reproduction exacte exige un dépôt
compagnon qui fige topologie, versions, commandes, configurations, sorties
attendues, tolérances et remise à zéro.

Trois parcours disposent désormais d'un compagnon exécutable et déterministe :
[latence et QoS](core_network_labs/notebooks/tp_latence_qos.ipynb),
[convergence et boucle transitoire](core_network_labs/notebooks/tp_convergence.ipynb)
et [BGP : validation d'origine et politique](core_network_labs/notebooks/tp_bgp_rov.ipynb).
Le [guide du compagnon cœur réseau](core_network_labs/README.md) donne les
entrées figées, commandes, sorties, tolérances, limites et remise à zéro.
Ces trois modèles ne configurent aucun équipement et n'exécutent pas une pile
TCP, OSPF ou BGP réelle. Ils constituent des contre-épreuves causales bornées ;
les essais de pile et de terrain demandent un environnement distinct.

Depuis le dossier du livre, `python3 -m core_network_labs.run_labs --check`
recalcule les sorties et vérifie leurs empreintes. La commande
`uv run --project machine_learning_labs --locked python core_network_labs/verify_notebooks.py --execute`
rejoue les trois notebooks sans les réécrire. Les autres fiches restent des
cahiers d'expérimentation à instancier avant de revendiquer une reproduction.

## L00 — Construire le banc

Outils recommandés :

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

## L01 — Du signal au débit utile

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

## L02 — Budget de latence

Mesurer :

- propagation approximative ;
- sérialisation ;
- RTT ;
- latence sous charge ;
- p50/p95/p99 ;
- gigue.

Construire un budget pour voix, vidéo et fichier.

## L03 — Files et QoS

Créer deux flux :

- voix simulée faible débit ;
- transfert saturant.

Comparer :

- FIFO ;
- file équitable ;
- classe prioritaire bornée.

Vérifier que la priorité ne devient pas une famine.

## L04 — Découverte

Capturer :

- ARP ;
- Neighbor Discovery ;
- DHCP ;
- DNS.

Identifier les caches, expirations et autorités.

## L05 — Dijkstra

Coder l’algorithme, modifier un coût, puis comparer au résultat OSPF.

Question : quelle partie du protocole n’apparaît pas dans l’algorithme ?

**Réponse attendue.** Dijkstra ne décrit ni la découverte des voisins, ni la
diffusion et l’âge des annonces, ni leur authentification, ni la détection des
pannes, ni les temporisateurs, ni la résolution des incohérences, ni
l’installation effective des routes. Il calcule seulement un arbre à partir
d’un graphe déjà disponible et cohérent.

## L06 — Convergence

Couper un lien OSPF/IS-IS et mesurer :

- détection ;
- recalcul ;
- installation ;
- perte applicative.

Ajouter un flux audio pour observer la différence entre convergence réseau et service perçu.

## L07 — TCP et bufferbloat

Comparer :

- RTT au repos ;
- RTT sous saturation ;
- CUBIC ;
- discipline de file ;
- perte et débit.

Ne conclure à la supériorité d’un mécanisme qu’après plusieurs profils.

## L08 — Média temps réel

Générer un flux RTP ou utiliser une application de laboratoire. Ajouter :

- délai ;
- gigue ;
- perte aléatoire ;
- perte par rafale.

Observer le tampon, les paquets tardifs et l’adaptation.

## L09 — Mini-Internet BGP

Créer plusieurs AS, politiques, peering et transit. Simuler dans le laboratoire :

- panne ;
- fuite ;
- annonce plus spécifique ;
- filtrage.

## L10 — TLS et identité

Lire une chaîne de certificats, tester un nom incorrect et une horloge fausse dans une VM.

Distinguer identité du serveur et autorisation applicative.

## L11 — Équilibrage et retries

Créer une dépendance lente. Faire varier :

- algorithme ;
- dépassement de délai ;
- retries ;
- concurrence ;
- circuit breaker.

Mesurer le travail utile.

## L12 — Mise à l’échelle automatique simulée

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

## L13 — Multicast

Exécuter l’émetteur et plusieurs récepteurs locaux. Perdre des paquets. Concevoir :

- numéro de séquence ;
- détection de trou ;
- réparation ;
- FEC conceptuelle ;
- contrôle d’accès.

## L14 — Anycast de laboratoire

Faire annoncer la même adresse par deux nœuds BGP. Retirer l’un et mesurer :

- convergence ;
- sessions ;
- chemin ;
- trou applicatif.

## L15 — DDIL

Créer une partition de vingt minutes :

- écrire localement ;
- stocker ;
- expirer certaines données ;
- réconcilier.

Documenter les conflits.

## L16 — PACE applicatif

Définir quatre profils de liaison et la fonction conservée à chaque niveau. Automatiser une bascule simulée et vérifier l’information utilisateur.

## L17 — Chaîne réseau

Modéliser, générer, valider, déployer progressivement, tester et annuler un changement FRRouting.

## L18 — Projet IA/réseau

Simuler des workers synchrones. Ajouter un retardataire et un incast. Tester :

- placement ;
- limitation ;
- hiérarchie ;
- taille de groupe ;
- reprise.

## L19 — SWaP-C, mini-drones et relais mobile

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

- A : ((1; 0{,}5; -4)), gain immédiat puis débordement ;
- B : ((0{,}2; 0{,}8; 1)), gain initial modeste puis service stable.

Le notebook exécutable se trouve dans
`machine_learning_labs/notebooks/tp_rl_retour_q_td.ipynb`.

### Déroulé

1. calculer les deux retours pour (gamma=0{,}9) ;
2. les interpréter comme (Q(s,A)) et (Q(s,B)) ;
3. calculer (V(s)) pour une politique équiprobable, puis les avantages ;
4. faire varier (gamma) et repérer le changement de classement ;
5. comparer l'erreur TD d'une transition en cours à celle d'une vraie
   terminaison ;
6. expliquer pourquoi une troncature temporelle conserve le bootstrap.

**Résultat attendu.** (Q(s,A)=-1{,}79), (Q(s,B)=1{,}73),
(V(s)=-0{,}03), avec des avantages de (-1{,}76) et (+1{,}76).
Le lecteur doit surtout expliquer pourquoi la récompense immédiate classe mal
les actions.

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
Q, rejeu d'expérience, réseau cible, exploration (epsilon)-greedy et arrêt du
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

### Déroulé

1. inspecter les valeurs renvoyées par `reset` et `step` ;
2. mesurer une politique aléatoire et l'heuristique `projected_queue` ;
3. entraîner le DQN sur CPU avec un seed fixé ;
4. évaluer les trois politiques sur les mêmes 40 seeds tenus à l'écart ;
5. comparer retour, paquets livrés et paquets perdus ;
6. transformer une indisponibilité de relais en masque d'action, et non en
   simple pénalité.

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

### 1. Geler le contrat avant le calcul

Consigner dans le compte rendu :

- identifiant de scénario, seed et empreinte de topologie ;
- connaissance de topologie autorisée à chaque contrôleur ;
- classes de trafic, capacités, délais et contraintes impératives ;
- ensemble de scénarios d'entraînement et ensemble tenu à l'écart ;
- KPI : livraison, latence, pertes, violations et coût de décision.

Une comparaison est invalide si un contrôleur voit une topologie, une demande
ou un budget différent.

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

### 4. Interpréter sans faux classement universel

Présenter un tableau par scénario et un agrégat sur l'ensemble tenu à l'écart.
Le minimum est : taux de livraison, latence, pertes, violations de contraintes
et temps de décision. Toute amélioration doit être rapportée à sa référence et
à son hypothèse d'information.

### Critères de réussite

- mêmes scénario, seed, topologie et demandes pour chaque comparaison ;
- ILP strict confirmé, sans repli silencieux ;
- artefacts vérifiés et provenance conservée ;
- au moins un scénario tenu à l'écart ;
- conclusion séparant performance, faisabilité et coût de calcul ;
- aucune phrase « PPO bat l'ILP » fondée sur un scénario unique.

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

<a id="choisir-variante-acp-reseaux"></a>

## Choisir une variante de l’ACP pour les réseaux

L’analyse en composantes principales (ACP, ou *principal component analysis*,
PCA) ne désigne pas une recette unique. La variante la plus pertinente dépend
de la structure des données et de l’objectif opérationnel :

| Données ou objectif | Variante d’ACP la plus adaptée |
|---|---|
| Détecter des pannes, des interférences ou de la congestion | **ACP robuste (RPCA)** |
| Analyser des séries temporelles de KPI | **ACP dynamique (DPCA)** |
| Prendre en compte la topologie des cellules ou des sites | **ACP régularisée par graphe** |
| Traiter des données site × KPI × temps × fréquence | **ACP tensorielle** |
| Modéliser des relations non linéaires | **ACP à noyau (*kernel PCA*)** |
| Obtenir des combinaisons de KPI interprétables | **ACP parcimonieuse (*sparse PCA*)** |
| Traiter des échantillons I/Q ou un CSI complexe | **ACP complexe / transformée de Karhunen–Loève** |

### Pourquoi l’ACP robuste est particulièrement pertinente

En fonctionnement normal, les KPI d’un réseau radio sont fortement corrélés :
RSRP, RSRQ et SINR ; débit et utilisation des PRB ; BLER et retransmissions ;
latence et pertes de paquets ; échecs de transfert de connexion et appels interrompus. Le
comportement nominal est donc approximativement de faible rang, tandis que les
défauts sont souvent rares et localisés. On peut l’écrire :

> **Modèle faible rang + anomalies parcimonieuses :** $X = L + S + E$.

où $L$ représente le comportement réseau normal et corrélé, $S$ les anomalies
parcimonieuses — cellule en panne, interférence ou congestion soudaine — et $E$
le bruit de mesure. La RPCA vise à limiter la déformation du sous-espace nominal
par des anomalies de grande amplitude. Cette séparation n'est pas garantie par
la seule rareté des incidents : elle suppose notamment que le faible rang ne
soit pas lui-même concentré sur quelques coefficients et que les anomalies ne
se confondent pas avec une composante de faible rang. Un changement de régime
ou un défaut aligné avec les modes nominaux peut rester ambigu.

### Recommandation pour la supervision au niveau cellule

Une architecture conceptuelle particulièrement adaptée est :

> **Recommandation : ACP robuste, dynamique et régularisée par graphe.**

L’ACP dynamique représente l’évolution temporelle, l’ACP robuste sépare le
comportement nominal des défauts, et la régularisation par graphe impose une
cohérence entre cellules voisines ou interférentes. Cette combinaison est une
orientation de conception, pas un algorithme universel prêt à déployer : ses
hyperparamètres et ses seuils doivent être validés sur des incidents réellement
annotés.

Pour le traitement du canal radio ou du CSI, l’ACP complexe appliquée à la
matrice de covariance du canal est plus naturelle. Ses composantes principales
correspondent aux modes propres dominants de propagation ou d’espace, ce qui la
rend utile pour le MIMO, la formation de faisceaux et la compression du canal.

Enfin, il faut standardiser les KPI et, de préférence, ajuster des modèles
distincts selon les régimes — heure chargée ou nuit, intérieur ou extérieur,
technologie et bande de fréquences. Sans cette précaution, l’ACP risque surtout
de redécouvrir le niveau de trafic, plutôt que les véritables défauts.

### SVD : fondement numérique de l’ACP

La décomposition en valeurs singulières (*singular value decomposition*, SVD)
est particulièrement pertinente en télécommunications radio. Elle constitue
aussi le fondement numérique naturel de l’ACP. Pour une matrice de KPI centrée
$X$ contenant $n$ observations :

> **Décomposition SVD :** $X = U\Sigma V^\top$.

Les colonnes de $V$ sont les directions principales, c’est-à-dire les
combinaisons de KPI définies par l’ACP. La matrice $U\Sigma$ contient les
observations projetées sur ces directions. La variance expliquée par la
composante $i$ vaut $\sigma_i^2/(n-1)$ : les valeurs singulières ordonnent donc
directement les modes dominants.

![Carte de lecture de la SVD : standardisation commune puis branches vers
l’ACP tronquée, la RPCA et le canal MIMO complexe, avec les normes utilisées
dans le notebook](assets/ml_svd_rpca_mimo_map.svg){width=98%}

#### Vocabulaire linéaire minimal pour lire le notebook

Soit \(K\in\mathbb{R}^{n\times p}\) la table brute de \(n\) observations et
\(p\) KPI. Le centrage retranche à chaque colonne sa moyenne. Comme les KPI
n’ont pas la même unité, le notebook les standardise aussi :

\[
X_{tj}=\frac{K_{tj}-\bar K_j}{s_j},
\]

où \(s_j\) est l’écart-type du KPI \(j\). Dans une tâche prédictive, moyenne et
écart-type doivent être ajustés sur l’entraînement seulement ; ici, le notebook
réalise une analyse descriptive d’un jeu synthétique unique.

Le **rang** est le nombre de directions linéairement indépendantes portées par
une matrice. Dans \(X=U\Sigma V^\top\), les colonnes de \(U\) et \(V\) sont
orthonormales et les valeurs singulières
\(\sigma_1\geq\sigma_2\geq\cdots\geq0\) occupent la diagonale de \(\Sigma\).
Garder les \(r\) premières donne la SVD tronquée
\(X_r=U_r\Sigma_rV_r^\top\), meilleure approximation de rang au plus \(r\)
pour la norme de Frobenius. Le notebook mesure son erreur relative par

\[
\frac{\lVert X-X_r\rVert_F}{\lVert X\rVert_F},
\qquad
\lVert X\rVert_F=\sqrt{\sum_{t,j}|X_{tj}|^2}.
\]

La norme spectrale \(\lVert X\rVert_2=\sigma_1\) mesure au contraire la plus
forte amplification linéaire. Ces deux normes ont donc des rôles distincts
dans le code : la première contrôle reconstruction et convergence, la seconde
initialise l’algorithme robuste.

<a id="rpca-code-numerique"></a>

#### Du modèle RPCA au code numérique

La version *Principal Component Pursuit* utilisée dans le notebook part de
\(X=L+S\) et résout le problème convexe

\[
\min_{L,S}\;\lVert L\rVert_*+\lambda\lVert S\rVert_1
\quad\text{sous la contrainte}\quad X=L+S.
\]

La norme nucléaire \(\lVert L\rVert_*=\sum_i\sigma_i(L)\) encourage un petit
nombre de modes, donc un faible rang. La norme
\(\lVert S\rVert_1=\sum_{t,j}|S_{tj}|\) encourage beaucoup de coefficients
nuls, donc des anomalies parcimonieuses. Le choix usuel repris dans le code est
\(\lambda=1/\sqrt{\max(n,p)}\). Ici \(E=X-L-S\) est exclusivement le résidu
numérique de la contrainte d'égalité, pas une estimation du bruit de mesure.
Le bruit dense injecté dans les KPI doit donc être absorbé par \(L\) ou \(S\).
Un modèle qui sépare explicitement ce bruit utiliserait, par exemple, une
contrainte \(\lVert X-L-S\rVert_F\leq\delta\), avec un budget de bruit justifié :
c'est une formulation de PCP stable distincte de celle exécutée dans ce TP.

Deux opérateurs expliquent les fonctions du notebook. Le seuillage doux agit
coefficient par coefficient :

\[
\operatorname{shrink}_\tau(z)=
\operatorname{sign}(z)\max(|z|-\tau,0).
\]

Le seuillage des valeurs singulières applique la même contraction au spectre :

\[
\mathcal D_\tau(M)=U\,\operatorname{diag}
\bigl(\max(\sigma_i-\tau,0)\bigr)V^\top,
\quad M=U\Sigma V^\top.
\]

Avec un multiplicateur \(Y\) et un paramètre de pénalité \(\mu\), l’algorithme
de Lagrangien augmenté alterne alors :

\[
L\leftarrow\mathcal D_{1/\mu}(X-S+Y/\mu),
\qquad
S\leftarrow\operatorname{shrink}_{\lambda/\mu}(X-L+Y/\mu),
\]

\[
E\leftarrow X-L-S,
\qquad
Y\leftarrow Y+\mu E.
\]

Le notebook augmente progressivement \(\mu\) et s’arrête lorsque
\(\lVert E\rVert_F/\lVert X\rVert_F\) passe sous la tolérance. Il transforme
ensuite chaque ligne parcimonieuse en score d’anomalie
\(a_t=\lVert S_{t,:}\rVert_2\). Les étiquettes d’incident servent uniquement à
calculer le rappel des plus grands scores après l’ajustement ; elles ne sont pas
utilisées pour construire \(L\) ou \(S\).

Le carnet publie aussi la fraction de coefficients non nuls de \(S\) et le
taux de fausses alertes de la règle naïve « un coefficient non nul suffit ».
Sur les données fixées du TP, environ 79 % des coefficients de \(S\) dépassent
\(10^{-6}\) : son support ne désigne donc pas les seuls incidents. Ce
contre-exemple rend visible l'absorption du bruit par la composante pénalisée.
Le rappel est mesuré au rang \(k=24\), nombre d'incidents connu par construction ;
il décrit un classement, pas un détecteur à seuil calibré. Une évaluation de
détection demanderait un seuil choisi sur une calibration séparée, puis
précision, rappel et fausses alertes sur un test indépendant.

#### Canal radio MIMO

Pour un canal MIMO complexe, on applique directement la SVD complexe à la
matrice de canal $H$ :

> **Décomposition du canal MIMO :** $H = U\Sigma V^{H}$.

Les colonnes de $V$ définissent les directions de précodage à l’émission,
celles de $U$ les directions de combinaison à la réception, et les valeurs
diagonales de $\Sigma$ la force de chaque flux spatial. La SVD transforme ainsi
le canal MIMO, sous les hypothèses du modèle, en sous-canaux spatiaux
indépendants. Elle est fondamentale pour la formation de faisceaux, le
multiplexage spatial, l’estimation du rang du canal et le calcul de capacité.

Dans le cas complexe, \(H^H\) est la transposée conjuguée de \(H\). Les matrices
\(U\) et \(V\) sont unitaires : \(U^HU=I\) et \(V^HV=I\). Le notebook vérifie
ces deux identités ainsi que la reconstruction
\(H=(U\Sigma)V^H\) avec une erreur relative de Frobenius proche de zéro.

Pour relier les valeurs singulières à la capacité, il suppose un bruit spatial
blanc normalisé, une connaissance parfaite du canal, une puissance répartie
également entre les \(n_t\) antennes d’émission et aucune optimisation par
*water-filling*. Un rapport signal sur bruit de \(\rho_{dB}\) décibels devient
\(\rho=10^{\rho_{dB}/10}\). La capacité spectrale synthétique est alors

\[
C=\sum_i\log_2\!\left(1+\frac{\rho}{n_t}\sigma_i^2\right)
=\log_2\det\!\left(I_{n_r}+\frac{\rho}{n_t}HH^H\right)
\quad\text{bit/s/Hz}.
\]

L’égalité vient de ce que les valeurs propres non nulles de \(HH^H\) sont
\(\sigma_i^2\). Le calcul `slogdet` du notebook évalue le logarithme du
déterminant de façon plus stable que `log(det(...))` et vérifie numériquement
que la somme par modes et la forme matricielle coïncident. Cette formule décrit
les hypothèses synthétiques du TP ; elle ne constitue pas à elle seule un
budget de liaison ou une prédiction de capacité terrain.

#### Variantes recommandées

| Données ou objectif | Variante adaptée |
|---|---|
| Compresser le CSI et extraire les modes propres MIMO | **SVD complexe tronquée** |
| Traiter de très grands jeux de données réseau | **SVD aléatoire (*randomized SVD*)** |
| Mettre à jour un modèle avec une télémétrie continue | **SVD incrémentale** |
| Détecter des anomalies ou des pannes | **SVD robuste / RPCA** |
| Traiter des données cellule × KPI × temps × fréquence | **Décomposition tensorielle**, analogue multilinéaire de la SVD |

En pratique, le choix peut se résumer ainsi :

> **MIMO ou CSI : SVD complexe.**
>
> **KPI réseau : SVD/ACP robuste, ou SVD tronquée incrémentale.**

La troncature doit être dimensionnée sur la variance utile et validée contre
les événements rares : une compression trop agressive peut justement supprimer
les signatures faibles que l’on cherche à détecter.

Le [carnet SVD radio reproductible](machine_learning_labs/notebooks/svd_radio.ipynb)
met ces calculs en pratique avec des KPI synthétiques, une RPCA et un canal MIMO
complexe. Il adapte le
[carnet de réduction dimensionnelle original](https://github.com/morard/ML-jpmorard-AE/blob/main/ml1/dim-reduc.ipynb)
sans présenter les données simulées comme une validation RF.

> **Vocabulaire.** La SVD est une décomposition matricielle ; SVG est un format
> graphique vectoriel. L’ACP peut servir à aligner ou compresser des formes
> vectorielles, mais cet usage n’a pas de signification radio particulière.

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

## Fiche de compte rendu commune

Chaque laboratoire répond aux sept questions :

1. problème ;
2. hypothèse ;
3. montage ;
4. mesure ;
5. résultat ;
6. explication ;
7. limite et généralisation.

---
