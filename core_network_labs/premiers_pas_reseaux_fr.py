"""Quatre expériences de découverte, sans réseau ni dépendance externe."""
from __future__ import annotations

import argparse
import heapq
import json
from .models import Packet, simulate_queue


def latence_ms(octets: int, debit_bps: int, propagation_ms: float) -> float:
    """Sérialisation et propagation seules, sans en-tête ni file."""
    if octets < 0 or debit_bps <= 0 or propagation_ms < 0:
        raise ValueError("taille et propagation positives ou nulles, débit positif")
    return octets * 8 / debit_bps * 1000 + propagation_ms


def experience_latence() -> dict:
    return {
        str(taille): {
            "A_ms": latence_ms(taille, 1_000_000, 2),
            "B_ms": latence_ms(taille, 100_000_000, 250),
        }
        for taille in (100, 1_000_000)
    }


def experience_files() -> dict:
    # Les identifiants fixent l'ordre des arrivées simultanées.
    paquets = [Packet(f"b{i}", "fichier", 0, 100) for i in range(3)]
    paquets.append(Packet("v0", "voix", 0, 100, priority=0))
    resultat = {}
    for nom, places, politique in (
        ("petite_fifo", 1, "fifo"),
        ("grande_fifo", 3, "fifo"),
        ("grande_priorite", 3, "priority"),
    ):
        r = simulate_queue(paquets, rate_bps=8_000, waiting_slots=places, policy=politique)
        voix = next((p for p in r["delivered"] if p["packet_id"] == "v0"), None)
        resultat[nom] = {
            "livres": len(r["delivered"]),
            "perdus": len(r["dropped"]),
            "voix_sejour_ms": voix["sojourn_us"] / 1000 if voix else None,
        }
    return resultat


def experience_decouverte(instants=(0, 20, 31), duree=30) -> list[dict]:
    """L'autorité change à t=10 s ; le cache expire exactement à sa limite."""
    if duree < 0 or any(t < 0 for t in instants) or list(instants) != sorted(instants):
        raise ValueError("durée et temps non négatifs, requêtes dans l'ordre")
    valeur = None
    expiration = 0
    resultat = []
    for instant in instants:
        autorite = "203.0.113.10" if instant < 10 else "203.0.113.20"
        cache = valeur is not None and instant < expiration
        if not cache:
            valeur, expiration = autorite, instant + duree
        resultat.append({
            "temps_s": instant, "autorite": autorite, "adresse_obtenue": valeur,
            "depuis_cache": cache, "expiration_s": expiration,
        })
    return resultat


def chemin_minimal(liens, depart="A", arrivee="D"):
    """Dijkstra sur un graphe non orienté à coûts strictement positifs."""
    voisins = {}
    for a, z, cout in liens:
        if cout <= 0:
            raise ValueError("coûts strictement positifs")
        voisins.setdefault(a, []).append((z, cout))
        voisins.setdefault(z, []).append((a, cout))
    candidats = [(0, (depart,))]
    visites = set()
    while candidats:
        cout, chemin = heapq.heappop(candidats)
        sommet = chemin[-1]
        if sommet in visites:
            continue
        visites.add(sommet)
        if sommet == arrivee:
            return {"chemin": list(chemin), "cout": cout}
        for suivant, poids in voisins.get(sommet, []):
            if suivant not in visites:
                heapq.heappush(candidats, (cout + poids, (*chemin, suivant)))
    return {"chemin": [], "cout": None}


def experience_chemins() -> dict:
    liens = [("A", "D", 15), ("A", "B", 2), ("B", "C", 2), ("C", "D", 2)]
    return {
        "avant_coupure": chemin_minimal(liens),
        "apres_coupure_BC": chemin_minimal([l for l in liens if l[:2] != ("B", "C")]),
    }


def main():
    experiences = {
        "latence": experience_latence, "files": experience_files,
        "decouverte": experience_decouverte, "chemins": experience_chemins,
    }
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experience", choices=[*experiences, "tous"], nargs="?", default="tous")
    args = parser.parse_args()
    resultat = ({nom: f() for nom, f in experiences.items()} if args.experience == "tous"
                else experiences[args.experience]())
    print(json.dumps(resultat, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
