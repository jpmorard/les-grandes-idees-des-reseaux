"""Vérifier les contre-exemples que les quatre premiers TP font explorer."""
import unittest
from core_network_labs.premiers_pas_reseaux_fr import (
    chemin_minimal, experience_decouverte, experience_files, experience_latence,
)


class PremiersPasTests(unittest.TestCase):
    def test_le_classement_change_avec_la_taille(self):
        r = experience_latence()
        self.assertAlmostEqual(r["100"]["A_ms"], 2.8)
        self.assertAlmostEqual(r["100"]["B_ms"], 250.008)
        self.assertLess(r["100"]["A_ms"], r["100"]["B_ms"])
        self.assertGreater(r["1000000"]["A_ms"], r["1000000"]["B_ms"])

    def test_plus_de_memoire_livre_une_voix_tardive(self):
        r = experience_files()
        self.assertEqual(r["petite_fifo"]["perdus"], 2)
        self.assertIsNone(r["petite_fifo"]["voix_sejour_ms"])
        self.assertEqual(r["grande_fifo"]["perdus"], 0)
        self.assertEqual(r["grande_fifo"]["voix_sejour_ms"], 400)
        self.assertEqual(r["grande_priorite"]["voix_sejour_ms"], 200)

    def test_le_cache_expire_a_la_borne(self):
        r = experience_decouverte((0, 29, 30))
        self.assertEqual(r[1]["adresse_obtenue"], "203.0.113.10")
        self.assertTrue(r[1]["depuis_cache"])
        self.assertEqual(r[2]["adresse_obtenue"], "203.0.113.20")
        self.assertFalse(r[2]["depuis_cache"])

    def test_ttl_nul_ne_conserve_pas_de_reponse(self):
        r = experience_decouverte((0, 0, 10), duree=0)
        self.assertTrue(all(not x["depuis_cache"] for x in r))
        self.assertEqual(r[-1]["adresse_obtenue"], "203.0.113.20")

    def test_un_detour_est_moins_couteux_puis_devient_impossible(self):
        liens = [("A", "D", 15), ("A", "B", 2), ("B", "C", 2), ("C", "D", 2)]
        self.assertEqual(chemin_minimal(liens), {"chemin": ["A", "B", "C", "D"], "cout": 6})
        self.assertEqual(chemin_minimal([liens[0], liens[1], liens[3]])["cout"], 15)

    def test_graphe_deconnecte_et_couts_invalides(self):
        self.assertEqual(chemin_minimal([("A", "B", 1)])["chemin"], [])
        with self.assertRaises(ValueError):
            chemin_minimal([("A", "D", -1)])


if __name__ == "__main__":
    unittest.main()
