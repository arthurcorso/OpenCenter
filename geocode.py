# ============================================================
# geocode.py – Géocodage des datacenters sans coordonnées GPS
# Utilise Nominatim (OpenStreetMap) via geopy
# ============================================================
# Installation : pip install geopy
# Usage        : python geocode.py [--dry-run] [--limit N]
# ============================================================
# Nominatim ToS : 1 requête/seconde max, User-Agent obligatoire
# ============================================================

import sqlite3
import time
import argparse
import sys
import os
import ssl

try:
    import certifi
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    import urllib.request
    # Fix SSL sur macOS : utiliser les certificats certifi
    _ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    import geopy.geocoders
    geopy.geocoders.options.default_ssl_context = _ssl_ctx
except ImportError as e:
    print(f"❌  Dépendance manquante : {e}\n   Lance : pip install geopy certifi")
    sys.exit(1)

# -------------------- CONSTANTES ----------------------------
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
FICHIER_BDD = os.path.join(BASE_DIR, "data", "datacenter.sqlite3")
DELAI       = 1.1          # secondes entre chaque requête (>1 selon ToS)
MAX_RETRIES = 3


# ============================================================
def geocoder_adresse(geocoder, adresse: str) -> tuple[float, float] | None:
    """
    Tente de géocoder une adresse.
    Retourne (lat, lon) ou None si introuvable.
    """
    for tentative in range(MAX_RETRIES):
        try:
            location = geocoder.geocode(adresse, timeout=10)
            if location:
                return round(location.latitude, 6), round(location.longitude, 6)
            return None
        except GeocoderTimedOut:
            if tentative < MAX_RETRIES - 1:
                time.sleep(2)
        except GeocoderServiceError as e:
            print(f"    ⚠  Erreur service : {e}")
            return None
    return None


def construire_adresse(row) -> list[str]:
    """
    Construit plusieurs variantes d'adresse pour maximiser les chances
    de géocodage (du plus précis au moins précis).
    """
    variantes = []
    addr1  = (row["address1"] or "").strip()
    addr2  = (row["address2"] or "").strip()
    city   = (row["city"]    or "").strip()
    state  = (row["state"]   or "").strip()
    zip_   = (row["zipcode"] or "").strip()
    pays   = (row["country"] or "").strip()

    # Variante 1 : adresse complète
    parts = [p for p in [addr1, addr2, zip_, city, state, pays] if p]
    if parts:
        variantes.append(", ".join(parts))

    # Variante 2 : sans adresse de rue (code postal + ville + pays)
    parts2 = [p for p in [zip_, city, state, pays] if p]
    if parts2 and parts2 != parts:
        variantes.append(", ".join(parts2))

    # Variante 3 : ville + pays uniquement
    parts3 = [p for p in [city, pays] if p]
    if parts3:
        variantes.append(", ".join(parts3))

    return variantes


# ============================================================
def geocoder_manquants(dry_run=False, limite=None):
    """
    Parcourt tous les datacenters sans coordinates valides,
    tente de les géocoder via Nominatim, et met à jour la BDD.
    """
    conn = sqlite3.connect(FICHIER_BDD)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Récupérer les DC sans GPS valide
    c.execute("""
        SELECT id, name, city, country, address1, address2,
               state, zipcode, latitude, longitude
        FROM datacenter
        WHERE (latitude  IS NULL OR latitude  = '' OR CAST(latitude  AS REAL) = 0)
           OR (longitude IS NULL OR longitude = '' OR CAST(longitude AS REAL) = 0)
        ORDER BY country, city
    """)
    a_geocoder = c.fetchall()

    total = len(a_geocoder)
    if limite:
        a_geocoder = a_geocoder[:limite]

    print(f"🔍  {total} datacenters sans coordonnées GPS trouvés.")
    if limite:
        print(f"    → Traitement limité à {limite} entrées.")
    if dry_run:
        print("    [DRY-RUN] Aucune écriture en base.\n")

    geocoder = Nominatim(user_agent="OpenCenter-Geocoder/1.0")

    succes = 0
    echecs = 0

    for i, row in enumerate(a_geocoder, 1):
        print(f"[{i:4d}/{len(a_geocoder)}] {row['name'][:50]:<50s} | {row['city']}, {row['country']}")

        variantes = construire_adresse(row)
        if not variantes:
            print("           ⛔  Aucune adresse disponible, ignoré.\n")
            echecs += 1
            continue

        coords = None
        for variante in variantes:
            coords = geocoder_adresse(geocoder, variante)
            if coords:
                print(f"           ✅  {coords[0]}, {coords[1]}  (via: \"{variante}\")")
                break
            time.sleep(DELAI)

        if coords:
            if not dry_run:
                c.execute(
                    "UPDATE datacenter SET latitude=?, longitude=? WHERE id=?",
                    (str(coords[0]), str(coords[1]), row["id"])
                )
                conn.commit()
            succes += 1
        else:
            print(f"           ❌  Introuvable.")
            echecs += 1

        # Respecter le délai Nominatim
        time.sleep(DELAI)

    conn.close()

    print(f"\n{'─'*60}")
    print(f"✅  Géocodés avec succès : {succes}")
    print(f"❌  Non trouvés          : {echecs}")
    print(f"📊  Total traités        : {succes + echecs} / {total}")
    if not dry_run and succes > 0:
        print(f"💾  Base de données mise à jour : {FICHIER_BDD}")


# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Géocode les datacenters sans coordonnées GPS via Nominatim (OSM)."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Affiche les résultats sans modifier la base de données."
    )
    parser.add_argument(
        "--limite", type=int, default=None, metavar="N",
        help="Limite le traitement à N entrées (pratique pour tester)."
    )
    args = parser.parse_args()

    geocoder_manquants(dry_run=args.dry_run, limite=args.limite)
