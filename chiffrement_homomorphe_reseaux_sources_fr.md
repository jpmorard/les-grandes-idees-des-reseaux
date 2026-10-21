# Chiffrement homomorphe pour les réseaux — sources et portée

Vérification documentaire : 1 octobre 2026. Ajout à l'Idée IX, renvoi depuis
le traité IA, laboratoire L28 et questions 209 à 214 de l'annexe H.

| Source primaire | Apport retenu | Limite |
|---|---|---|
| Pascal Paillier, [EUROCRYPT 1999](https://doi.org/10.1007/3-540-48910-X_16), p. 223–238 | schéma additif et arithmétique modulaire | le TP original emploie volontairement des paramètres non sûrs ; il n'est pas FHE |
| [Documentation OpenFHE](https://openfhe-development.readthedocs.io/en/latest/) | BFV/BGV, CKKS, FHEW/TFHE, calcul chiffré et variantes multiparti | fonctions et types de calcul dépendent du schéma ; aucune performance terrain déduite |
| [Microsoft SEAL](https://github.com/microsoft/SEAL) | arithmétique exacte ou approchée, coût et domaine des opérations | ce n'est pas un remplacement transparent de tout programme en clair |
| [Security Guidelines for Implementing Homomorphic Encryption, 2024](https://doi.org/10.62056/anxra69p1) | choix des paramètres et hypothèses de sécurité | recommandations scientifiques, sans certification automatique d'une application |
| [Statut des recommandations](https://homomorphicencryption.org/security-guidelines/) | distinguer les guides 2018 et 2024 d'une norme formellement adoptée par un organisme de normalisation | le livre ne revendique aucune conformité certifiée |
| [Modèle de sécurité OpenFHE](https://openfhe-development.readthedocs.io/en/latest/sphinx_rsts/intro/security.html) | sécurité de confidentialité, attaquant honnête mais curieux, risques liés aux déchiffrements exposés | confidentialité du calcul ne vaut pas intégrité ni sécurité d'un oracle de déchiffrement |
| [Exemple de rafraîchissement CKKS](https://github.com/openfheorg/openfhe-development/blob/main/src/pke/examples/CKKS_BOOTSTRAPPING.md) | rafraîchir le budget de calcul, avec un coût et une précision à gérer | aucune latence générique ou garantie de temps réel |

Les compteurs 12, 18, 30 et les paramètres minuscules du TP sont des exemples
inventés. Les sorties de `chiffrement_homomorphe_labs/` et leurs tests vérifient
l'arithmétique ; ils n'évaluent pas la sécurité d'un déploiement.

Le dépôt compagnon est
[jpmorard/les-grandes-idees-des-reseaux](https://github.com/jpmorard/les-grandes-idees-des-reseaux).
Il rassemble les TP et le code ; sa disponibilité ne vaut pas intégration des
questions du livre dans l'application AGILAB Learning & Assessment.
