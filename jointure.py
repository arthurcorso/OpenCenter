# ============================================================
# ACTIVITÉ 7 : Jointure de tables + nouvelles cartes Folium
# Tables jointes : datacenter x pays  (clé : country = code_pays)
# ============================================================
# Prérequis : exécuter import_pays.py au préalable
# ============================================================

import os
import sqlite3
import folium
from folium.plugins import MarkerCluster

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
FICHIER_BDD = os.path.join(BASE_DIR, "data", "datacenter.sqlite3")
OUTPUT_DIR  = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# REQUÊTES SQL AVEC JOINTURE
# ============================================================

def afficher_requetes_jointure():
    """Exécute et affiche plusieurs requêtes SQL avec JOIN."""
    conn = sqlite3.connect(FICHIER_BDD)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # --- Jointure 1 : nombre de datacenters par pays (avec nom complet) ---
    print("\n=== Nombre de datacenters par pays (nom complet) ===")
    c.execute("""
        SELECT p.nom_pays, d.country, COUNT(*) AS nb
        FROM datacenter d
        JOIN pays p ON d.country = p.code_pays
        GROUP BY d.country
        ORDER BY nb DESC
        LIMIT 15
    """)
    # La jointure se fait ici sur : datacenter.country = pays.code_pays
    for row in c.fetchall():
        print(f"  {row['nom_pays']:30s} ({row['country']}) : {row['nb']}")

    # --- Jointure 2 : moyenne de réseaux par pays avec population ---
    print("\n=== Moyenne réseaux connectés vs population ===")
    c.execute("""
        SELECT p.nom_pays,
               COUNT(*)                  AS nb_dc,
               ROUND(AVG(d.net_count),1) AS moy_reseaux,
               p.population
        FROM datacenter d
        JOIN pays p ON d.country = p.code_pays
        GROUP BY d.country
        ORDER BY moy_reseaux DESC
        LIMIT 10
    """)
    for row in c.fetchall():
        print(f"  {row['nom_pays']:30s} : {row['nb_dc']} DC, "
              f"moy. réseaux={row['moy_reseaux']}, pop={row['population']:,}")

    # --- Jointure 3 : datacenters en France avec nom du pays ---
    print("\n=== Datacenters en France (jointure) ===")
    c.execute("""
        SELECT d.name, d.city, p.nom_pays, d.latitude, d.longitude
        FROM datacenter d
        JOIN pays p ON d.country = p.code_pays
        WHERE p.code_pays = 'FR'
          AND d.latitude  IS NOT NULL AND d.latitude  != ''
          AND d.longitude IS NOT NULL AND d.longitude != ''
        ORDER BY d.city
    """)
    rows_fr = c.fetchall()
    print(f"  {len(rows_fr)} datacenters français avec GPS")

    conn.close()


# ============================================================
# CARTE 1 : Datacenters par pays — couleur selon nb de DC
# ============================================================

def couleur_par_nb(nb):
    """Retourne une couleur Folium selon le nombre de datacenters."""
    if nb >= 200: return 'darkred'
    if nb >= 100: return 'red'
    if nb >= 50:  return 'orange'
    if nb >= 20:  return 'green'
    return 'lightblue'


def carte_par_pays(fichier=None):
    """
    Crée une carte avec un marqueur par pays positionné sur la capitale,
    indiquant le nombre de datacenters.
    """
    if fichier is None:
        fichier = os.path.join(OUTPUT_DIR, "carte_par_pays.html")
    conn = sqlite3.connect(FICHIER_BDD)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Jointure : datacenter ⟕ pays  →  nb dc + coord capitale
    c.execute("""
        SELECT p.nom_pays, p.code_pays,
               p.lat_capitale, p.lon_capitale,
               p.capitale,
               COUNT(d.id)              AS nb_dc,
               ROUND(AVG(d.net_count),1) AS moy_reseaux
        FROM pays p
        LEFT JOIN datacenter d ON d.country = p.code_pays
        GROUP BY p.code_pays
        ORDER BY nb_dc DESC
    """)
    rows = c.fetchall()
    conn.close()

    carte = folium.Map(
        location=(50.0, 15.0),
        zoom_start=4,
        attr='© Contributeurs OpenStreetMap'
    )

    for r in rows:
        if r['lat_capitale'] and r['lon_capitale']:
            folium.CircleMarker(
                location=(r['lat_capitale'], r['lon_capitale']),
                radius=max(5, min(30, r['nb_dc'] / 5)),
                color=couleur_par_nb(r['nb_dc']),
                fill=True,
                fill_opacity=0.7,
                popup=folium.Popup(
                    f"<b>{r['nom_pays']}</b><br>"
                    f"Datacenters : {r['nb_dc']}<br>"
                    f"Moy. réseaux connectés : {r['moy_reseaux']}",
                    max_width=250
                ),
                tooltip=f"{r['nom_pays']} : {r['nb_dc']} DC"
            ).add_to(carte)

    carte.save(fichier)
    print(f"Carte sauvegardée : {fichier}")


# ============================================================
# CARTE 2 : Datacenters d'un pays spécifique (ex : France)
# ============================================================

def carte_pays_detail(code_pays='FR', fichier=None):
    """
    Crée une carte avec tous les datacenters d'un pays donné.
    La jointure permet d'afficher le nom complet du pays.
    """
    if fichier is None:
        fichier = os.path.join(OUTPUT_DIR, f"carte_{code_pays.lower()}.html")

    conn = sqlite3.connect(FICHIER_BDD)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Jointure pour récupérer le nom du pays
    c.execute("""
        SELECT d.name, d.city, d.net_count, d.ix_count,
               d.website, p.nom_pays,
               CAST(d.latitude  AS REAL) AS lat,
               CAST(d.longitude AS REAL) AS lon
        FROM datacenter d
        JOIN pays p ON d.country = p.code_pays
        WHERE p.code_pays = ?
          AND d.latitude  IS NOT NULL AND d.latitude  != ''
          AND d.longitude IS NOT NULL AND d.longitude != ''
          AND CAST(d.latitude  AS REAL) BETWEEN -90  AND 90
          AND CAST(d.longitude AS REAL) BETWEEN -180 AND 180
    """, (code_pays,))
    rows = c.fetchall()

    # Centre de la carte = centroïde des points
    if rows:
        centre_lat = sum(r['lat'] for r in rows) / len(rows)
        centre_lon = sum(r['lon'] for r in rows) / len(rows)
    else:
        centre_lat, centre_lon = 46.2, 2.2

    nom_pays = rows[0]['nom_pays'] if rows else code_pays
    conn.close()

    carte = folium.Map(
        location=(centre_lat, centre_lon),
        zoom_start=6,
        attr='© Contributeurs OpenStreetMap'
    )
    cluster = MarkerCluster(name=f"Datacenters {nom_pays}").add_to(carte)

    for r in rows:
        folium.Marker(
            location=(r['lat'], r['lon']),
            popup=folium.Popup(
                f"<b>{r['name']}</b><br>"
                f"Ville : {r['city']}<br>"
                f"Pays : {r['nom_pays']}<br>"
                f"Réseaux : {r['net_count']} | IX : {r['ix_count']}<br>"
                f"<a href='{r['website']}' target='_blank'>Site web</a>",
                max_width=300
            ),
            tooltip=r['name'],
            icon=folium.Icon(color='blue', icon='server', prefix='fa')
        ).add_to(cluster)

    folium.LayerControl().add_to(carte)
    carte.save(fichier)
    print(f"Carte sauvegardée : {fichier} ({len(rows)} marqueurs pour {nom_pays})")


# ============================================================
if __name__ == "__main__":
    # 1. Affichage des requêtes avec jointure dans le terminal
    afficher_requetes_jointure()

    # 2. Carte par pays (cercles proportionnels)
    carte_par_pays()

    # 3. Carte détaillée France
    carte_pays_detail('FR')

    # 4. Carte détaillée Allemagne
    carte_pays_detail('DE')
