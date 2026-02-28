# ============================================================
# csv_to_sqlite.py – Importe datacenter.csv dans SQLite3
# ============================================================
# Remplace l'import manuel via DB Browser for SQLite.
# Lit les colonnes et types directement depuis le CSV et crée
# la table `datacenter` dans data/datacenter.sqlite3.
#
# Usage : python scripts/csv_to_sqlite.py [--reset]
#   --reset  Supprime et recrée la table si elle existe déjà
# ============================================================

import os
import csv
import sqlite3
import argparse

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
FICHIER_CSV = os.path.join(BASE_DIR, "..", "data", "datacenter.csv")
FICHIER_BDD = os.path.join(BASE_DIR, "..", "data", "datacenter.sqlite3")

# Colonnes stockées en INTEGER dans la BDD (toutes les autres → TEXT)
COLONNES_INT = {"id", "org_id", "net_count", "ix_count"}


# ============================================================
def detecter_colonnes(fichier_csv: str) -> list[str]:
    """Lit la première ligne du CSV et retourne la liste des colonnes."""
    with open(fichier_csv, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        return next(reader)


def type_sqlite(nom_colonne: str) -> str:
    """Retourne le type SQLite selon le nom de la colonne."""
    return "INTEGER" if nom_colonne in COLONNES_INT else "TEXT"


def creer_table(cursor, colonnes: list[str], reset: bool):
    """Crée (ou recrée) la table `datacenter`."""
    if reset:
        cursor.execute("DROP TABLE IF EXISTS datacenter")
        print("  Table existante supprimée.")

    definitions = ", ".join(
        f'"{col}" {type_sqlite(col)}' for col in colonnes
    )
    cursor.execute(f'CREATE TABLE IF NOT EXISTS "datacenter" ({definitions})')


def importer_csv(fichier_csv: str, fichier_bdd: str, reset: bool = False):
    """
    Lit le CSV et l'insère dans la table `datacenter` de la BDD SQLite3.

    :param fichier_csv: chemin vers data/datacenter.csv
    :param fichier_bdd: chemin vers data/datacenter.sqlite3
    :param reset:       si True, recrée la table même si elle existe
    """
    if not os.path.exists(fichier_csv):
        raise FileNotFoundError(f"CSV introuvable : {fichier_csv}")

    conn = sqlite3.connect(fichier_bdd)
    c = conn.cursor()

    # --- Détection des colonnes ---
    colonnes = detecter_colonnes(fichier_csv)
    print(f"  Colonnes détectées : {len(colonnes)}")
    print(f"  Dont INTEGER       : {sorted(COLONNES_INT)}")

    # --- Création de la table ---
    creer_table(c, colonnes, reset)

    # --- Comptage des lignes existantes ---
    c.execute("SELECT COUNT(*) FROM datacenter")
    nb_existants = c.fetchone()[0]
    if nb_existants > 0 and not reset:
        print(f"  ⚠  La table contient déjà {nb_existants} lignes.")
        print("     Utilisez --reset pour la recréer depuis zéro.")
        conn.close()
        return

    # --- Insertion des données ---
    placeholders = ", ".join("?" * len(colonnes))
    requete_insert = f'INSERT INTO "datacenter" VALUES ({placeholders})'

    nb_inseres  = 0
    nb_erreurs  = 0

    with open(fichier_csv, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader)  # sauter l'en-tête

        for numero, ligne in enumerate(reader, start=2):
            # Normaliser la longueur de la ligne (colonnes manquantes → None)
            while len(ligne) < len(colonnes):
                ligne.append(None)
            ligne = ligne[:len(colonnes)]

            # Convertir les colonnes INTEGER (None et '' → None)
            valeurs = []
            for col, val in zip(colonnes, ligne):
                if col in COLONNES_INT:
                    try:
                        valeurs.append(int(val) if val not in (None, "") else None)
                    except ValueError:
                        valeurs.append(None)
                else:
                    valeurs.append(val if val != "" else None)

            try:
                c.execute(requete_insert, valeurs)
                nb_inseres += 1
            except sqlite3.Error as e:
                print(f"  ⚠  Ligne {numero} ignorée : {e}")
                nb_erreurs += 1

    conn.commit()
    conn.close()

    print(f"\n  ✅  {nb_inseres} lignes insérées dans `datacenter`")
    if nb_erreurs:
        print(f"  ⚠   {nb_erreurs} lignes ignorées (erreurs)")
    print(f"  💾  Base de données : {fichier_bdd}")


# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Importe data/datacenter.csv dans data/datacenter.sqlite3"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Supprime et recrée la table datacenter avant l'import"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  csv_to_sqlite.py – Import datacenter.csv → SQLite3")
    print("=" * 60)
    print(f"  Source  : {FICHIER_CSV}")
    print(f"  Cible   : {FICHIER_BDD}")
    print()

    importer_csv(FICHIER_CSV, FICHIER_BDD, reset=args.reset)
