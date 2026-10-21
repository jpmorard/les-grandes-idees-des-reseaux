"""L28 : comprendre l'addition chiffrée avec un Paillier volontairement minuscule.

NE PAS PROTÉGER DE DONNÉES AVEC CE CODE. Les facteurs sont publics, les clés
sont cassables à la main et les aléas sont fixés pour reproduire les calculs.
Ce TP illustre un chiffrement partiellement homomorphe, pas un système FHE.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from math import gcd, lcm, prod
from pathlib import Path


@dataclass(frozen=True)
class ClePublique:
    n: int
    g: int

    @property
    def n_carre(self) -> int:
        return self.n * self.n


@dataclass(frozen=True)
class ClePrivee:
    lambda_: int
    mu: int


def cles_pedagogiques() -> tuple[ClePublique, ClePrivee]:
    """Paramètres fixes publiés pour le TP ; aucune génération de clé sûre."""
    p, q = 17, 19
    n = p * q
    publique = ClePublique(n=n, g=n + 1)
    lambda_ = lcm(p - 1, q - 1)
    valeur_l = (pow(publique.g, lambda_, publique.n_carre) - 1) // n
    return publique, ClePrivee(lambda_, pow(valeur_l, -1, n))


def chiffrer(publique: ClePublique, message: int, alea: int) -> int:
    if not 0 <= message < publique.n:
        raise ValueError("Le message doit appartenir à [0, n).")
    if not 1 <= alea < publique.n or gcd(alea, publique.n) != 1:
        raise ValueError("L'aléa doit être dans [1, n) et premier avec n.")
    return (
        pow(publique.g, message, publique.n_carre)
        * pow(alea, publique.n, publique.n_carre)
    ) % publique.n_carre


def _verifier_chiffre(publique: ClePublique, chiffre: int) -> None:
    if not 1 <= chiffre < publique.n_carre or gcd(chiffre, publique.n) != 1:
        raise ValueError("Chiffré hors du groupe multiplicatif modulo n².")


def agreger(publique: ClePublique, chiffres: list[int]) -> int:
    """Le calculateur ne reçoit que la clé publique et les chiffrés."""
    for chiffre in chiffres:
        _verifier_chiffre(publique, chiffre)
    return prod(chiffres) % publique.n_carre


def dechiffrer(publique: ClePublique, privee: ClePrivee, chiffre: int) -> int:
    _verifier_chiffre(publique, chiffre)
    valeur_l = (pow(chiffre, privee.lambda_, publique.n_carre) - 1) // publique.n
    return (valeur_l * privee.mu) % publique.n


def experience() -> dict[str, object]:
    publique, privee = cles_pedagogiques()
    mesures = [12, 18, 30]
    chiffres = [chiffrer(publique, m, r) for m, r in zip(mesures, [2, 3, 5])]
    chiffre_somme = agreger(publique, chiffres)
    somme = dechiffrer(publique, privee, chiffre_somme)
    chiffre_pondere = (pow(chiffres[0], 2, publique.n_carre) * chiffres[1]) % publique.n_carre
    debordement = agreger(publique, [chiffrer(publique, 200, 2), chiffrer(publique, 200, 3)])
    autre_chiffre = chiffrer(publique, mesures[0], 7)
    return {
        "schema": "reseaux.tp-paillier.v1",
        "securite": "AUCUNE : petits facteurs publics et aléas fixes ; démonstration arithmétique seulement",
        "famille": "partiellement homomorphe additif, pas FHE",
        "parametres_publics": {"n": publique.n, "g": publique.g, "n_carre": publique.n_carre},
        "mesures_synthetiques": mesures,
        "chiffres": chiffres,
        "chiffre_agrege": chiffre_somme,
        "somme_dechiffree": somme,
        "moyenne_apres_dechiffrement": somme / len(mesures),
        "somme_ponderee_2x12_plus_18": dechiffrer(publique, privee, chiffre_pondere),
        "meme_message_autre_alea": {"chiffre": autre_chiffre, "dechiffre": dechiffrer(publique, privee, autre_chiffre)},
        "depassement_modulaire": {"somme_entiere": 400, "modulo": publique.n, "dechiffre": dechiffrer(publique, privee, debordement)},
        "limites": ["aucune preuve d'intégrité", "aucune confidentialité du résultat publié", "aucun coût FHE mesuré"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Comparer au résultat pédagogique conservé.")
    parser.add_argument("--output", type=Path, help="Écrire le résultat dans ce fichier JSON.")
    args = parser.parse_args()
    resultat = experience()
    if args.check:
        attendu = Path(__file__).with_name("chiffrement_homomorphe_paillier_validation_fr.json")
        if json.loads(attendu.read_text(encoding="utf-8")) != resultat:
            raise SystemExit("Échec : résultat différent de la référence pédagogique.")
        print("L28 : somme 60, moyenne 20, somme pondérée 42, débordement 77 ; référence conforme.")
    elif args.output:
        args.output.write_text(json.dumps(resultat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        print(json.dumps(resultat, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
