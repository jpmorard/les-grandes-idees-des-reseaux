# Sources pédagogiques et provenance

Repères scientifiques pour les limites explicitées dans les TP :

- Candès, Li, Ma et Wright, [Robust Principal Component Analysis?](https://arxiv.org/abs/0912.3599)
  — PCP exacte et hypothèses de séparation faible rang/parcimonie.
- Zhou, Li, Wright, Candès et Ma, [Stable Principal Component Pursuit](https://arxiv.org/abs/1001.2363)
  — formulation relâchée pour séparer le bruit dense ; cette variante n'est pas
  implémentée dans le TP.
- Cawley et Talbot, [On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation](https://www.jmlr.org/papers/v11/cawley10a.html)
  — raison pour laquelle les intervalles de L24 restent exploratoires après sélection.
- Farama Foundation, [Handling Time Limits](https://gymnasium.farama.org/tutorials/gymnasium_basics/handling_time_limits/)
  — distinction entre horizon intrinsèque, terminaison et limite externe de collecte.

Les laboratoires de classification et de RL sont des créations originales
adaptées aux problèmes de classes rares, de files et de routage du livre.
Aucun code ni cellule FIDLE n'est reproduit.

La progression a été inspirée par deux ressources consultées dans le dépôt
FIDLE :

- `DRL.PyTorch/FIDLE_DQNfromScratch.ipynb`, qui rend visibles réseau de valeur,
  rejeu d'expérience et réseau cible ;
- `DRL.PyTorch/FIDLE_rl_baselines_zoo.ipynb`, qui sépare entraînement,
  évaluation et réglage d'hyperparamètres.

Références :

- dépôt : <https://gricad-gitlab.univ-grenoble-alpes.fr/talks/fidle/-/tree/master> ;
- DQN : <https://gricad-gitlab.univ-grenoble-alpes.fr/talks/fidle/-/blob/master/DRL.PyTorch/FIDLE_DQNfromScratch.ipynb> ;
- RL Zoo : <https://gricad-gitlab.univ-grenoble-alpes.fr/talks/fidle/-/blob/master/DRL.PyTorch/FIDLE_rl_baselines_zoo.ipynb>.

Références fondamentales et contrats d'API :

- Sutton, R. S. et Barto, A. G., *Reinforcement Learning: An Introduction*,
  2e éd. : <https://incompleteideas.net/book/the-book-2nd.html> ;
- Mnih et al., « Human-level control through deep reinforcement learning »,
  *Nature* 518, 529–533 (2015) : <https://www.nature.com/articles/nature14236> ;
- Farama Foundation, « Handling Time Limits », pour la distinction actuelle
  entre terminaison, troncature et bootstrap :
  <https://gymnasium.farama.org/main/tutorials/handling_time_limits/>.

Le `README.md` du dépôt FIDLE observé au commit
`1cff5b5fed0a2a171244c6185ae455a4eb3587ae` indique CC BY-NC-SA 4.0, tandis
que le site FIDLE consulté en septembre 2026 annonce CC BY-NC-ND 4.0 pour
l'ensemble de la formation. Pour éviter toute ambiguïté, seules les idées
pédagogiques et les références publiques sont reprises ici.

La migration technique suit l'API Gymnasium actuelle : `reset()` retourne
observation et informations ; `step()` distingue `terminated` et `truncated` ;
une troncature conserve le bootstrap de la valeur future.

Le laboratoire de classification rare est une création originale. Ses données
sont synthétiques et générées localement ; les trois jeux portent des
identifiants et des empreintes distinctes. Le seuil est choisi sur la validation
et le test final n'est évalué qu'après ce choix.

## Adaptation SVD, ACP et radio

Le notebook `notebooks/svd_radio.ipynb` reprend le fil pédagogique ACP → SVD du
notebook antérieur de Jean-Pierre Morard `ml1/dim-reduc.ipynb`, observé au
commit `b7fa78258df79f7adfc80f4d5e98c74cf4605948` du dépôt
`morard/ML-jpmorard-AE`. Ce dépôt publie son contenu sous licence MIT.

Références figées :

- notebook source :
  <https://github.com/morard/ML-jpmorard-AE/blob/b7fa78258df79f7adfc80f4d5e98c74cf4605948/ml1/dim-reduc.ipynb> ;
- licence MIT :
  <https://github.com/morard/ML-jpmorard-AE/blob/b7fa78258df79f7adfc80f4d5e98c74cf4605948/LICENSE>.

L'adaptation est réécrite pour ce livre : elle ne reprend ni cellule, ni sortie,
ni jeu de données du notebook antérieur. Elle emploie des KPI réseau
synthétiques, une séparation RPCA d'incidents et un canal MIMO complexe. Ses
assertions vérifient la reconstruction, la convergence, le rappel des incidents,
l'unitarité et deux calculs indépendants de capacité. Ces résultats restent des
preuves pédagogiques hors ligne, pas une qualification radio.
