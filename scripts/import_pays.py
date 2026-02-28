# ============================================================
# ACTIVITÉ 7 : Import du jeu de données pays européens
# Crée la table `pays` dans datacenter.sqlite3 depuis pays_europe.csv
# ============================================================

import os
import sqlite3
import csv

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
FICHIER_BDD = os.path.join(BASE_DIR, "..", "data", "datacenter.sqlite3")
FICHIER_CSV = os.path.join(BASE_DIR, "..", "data", "pays_europe.csv")


def import_pays(fichier_csv=FICHIER_CSV, fichier_bdd=FICHIER_BDD):
    conn = sqlite3.connect(fichier_bdd)
    c = conn.cursor()

    # --- Création de la table pays ---
    c.execute("DROP TABLE IF EXISTS pays")
    c.execute("""
        CREATE TABLE pays (
            code_pays    TEXT PRIMARY KEY,
            nom_pays     TEXT,
            capitale     TEXT,
            lat_capitale REAL,
            lon_capitale REAL,
            population   INTEGER,
            superficie_km2 INTEGER
        )
    """)

    # --- Remplissage depuis le CSV ---
    with open(fichier_csv, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [
            (
                r['code_pays'], r['nom_pays'], r['capitale'],
                float(r['lat_capitale']), float(r['lon_capitale']),
                int(r['population']), int(r['superficie_km2'])
            )
            for r in reader
        ]

    c.executemany("""
        INSERT OR IGNORE INTO pays
            (code_pays, nom_pays, capitale, lat_capitale, lon_capitale, population, superficie_km2)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    print(f"{c.rowcount} pays importés dans la table `pays`.")
    conn.close()


if __name__ == "__main__":
    import_pays()
    print("Import terminé.")
