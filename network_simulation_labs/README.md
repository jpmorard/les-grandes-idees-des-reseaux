# Laboratoires reproductibles de simulation réseau

Ce paquet est un support pédagogique **entièrement synthétique, déterministe,
hors ligne et non productif**. Il ne contient aucune trace client ou opérateur,
n'établit aucune preuve de déploiement et ne doit jamais être présenté comme une
validation terrain.

Il dépend uniquement de la bibliothèque standard Python. Aucun téléchargement,
simulateur externe, accès réseau, privilège ou commande système n'est requis.
Les neuf notebooks demandent seulement un environnement Jupyter pour afficher
leurs tableaux de bord ; leurs cellules de calcul restent en bibliothèque
standard et n'exécutent ni FlowSynth, ni Scapy, ni commande externe.

Leur contrat **self-contained** est testé, pas seulement déclaré : chaque
notebook est exécuté deux fois depuis un répertoire temporaire vide. Code,
fixtures, SVG/audio et exports data URI résident dans le `.ipynb`; une
dépendance cachée à un fichier du dépôt ferait échouer le contrôle. Python et
un noyau Jupyter restent les deux prérequis d'exécution.

## Neuf TP guidés : obtenir un résultat visible en une heure au plus

Ces notebooks sont des vues pédagogiques du banc ; ils ne modifient pas ses
cinq familles de benchmark :

- `notebooks/mini_fanet_reroutage.ipynb` — **45 minutes**, pour étudiant,
  alternant ou technicien débutant. Quatre drones, une rupture, trois secondes
  de trou noir, une route de secours et un tableau de bord SVG relient portée,
  route installée, PDR, délai et convergence. Le SPF miniature n'est ni AODV,
  ni OLSR, ni un modèle PHY/MAC ou de vol ;
- `notebooks/tp_voix_flowsynth.ipynb` — **60 minutes**, pour étudiant
  paquet/VoIP, analyste cyber débutant ou novice QoS. Un signal vocal
  procédural est encodé en PCMU, découpé en trames de 20 ms, transporté par des
  en-têtes RTP pédagogiques puis dégradé par perte et gigue. Le notebook permet
  d'écouter avant/après et exporte un DSL FlowSynth téléchargeable ;
- `notebooks/tp_detective_reseau.ipynb` — **60 minutes**, pour étudiant,
  technicien ou NetOps débutant. Le contrat pédagogique est **prédire,
  mesurer, falsifier, diagnostiquer, transférer** sur quatre scénarios cachés :
  congestion par capacité, bufferbloat, pertes radio-like et trou noir MTU. Un
  tableau de synthèse SVG et un rapport d'incident court rendent le raisonnement
  causal observable et transférable. Règle de sortie : **jamais un verdict sur un seul KPI** ;
  chaque diagnostic propose une contre-expérience corrective ;
- `notebooks/tp_capture_replay.ipynb` — **60 minutes**, pour étudiant,
  technicien, analyste cyber ou NetOps débutant. Un vrai PCAP synthétique est
  construit en mémoire, inspecté puis traité : anonymiser les identifiants ne
  doit modifier ni ordre ni horodatage relatif. Un tableau SVG et des artefacts
  téléchargeables rendent visibles timing, fidélité et transformations. Le plan
  inerte ne sait pas émettre. Règle : **capturer n'autorise pas à rejouer** ;
  autoriser une capture et autoriser une injection sont deux décisions
  distinctes ;
- `notebooks/tp_discovery_reseau.ipynb` — **60 minutes**, pour étudiant,
  technicien, analyste cyber ou NetOps débutant. Le passif exploite des
  observations synthétiques ; l'actif reste un
  choix autorisé seulement simulé. La réconciliation MAC–IP–nom–service relie
  les réponses sans en faire une identité certaine. Le tableau SVG et les
  exports expliquent confiance, fraîcheur, contradictions, angles morts et
  budget de sondes. Règle : **non découvert ne signifie pas absent** ;
- `notebooks/tp_dns_resolution.ipynb` — **60 minutes**, pour étudiant,
  technicien, NetOps ou analyste cyber débutant. Un **résolveur récursif** suit
  hors ligne un **autoritatif**, une **délégation**, un CNAME et leur **TTL** ;
  le **cache négatif** distingue **NXDOMAIN**, **NODATA** et **SERVFAIL**, puis
  l'apprenant observe un cache périmé. Une waterfall SVG, une trace et un
  rapport téléchargeables imposent la conclusion : **réponse DNS ≠ connectivité
  applicative** ;
- `notebooks/tp_dhcp_bail.ipynb` — **60 minutes**, pour étudiant, technicien,
  NetOps ou analyste cyber débutant. Une fixture binaire et synthétique déroule
  **DORA** — **Discover**, **Offer**, **Request**, **ACK** —, le **bail**, **T1**,
  **T2**, renouvellement, rebinding et expiration. Broadcast/unicast, **relais
  DHCP**, `giaddr`, options masque/routeur/DNS/bail, absence d'Offer, NAK,
  **pool épuisé** et option incohérente sont comparés dans un SVG, une trace et
  un rapport téléchargeables ;
- `notebooks/tp_sous_reseau_passerelle.ipynb` — **60 minutes**, pour étudiant,
  technicien ou NetOps débutant. `/24` et `255.255.255.0`, AND bit à bit,
  **adresse réseau**, **broadcast**, `/31`, `/32` et **même sous-réseau** mènent
  à une vraie décision de table : **préfixe le plus long**, route connectée ou
  **passerelle par défaut**, puis ARP/ND du **prochain saut**. Le miroir IPv6,
  le SVG et trois incidents séparent aussi gateway, routeur, NAT, DNS et
  pare-feu ;
- `notebooks/tp_modulation_symboles.ipynb` — **60 minutes**, pour étudiant,
  technicien radio ou NetOps débutant. L'**ordre de modulation** \(M\), les
  **bits par symbole** \(\log_2(M)\), le **nombre de symboles**, le
  **bourrage**, le **baud** et le bit/s sont calculés sur un exemple complet.
  Étiquetage de Gray, **symbole OFDM**, **élément de ressource**, pilote, préfixe
  cyclique, couche MIMO et **échantillon I/Q** restent distincts. Le SVG relie
  aussi **Es/N0**, **Eb/N0**, constellation, EVM, BLER et MCS.

FlowSynth ne produit ni la voix, ni l'encodage PCMU, ni les intervalles de
20 ms, ni la perte, ni le jitter buffer. Il compile seulement la conversation
UDP et ses payloads en fixture paquet. Le notebook ne l'exécute pas, n'émet
aucun paquet et ne prétend pas réaliser un appel SIP/RTP conforme.
Le TP Capture/Replay n'ouvre aucune interface et ne sait pas exécuter son plan
de rejeu. Le TP Discovery ne sniffe ni ne scanne : il compare uniquement des
fixtures locales et un budget de sondes hypothétiques. Toute acquisition,
injection ou découverte active sur un réseau réel exige un périmètre et une
autorisation propres. Le TP DNS n'envoie aucune requête et ne consulte aucun
résolveur, serveur autoritatif ou service réel. Le TP DHCP ne diffuse aucun
Discover et ne contacte aucun client, relais ou serveur réel.
Le TP Sous-réseau/Gateway ne change ni adresse, ni route, ni table de voisins :
ses décisions et son plan d'exécution restent des objets locaux inertes.
Le TP Modulation ne pilote ni SDR, ni radio, ni générateur de signaux : points
I/Q, grille OFDM et métriques sont des objets mathématiques locaux.

## Ce qui est mesuré

- une file `M/M/1/K` rejouée par événements discrets (arrivées et départs), avec
  débit, pertes, utilisation, moyenne, p95 et temps de vidange ;
- les altérations d'un flux de paquets : délai, gigue, perte, duplication et
  réordonnancement observé ;
- une convergence de routage par rejeu d'événements, dont la fenêtre transitoire
  de trou noir avant application par le plan de contrôle ;
- le calibrage d'un modèle analytique sur un sous-ensemble d'apprentissage puis
  son évaluation sur une trace synthétique tenue à l'écart, avec un point OOD ;
- la **génération seulement** d'un plan d'émulation inerte. Ses actions sont des
  tableaux `argv`, `execution_allowed` vaut toujours `false`, et aucun chemin de
  code ne sait exécuter une commande privilégiée.

Les résultats utilisent les cinq graines fixes `7, 19, 43, 101, 211`. Chaque
agrégat stochastique publie le nombre d'essais, la moyenne, l'écart-type
d'échantillon, la demi-largeur IC95 approximative, le minimum et le maximum. Le
fichier de résultats conserve aussi les essais unitaires et les constats
négatifs ; il ne masque donc ni la variance des queues ni l'échec de couverture
du modèle calibré hors distribution.

## Exécution exacte

Depuis le répertoire du livre
`Les_Grandes_Idees_des_Reseaux_Edition_1.0` :

```bash
python3 -m network_simulation_labs.run_labs --check
python3 -m network_simulation_labs.verify
python3 -m unittest discover -s network_simulation_labs/tests -v
python3 tools/check_network_notebooks.py
```

Pour régénérer volontairement les artefacts après une modification revue :

```bash
python3 -m network_simulation_labs.run_labs --write
python3 -m network_simulation_labs.verify --write-manifest
python3 -m network_simulation_labs.verify
```

La régénération écrit seulement `results/*.json` et `manifest.json`. Elle
n'exécute aucune action décrite dans le plan d'émulation.

## Contrats et provenance

- `datasets/` contient quatre jeux de données explicitement marqués
  `synthetic=true`, avec générateur, description et licence `CC0-1.0` ;
- `schemas/` publie les enveloppes JSON Schema 2020-12 des entrées, résultats et
  du plan inerte ;
- `contracts.py` applique les contraintes détaillées en mode fail-closed : clés
  inconnues, valeurs hors domaine, noms injectables et chemins traversants sont
  refusés ;
- `results/benchmark_results.json` est la preuve reproductible locale, pas une
  preuve opérationnelle ;
- `manifest.json` couvre tous les fichiers publiés par taille et SHA-256, hors
  lui-même et caches d'exécution.

Le vérificateur reparcourt les contrats, recalcule tous les résultats, inspecte
l'AST Python et les cellules des notebooks pour interdire commandes, accès
réseau et écritures, contrôle l'absence de liens symboliques et compare le
manifeste. Le contrôle notebook exécute chaque TP deux fois en mémoire et exige
des sorties riches identiques. Les tests de régression incluent JSON malformé,
traversée de chemin, métacaractères de shell, interface non sûre, champ
`execute` inconnu et scénario de file non stable.

## Limites à conserver dans toute citation

Les distributions sont choisies pour l'enseignement, le graphe est minuscule,
les intervalles IC95 utilisent l'approximation normale sur cinq graines et le
modèle `M/M/1` ne représente ni trafic auto-similaire, ni files multiples, ni
ordonnancement réel. Le plan `ip`/`tc` n'est ni testé sur un noyau Linux ni
autorisé à être appliqué. Une expérience terrain exige des données gouvernées,
un environnement isolé autorisé, des contrôles de sécurité, des répétitions plus
nombreuses et une revue indépendante.

Le TP FANET reste un graphe géométrique minuscule sans radio ni protocole RFC.
Le TP voix emploie un signal procédural, un codec PCMU pédagogique et un en-tête
RTP minimal : il ne mesure ni MOS/PESQ/POLQA, ni qualité de conversation, ni
performance temps réel. L'écoute illustre un mécanisme ; elle n'est pas une
validation perceptuelle. Le TP Détective réseau emploie des observations
synthétiques et des règles de décision didactiques : son tableau SVG et son
rapport ne sont ni une capture terrain, ni l'exécution d'un protocole réel, ni
une preuve qu'un diagnostic identique s'applique en production. Le PCAP du TP
Capture/Replay est synthétique ; son anonymisation est un exercice borné, pas
une garantie de désidentification, et la fidélité calculée ne prouve aucun
replay réel. L'inventaire Discovery est une fusion de fixtures : confiance et
fraîcheur sont des indicateurs pédagogiques, pas une preuve d'exhaustivité ni
une autorisation de scanner.
Le TP DNS modélise un résolveur récursif, un autoritatif, la délégation, le
TTL, le cache positif, le cache négatif, CNAME, NXDOMAIN, NODATA et SERVFAIL à
partir de fixtures. Il n'évalue ni DNSSEC, ni transport DNS réel, ni
disponibilité de service ; **réponse DNS ≠ connectivité applicative**.
Le TP DHCP décode ses seuls octets synthétiques : DORA, Discover, Offer,
Request, ACK, bail, T1, T2, relais DHCP et pool épuisé sont des mécanismes et
incidents pédagogiques, pas une validation d'interopérabilité, de sécurité ou
d'un serveur DHCP réel.
Le TP Sous-réseau/Gateway simplifie ECMP, policy routing, VRF, proxy ARP,
tunnels, VLAN et états pare-feu. Son adresse réseau, son broadcast, ses routes
et sa résolution du prochain saut sont des calculs synthétiques, pas une preuve
de configuration ou de trafic réel.
Le TP Modulation emploie un étiquetage, une grille et des courbes de BLER
pédagogiques : il ne prouve ni conformité à une forme d'onde, ni masque
spectral, ni performance RF. Le codage réel peut imposer blocs, CRC, *rate
matching* et alignements absents de l'approximation du nombre de symboles.
