# Premiers pas pour explorer les réseaux

Quatre expériences pour prédire, dessiner, essayer et expliquer. Elles fonctionnent sur papier ou avec Python 3.10 ou plus, sans accès réseau ni bibliothèque à installer. Depuis la racine du dépôt compagnon, utilisez les commandes indiquées. Chaque exécution est déterministe et ne crée ni fichier ni configuration : relancer suffit pour recommencer.

## G01 Latence : petit message et gros fichier

**Durée :** 20 minutes. **Prérequis :** multiplication et division ; Python 3.10 ou plus pour exécuter. Une feuille suffit pour chercher.

Dessinez deux liaisons : A à 1 Mbit/s et 2 ms de propagation ; B à 100 Mbit/s et 250 ms. Aucune file ni aucun en-tête n’est modélisé.

1. Prédisez la liaison la plus rapide pour 100 octets, puis pour 1 Mo décimal.
2. Calculez la durée nécessaire pour émettre les bits : taille en octets × 8 / débit en bits/s.
3. Ajoutez la propagation, dans la même unité.
4. Exécutez la commande et comparez vos valeurs.
5. Modifiez une taille dans une copie du script et cherchez le changement de classement.

**Pour interpréter après la recherche :** le petit message prend 2,8 ms sur A et 250,008 ms sur B ; le fichier prend 8 002 ms sur A et 330 ms sur B. Le plus grand débit ne gagne donc pas pour toutes les tailles.

**À conserver :** prédiction, deux calculs avec unités et une phrase expliquant le changement. **Limite :** une conversation comporte aussi des réponses, des traitements et des attentes. Ce calcul ne mesure pas une liaison réelle.

~~~bash
python3 -m core_network_labs.premiers_pas_reseaux_fr latence
~~~

## G02 Files : perdre moins peut faire attendre davantage

**Durée :** 25 minutes. **Prérequis :** addition ; G01 conseillé.

Quatre paquets de 100 octets arrivent ensemble sur un lien à 8 000 bit/s. Trois paquets de fichier passent avant un paquet voix. Chaque transmission dure 100 ms. Une place en cours de service n’est pas comptée dans les places d’attente.

1. Dessinez les départs avec une seule place d’attente. Notez les paquets refusés.
2. Recommencez avec trois places. Le paquet voix arrive-t-il avant une échéance fictive de 250 ms ?
3. Prédisez l’effet d’une priorité donnée à la voix parmi les paquets en attente ; le paquet déjà en transmission continue.
4. Exécutez la commande. Expliquez chaque différence.
5. Imaginez des arrivées voix permanentes : quel autre risque faudrait-il tester ?

**Pour interpréter après la recherche :** la petite file perd deux paquets, dont la voix. La grande file livre les quatre, mais la voix termine à 400 ms. Avec priorité, elle termine à 200 ms. Une meilleure livraison ne garantit pas le respect de l’échéance.

**À conserver :** trois chronologies, pertes et délai de la voix. **Limite :** le petit lot fini ne démontre ni stabilité sous charge durable ni absence de famine. Le script réemploie le modèle de file du compagnon.

~~~bash
python3 -m core_network_labs.premiers_pas_reseaux_fr files
~~~

## G03 Découverte : une réponse exacte peut vieillir

**Durée :** 20 minutes. **Prérequis :** savoir lire une chronologie.

Un annuaire donne l’adresse 203.0.113.10 à t = 0 s. À t = 10 s, son adresse de référence devient 203.0.113.20. Un client conserve chaque réponse pendant 30 secondes, durée appelée TTL. L’expérience ne contacte aucun serveur.

1. Avant d’exécuter, écrivez la réponse attendue aux instants 0, 20 et 31 secondes.
2. Distinguez l’adresse de référence et celle que le cache rend au client.
3. Exécutez la commande, puis repérez les consultations de l’annuaire.
4. Dans une copie du script, remplacez la durée par 5 secondes. Que deviennent fraîcheur et nombre de consultations ?
5. Cherchez le résultat exactement à l’instant d’expiration.

**Pour interpréter après la recherche :** avec un TTL de 30 secondes, le client garde l’ancienne adresse à t = 20 s et obtient la nouvelle à t = 31 s. Le cache expire dès que sa limite est atteinte.

**À conserver :** une chronologie et une explication du compromis entre fraîcheur et consultations. **Limite :** ce modèle d’annuaire illustre un cache ; il n’exécute pas DNS, DHCP ou ARP. La capture de ces protocoles est un prolongement distinct.

~~~bash
python3 -m core_network_labs.premiers_pas_reseaux_fr decouverte
~~~

## G04 Chemins : moins de relais ou moins de temps

**Durée :** 25 minutes. **Prérequis :** addition ; lecture de Python facultative.

Dessinez quatre sommets A, B, C et D. Le lien direct A–D coûte 15 ; A–B, B–C et C–D coûtent chacun 2. Les liens fonctionnent dans les deux sens et les coûts s’additionnent.

1. Choisissez un chemin en minimisant le nombre de liens.
2. Choisissez-en un en minimisant le coût total.
3. Prédisez le résultat après suppression du lien B–C.
4. Exécutez la commande et comparez.
5. Si vous lisez Python, suivez la liste des candidats dans la fonction de Dijkstra. Sinon, énumérez les chemins sur papier.

**Pour interpréter après la recherche :** A–B–C–D coûte 6, contre 15 pour A–D. Après la coupure de B–C, le lien direct reste disponible.

**À conserver :** carte, deux critères et résultats avant/après coupure. **Limite :** Dijkstra suppose ici une carte disponible, cohérente et des coûts positifs. Il ne décrit ni l’échange des annonces ni leur vieillissement. La convergence OSPF appartient au second niveau.

~~~bash
python3 -m core_network_labs.premiers_pas_reseaux_fr chemins
~~~

## Expliquer ce que l’on a appris

Pour chaque expérience, gardez quatre lignes : ce que je pensais, ce que j’ai essayé, ce que le résultat change et le cas que je voudrais tester ensuite. Une sortie numérique correcte devient utile lorsqu’on peut expliquer ce qui la produit.
