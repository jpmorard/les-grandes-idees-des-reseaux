# Trois TP reproductibles de cœur réseau

Ce compagnon ferme trois parcours précis : latence/QoS, convergence distribuée,
et BGP/validation d'origine. Il fournit des **modèles synthétiques exécutables**,
pas un démon OSPF/BGP, une mesure TCP, une pile radio ni une configuration de
routeur. Aucun paquet n'est envoyé et aucune interface n'est modifiée.

## Environnement et commandes exactes

Exécuter les commandes depuis le dossier du livre,
Les_Grandes_Idees_des_Reseaux_Edition_1.0.

Le CLI et les tests demandent Python 3.10 ou plus et seulement la bibliothèque
standard. Les notebooks utilisent pandas et Jupyter dans l'environnement
commun verrouillé de machine_learning_labs (Python >=3.12,<3.15).

    python3 -m unittest discover -s core_network_labs/tests
    python3 -m core_network_labs.run_labs --check
    python3 core_network_labs/verify_notebooks.py
    uv run --project machine_learning_labs --locked python core_network_labs/verify_notebooks.py --execute

La dernière commande exécute les trois notebooks en mémoire, sans réécrire
leurs fichiers. Pour les ouvrir interactivement :

    uv run --project machine_learning_labs --locked jupyter lab core_network_labs/notebooks

Pour reproduire les sorties dans un dossier de travail choisi :

    python3 -m core_network_labs.run_labs --output /tmp/network-book-core-replay

La commande peut réécrire les trois JSON portant les noms indiqués dans ce
dossier. Elle ne modifie pas les entrées ni le manifeste canonique. Pour une
régénération éditoriale intentionnelle des résultats retenus et de leur manifeste :

    python3 -m core_network_labs.run_labs

Le mode --check recalcule les modèles, compare exactement les trois JSON
retenus et vérifie les empreintes des entrées, du code, des notebooks, des
tests et de ce README. Une empreinte prouve l'identité des octets ; elle ne
prouve ni l'adéquation du modèle au terrain ni une reproduction indépendante.

## Entrées, modèles et sorties

Les paramètres figés résident dans [scenarios.json](inputs/scenarios.json).
Les unités font partie des noms : bits/s, octets, microsecondes et millisecondes.
Les événements de file ont une résolution d'une microseconde ; la durée de
sérialisation est arrondie vers le haut. Les résultats sont déterministes :
la tolérance de comparaison des fichiers est nulle.

| TP | Entrées essentielles | Observation attendue | Notebook et preuve |
|---|---|---|---|
| Latence/QoS | 1 Mbit/s ; flux bulk 1500 octets/10 ms ; voix 200 octets/20 ms ; une seconde puis vidage ; 2 ou 20 places d'attente | File courte : plus de pertes et délai des livrés plus faible ; priorité : délai vocal plus faible sans préemption ni nouvelle capacité | [Notebook](notebooks/tp_latence_qos.ipynb), [résultats](results/latency_qos.json) |
| Convergence | A–B=1, B–C=1, A–C=3 ; B–C tombe à 0 ms ; mises à jour à 5 et 30 ms | Ancien chemin vers lien mort, puis A↔B si B met à jour avant A, puis A–C ; l'ordre inverse évite cette boucle dans ce triangle | [Notebook](notebooks/tp_convergence.ipynb), [résultats](results/convergence.json) |
| BGP/ROV | VRP AS64500, 203.0.113.0/24, maxLength24 ; quatre annonces et un cas de cache indisponible | Valid / Invalid / Invalid / NotFound ; la classification seule ne rejette rien ; la politique explicite change la décision | [Notebook](notebooks/tp_bgp_rov.ipynb), [résultats](results/bgp_rov.json) |

Le manifeste [manifest.json](manifest.json) inventorie les fichiers avec taille,
SHA-256, producteur et périmètre. Les entrées et résultats sont de vrais fichiers.

## Conventions qui changent l'interprétation

- La capacité de file compte les paquets **en attente**, en plus du paquet en
  service. Une fin de service et l'envoi du prochain paquet déjà en file
  précèdent les arrivées simultanées. Les arrivées de même date suivent leur
  identifiant ; une priorité agit à la sortie de la file, sans préemption.
- Le délai moyen/p95 porte sur les paquets **livrés**. Le p95 est au rang
  supérieur de la distribution empirique ; lire les pertes à côté du délai.
  Ce modèle ne mesure ni TCP, ni ECN/AQM, ni en-têtes, ni propagation.
- La convergence impose les instants d'installation des FIB. Il n'y a ni
  flooding, ni élection, ni temporisation d'un protocole. Une boucle est
  détectée dans le chemin de transfert ; aucun paquet n'attend un TTL réel.
- Les VRP sont fournis au modèle ; les signatures et certificats ne sont pas
  vérifiés. Unavailable est une observation de disponibilité locale, pas un
  quatrième état normatif ROV. La politique locale illustrée accepte NotFound
  et suspend sa décision lorsque le cache est indisponible. D'autres politiques
  exigent une analyse opérationnelle distincte.

## Remise à zéro et adaptation

Une exécution repart des paramètres immuables et d'objets neufs. Redémarrer le
noyau puis « tout exécuter » remet entièrement les notebooks à zéro. Le CLI
ne conserve ni processus, ni état réseau, ni fichier d'entrée modifié.

Pour apprendre, modifier les objets en mémoire et prédire le résultat avant
l'exécution : surcharge vocale, arrivée exactement en fin de service, inversion
des FIB, second VRP autorisant un /25, cache vide valide versus indisponible.
Une adaptation éditoriale des entrées impose de régénérer les résultats et le
manifeste, puis de relancer les tests et l'exécution des notebooks.

Le plan de vérification externe consiste à reproduire les trois commandes de
contrôle dans un second environnement, comparer les JSON et discuter les
limites. Cette reproduction externe n'est pas déclarée acquise ici.

Sources primaires : [RFC 5715](https://www.rfc-editor.org/info/rfc5715/),
[RFC 5286](https://www.rfc-editor.org/info/rfc5286/),
[RFC 6811](https://www.rfc-editor.org/info/rfc6811/),
[RFC 8481 §5](https://www.rfc-editor.org/rfc/rfc8481.html#section-5).
