# Laboratoires ML/RL reproductibles

Ces travaux pratiques prolongent le parcours ML/RL du livre avec quatre
notebooks exécutables, cinq preuves multi-graines retenues et le laboratoire
opérateur L22 utilisant la surface `routing_training_project`.

## Contrat pédagogique

- données entièrement synthétiques et sans trace client ;
- exécution CPU, aucune émission réseau et aucun privilège ;
- graines fixées, cinq entraînements indépendants, scénarios d'évaluation
  appariés et intervalles de confiance ;
- rôles entraînement/validation/test explicités ; une seule évaluation finale
  est un protocole à respecter, pas une propriété attestée par un compteur littéral ;
- récompenses, coûts et contraintes distingués ;
- aucune revendication de performance terrain ou d'autorité de production.

Les intervalles de L24 sont exploratoires après sélection parmi cinq pénalités.
Ils ne remplacent pas une confirmation indépendante de la configuration retenue.
Dans L27, la référence de support peut réutiliser des conditions initiales
d'entraînement ; la calibration et l'évaluation doivent être disjointes des
graines de chaque épisode d'entraînement. Le reçu publie ces rôles dans
`seed_role_contract`. La correction de l'ancienne assertion d'indépendance,
avec l'empreinte et la révision du reçu initial, est conservée dans
`results/l27_seed_contract_correction.json` ; les résultats numériques n'ont
pas été recalculés pour cette correction.

Le TP SVD/RPCA exécute une PCP exacte : son résidu numérique n'est pas une
estimation du bruit de mesure. Les diagnostics montrent que le bruit dense
contamine le support de la composante pénalisée. Le rappel au nombre connu
d'incidents évalue un classement, pas un détecteur à seuil calibré.

## Parcours

1. `notebooks/tp_ml_classification_rare.ipynb` — **60 minutes**. Ajuster un
   score sur l'entraînement, choisir un seuil de classe rare sur la validation,
   puis ouvrir le test scellé une seule fois.
2. `notebooks/tp_rl_retour_q_td.ipynb` — **45 minutes**. Calculer le retour,
   les valeurs d'action, la valeur de politique, les avantages et l'erreur TD
   sur le scénario à deux relais du livre. Comparer terminaison et troncature.
3. `notebooks/tp_rl_dqn_relais.ipynb` — **90 minutes**. Entraîner sur CPU un
   petit DQN avec rejeu d'expérience et réseau cible, puis le comparer sur des
   graines non vues à une politique aléatoire et à une heuristique de file
   projetée. Le filtre de sûreté bloque les actions vers un relais indisponible.
4. `notebooks/svd_radio.ipynb` — **60 minutes**. Relier la SVD à l'ACP de KPI
   corrélés, séparer les incidents synthétiques par RPCA et diagonaliser un
   canal MIMO complexe, avec reconstruction et capacité vérifiées.
5. **L22 dans le livre** — **120 minutes hors calcul**. Utiliser
   `routing_training_project` pour produire une politique PPO-GNN, une
   référence ILP stricte et une comparaison contrôlée avec une heuristique.
6. **L24 dans le livre** — **60 minutes hors calcul**. Balayer la pénalité de
   perte du DQN, conserver cinq graines par configuration, puis appliquer une
   porte lexicographique préétablie au retour, aux pertes et aux violations.
7. **L25 dans le livre** — **60 minutes hors calcul**. Geler le DQN retenu en
   L24, l'évaluer sans nouvel ajustement sous quatre décalages déclarés, puis
   ouvrir une fois un défi composite scellé.
8. **L26 dans le livre** — **60 minutes hors calcul**. Agréger les cinq DQN,
   balayer trois seuils d'accord et se replier sur l'heuristique lorsque les
   votes ne franchissent pas le seuil, avant un nouveau défi tenu à l'écart.
9. **L27 dans le livre** — **60 minutes hors calcul**. Calibrer sur données
   nominales un moniteur de support observable, puis cumuler repli hors support
   et unanimité des cinq DQN sans ajustement sur les régimes décalés.

Le second notebook est un exercice de compréhension. Le projet opérateur L22
reste la référence pour la chaîne PPO-GNN/ILP et ses artefacts de preuve.

## Installation et exécution

Depuis ce répertoire :

```bash
uv sync --python 3.12
uv run jupyter lab notebooks/
```

Pour exécuter et vérifier les notebooks sans interface :

```bash
uv run python verify_notebooks.py --execute
uv run pytest -q
```

La vérification écrit uniquement dans un répertoire temporaire. Les notebooks
versionnés restent sans sortie afin de limiter la taille et d'éviter de
présenter un résultat ancien comme une nouvelle exécution. Le contrôle AST
refuse les imports réseau, système et sous-processus connus, mais l'exécution
Jupyter utilise les droits du processus hôte : ce vérificateur n'est pas un bac
à sable de sécurité.

## Preuve retenue et intégrité

Depuis ce répertoire :

```bash
uv run python build_environment_lock.py
uv run python run_benchmarks.py
uv run python run_constrained_dqn_experiment.py
uv run python run_l25_robustness_experiment.py
uv run python run_l26_abstention_experiment.py
uv run python run_l27_support_guard_experiment.py
uv run python build_manifest.py
uv run python verify.py --execute-notebooks
```

Le résultat JSON conserve cinq graines d'entraînement, quarante scénarios
d'évaluation appariés, les méthodes de référence, les différences appariées,
les intervalles de confiance, les résultats négatifs et la preuve que le filtre
applique zéro action interdite. Le résultat L24 conserve séparément le balayage
de pénalités et son verdict, sans faire échouer la reproductibilité quand
l'hypothèse scientifique est rejetée. L25 conserve le contrôle nominal, quatre
décalages de distribution, un défi composite ouvert une fois et le verdict de
pire cas contre l'heuristique de charge projetée. L26 conserve les décisions
par graine, le taux de repli, l'accord des cinq modèles, la sélection de seuil
sur les seuls régimes déclarés et un nouveau défi ouvert une fois. Le taux
d'accord reste un signal de désaccord non calibré, pas une probabilité de
correction. Le seuil d'unanimité retenu réduit certaines régressions moyennes,
mais échoue encore au contrat complet ; l'heuristique reste donc la préférence
sur ce banc. `manifest.json` lie par SHA-256 le code, les notebooks, le verrou,
les schémas et les résultats. L27 conserve en plus la référence nominale du
moniteur, sa calibration disjointe, les distances de support, les décisions
d'autorité et de repli, ainsi qu'un nouveau défi ouvert une fois. La distance
au support corrige les régressions sous capacité et service déplacés, mais ne
détecte presque pas le changement séquentiel des rafales et ne démontre aucun
bénéfice strict face au repli. Elle reste un diagnostic synthétique, pas une
preuve OOD opérationnelle. Pour vérifier sans réécrire :

```bash
uv run python build_environment_lock.py --check
uv run python run_benchmarks.py --check
uv run python run_constrained_dqn_experiment.py --check
uv run python run_l25_robustness_experiment.py --check
uv run python run_l26_abstention_experiment.py --check
uv run python run_l27_support_guard_experiment.py --check
uv run python build_manifest.py --check
uv run python verify.py
```

## Limites

`RelayQueueEnv` est un modèle discret de files. Il ne modélise ni PHY/MAC, ni
TCP, ni mobilité, ni interférence. Une amélioration de sa récompense ne prouve
aucun gain sur un réseau réel. Toutes les références reçoivent le même vecteur
observable ; l'heuristique de file reste toutefois modèle-informée. Le DQN ne
reçoit aucune autorité implicite : le filtre indépendant refuse une action vers
un relais indisponible et choisit un repli autorisé avant l'appel à `step()`.

Voir `SOURCES.md` pour les références FIDLE et la provenance.
