<a id="choisir-variante-acp-reseaux"></a>

## Choisir une variante de l’ACP pour les réseaux

**Dossier de consultation.** Les calculs suivants prolongent la question de la représentation des observations. Vous pouvez rejoindre directement le dictionnaire commun du livre et revenir à cette étude pour choisir une décomposition.


Un **KPI** (*Key Performance Indicator*), ou indicateur clé de performance,
est une mesure choisie pour suivre une performance, comme le débit livré ou
la latence.

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

<a id="pourquoi-lacp-robuste-est-particulièrement-pertinente"></a>

### Pourquoi l’ACP robuste est particulièrement pertinente

En fonctionnement normal, les KPI d’un réseau radio sont fortement corrélés :
**RSRP** (puissance reçue sur les signaux de référence), **RSRQ** (indicateur
de qualité de réception) et SINR ; débit et utilisation des **PRB** (blocs de
ressources radio) ; BLER et retransmissions ;
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

<a id="recommandation-pour-la-supervision-au-niveau-cellule"></a>

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

<a id="svd-fondement-numérique-de-lacp"></a>

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

<a id="vocabulaire-linéaire-minimal-pour-lire-le-notebook"></a>

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

<a id="canal-radio-mimo"></a>

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

<a id="variantes-recommandées"></a>

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
