# L28 — Agréger des mesures sans les déchiffrer

**Durée : 45 minutes.** Prérequis : Python et reste d'une division entière.
Python 3.10 ou plus suffit ; aucune dépendance, connexion réseau ou donnée
réelle n'est nécessaire.

**Ce code ne protège aucune donnée.** Ses facteurs 17 et 19 sont publiés,
les clés sont cassables à la main et les aléas sont fixes. Il illustre Paillier
additif, un chiffrement partiellement homomorphe ; ce n'est pas un système FHE.

Depuis la racine du dépôt :

```bash
python3 -m chiffrement_homomorphe_labs.tp_paillier_agregation_fr
python3 -m chiffrement_homomorphe_labs.tp_paillier_agregation_fr --check
python3 -m unittest chiffrement_homomorphe_labs.test_paillier_agregation
```

1. Prédire la somme et la moyenne de trois compteurs synthétiques : 12, 18, 30.
2. Observer les chiffrés ; vérifier que `agreger` ne reçoit aucune clé privée.
3. Déchiffrer le produit modulaire : la somme vaut 60, la moyenne calculée
   ensuite en clair vaut 20. Une pondération publique donne `2 × 12 + 18 = 42`.
4. Changer l'aléa d'un même message : le chiffré change, pas son déchiffrement.
5. Expliquer pourquoi `200 + 200` donne 77 modulo 323. Choisir les bornes
   d'entrée avant d'interpréter une somme comme un entier usuel.
6. Expliquer pourquoi multiplier les chiffrés additionne les messages et ne
   calcule pas leur produit. Distinguer cette propriété d'un calcul FHE général.
7. Retrouver 30 en soustrayant les sommes publiées 60 et 30 de deux groupes
   emboîtés. La confidentialité du calcul n'empêche pas une fuite par les sorties.

Livrable : le JSON produit, les prédictions, une explication de chaque étape
et trois limites (clés, intégrité, divulgation des résultats). Le fichier
[de référence](chiffrement_homomorphe_paillier_validation_fr.json) atteste les
calculs de cet exemple uniquement. Les tests parcourent tous les messages
du petit domaine et des sommes avec dépassement.

Source du mécanisme : Pascal Paillier, EUROCRYPT 1999,
[Public-Key Cryptosystems Based on Composite Degree Residuosity Classes](https://doi.org/10.1007/3-540-48910-X_16).
Cette implémentation pédagogique est originale. Pour une étude FHE, partir
d'une bibliothèque maintenue telle qu'[OpenFHE](https://openfhe-development.readthedocs.io/en/latest/),
définir le modèle de menace et mesurer les coûts avec des paramètres de sécurité
adaptés ; le chronométrage de ce jouet n'aurait pas cette portée.
