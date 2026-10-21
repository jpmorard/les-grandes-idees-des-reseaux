"""Propriétés arithmétiques du TP, sans revendication de sécurité."""

import unittest

from chiffrement_homomorphe_labs.tp_paillier_agregation_fr import (
    agreger, chiffrer, cles_pedagogiques, dechiffrer, experience,
)


class PaillierPedagogiqueTests(unittest.TestCase):
    def setUp(self):
        self.publique, self.privee = cles_pedagogiques()

    def test_tous_les_messages_du_domaine(self):
        for message in range(self.publique.n):
            for alea in (2, 3, 5, 7):
                self.assertEqual(dechiffrer(self.publique, self.privee, chiffrer(self.publique, message, alea)), message)

    def test_addition_y_compris_zero_et_debordement(self):
        for gauche in (0, 1, 12, 200, 322):
            for droite in (0, 1, 18, 200, 322):
                c = agreger(self.publique, [chiffrer(self.publique, gauche, 2), chiffrer(self.publique, droite, 3)])
                self.assertEqual(dechiffrer(self.publique, self.privee, c), (gauche + droite) % self.publique.n)
        self.assertEqual(dechiffrer(self.publique, self.privee, agreger(self.publique, [])), 0)

    def test_parametres_invalides_refuses(self):
        for message in (-1, self.publique.n):
            with self.assertRaises(ValueError):
                chiffrer(self.publique, message, 2)
        for alea in (0, 17, 19, self.publique.n):
            with self.assertRaises(ValueError):
                chiffrer(self.publique, 12, alea)
        for chiffre in (0, 17, self.publique.n_carre):
            with self.assertRaises(ValueError):
                agreger(self.publique, [chiffre])
            with self.assertRaises(ValueError):
                dechiffrer(self.publique, self.privee, chiffre)

    def test_exemple_du_livre_et_alea(self):
        r = experience()
        self.assertEqual(r["somme_dechiffree"], 60)
        self.assertEqual(r["moyenne_apres_dechiffrement"], 20)
        self.assertEqual(r["somme_ponderee_2x12_plus_18"], 42)
        self.assertEqual(r["depassement_modulaire"]["dechiffre"], 77)
        self.assertNotEqual(r["chiffres"][0], r["meme_message_autre_alea"]["chiffre"])
        self.assertEqual(r["meme_message_autre_alea"]["dechiffre"], 12)


if __name__ == "__main__":
    unittest.main()
