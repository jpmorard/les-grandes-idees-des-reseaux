# Notebooks ML/RL

Ce répertoire contient les quatre notebooks exécutables du parcours :

- `tp_ml_classification_rare.ipynb` : séparation entraînement/validation/test,
  choix du seuil sur validation et ouverture unique du test scellé ;
- `tp_rl_retour_q_td.ipynb` : retour actualisé, valeurs, avantages, erreur TD,
  terminaison et troncature ;
- `tp_rl_dqn_relais.ipynb` : DQN avec rejeu, réseau cible, références appariées
  et filtre d'actions interdites ;
- `svd_radio.ipynb` : ACP/SVD de KPI corrélés, incidents synthétiques par RPCA
  et modes d'un canal MIMO complexe.

`svd_radio.ipynb` est le compagnon déterministe et autonome de la section
ACP/SVD du livre. Il adapte le fil pédagogique du notebook antérieur
[dim-reduc.ipynb](https://github.com/morard/ML-jpmorard-AE/blob/b7fa78258df79f7adfc80f4d5e98c74cf4605948/ml1/dim-reduc.ipynb)
à des KPI réseau corrélés, des incidents synthétiques rares et un canal MIMO
complexe. Voir `../SOURCES.md` pour la provenance figée et la licence.

Le notebook utilise NumPy, pandas et Matplotlib. Ses cellules de code vérifient
par assertion :

- la reconstruction SVD mince exacte ;
- la convergence RPCA et le rappel des incidents ;
- la reconstruction du canal MIMO complexe et l'unitarité des facteurs ;
- l'accord entre les calculs modal et matriciel de capacité.

Toutes les mesures radio et tous les incidents sont des données pédagogiques
synthétiques. Ils ne constituent ni une calibration RF, ni une preuve de
performance terrain.
