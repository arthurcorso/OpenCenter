# ============================================================
# ACTIVITÉ 6 : Visualisation sur carte Folium
# Jeu de données : PeeringDB – Datacenters européens
# ============================================================
# Installation : pip install folium
# Résultat     : carte_datacenters.html
# ============================================================

import os
import sqlite3
import folium
from folium.plugins import MarkerCluster

# -------------------- CONSTANTES ----------------------------
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
FICHIER_BDD   = os.path.join(BASE_DIR, "data",   "datacenter.sqlite3")
FICHIER_CARTE = os.path.join(BASE_DIR, "output", "carte_datacenters.html")
CENTRE_CARTE  = (48.8, 10.0)   # centre de l'Europe
ZOOM_DEPART   = 5
os.makedirs(os.path.join(BASE_DIR, "output"), exist_ok=True)

# -------------------- EXEMPLE DE LISTE ---------------------
Liste_exemple = [
    ('eve1', 44.29,  2.519),
    ('eve2', 44.339, 2.105),
    ('eve3', 43.855, 2.838),
    ('eve4', 44.332, 2.787),
    ('eve5', 44.126, 3.253),
    ('eve6', 44.484, 2.496),
    ('eve7', 44.316, 2.585),
    ('eve8', 43.849, 2.899),
    ('eve9', 44.366, 2.04199),
    ('eve10', 43.933, 2.664),
]


# ============================================================
def creation_carte(liste=None,
                   centre=CENTRE_CARTE,
                   zoom=ZOOM_DEPART,
                   fichier=FICHIER_CARTE):
    """
    Crée une carte Folium centrée sur `centre` avec un marqueur de test
    puis ajoute tous les marqueurs de `liste` (tuple : nom, lat, lon).
    Sauvegarde la carte dans `fichier`.

    :param liste:   liste de tuples (nom, latitude, longitude)
    :param centre:  tuple (lat, lon) pour centrer la carte
    :param zoom:    niveau de zoom initial (1-19)
    :param fichier: nom du fichier HTML de sortie
    :return: objet carte folium
    """

    # --- Création de l'objet carte ---
    carte = folium.Map(
        location=centre,
        zoom_start=zoom,
        attr='© Contributeurs OpenStreetMap'
    )

    # --- Marqueur central personnalisé ---
    folium.Marker(
        location=centre,
        popup="Centre de la carte",
        tooltip="Centre Europe",
        icon=folium.Icon(color='red', icon='star', prefix='fa')
    ).add_to(carte)

    # --- Ajout des marqueurs depuis la liste ---
    if liste:
        cluster = MarkerCluster(name="Datacenters").add_to(carte)
        for item in liste:
            nom, lat, lon = item[0], item[1], item[2]
            info_popup = item[3] if len(item) > 3 else nom

            folium.Marker(
                location=(lat, lon),
                popup=folium.Popup(info_popup, max_width=300),
                tooltip=nom,
                icon=folium.Icon(color='blue', icon='server', prefix='fa')
            ).add_to(cluster)

    # --- Contrôle des calques ---
    folium.LayerControl().add_to(carte)

    # --- Sauvegarde ---
    carte.save(fichier)
    print(f"Carte sauvegardée : {fichier} ({len(liste) if liste else 0} marqueurs)")
    return carte


# ============================================================
def recuperer_datacenters_bdd(fichier_bdd=FICHIER_BDD):
    """
    Récupère dans la BDD tous les datacenters ayant des coordonnées GPS valides.
    Retourne une liste de tuples (nom, lat, lon, popup_html).
    """
    conn = sqlite3.connect(fichier_bdd)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT name, city, country, net_count, ix_count,
               CAST(latitude  AS REAL) AS lat,
               CAST(longitude AS REAL) AS lon
        FROM datacenter
        WHERE latitude  IS NOT NULL AND latitude  != ''
          AND longitude IS NOT NULL AND longitude != ''
          AND CAST(latitude  AS REAL) BETWEEN -90  AND 90
          AND CAST(longitude AS REAL) BETWEEN -180 AND 180
    """)
    rows = c.fetchall()
    conn.close()

    liste = []
    for r in rows:
        popup = (
            f"<b>{r['name']}</b><br>"
            f"Ville : {r['city']} ({r['country']})<br>"
            f"Réseaux connectés : {r['net_count']}<br>"
            f"Points d'échange : {r['ix_count']}"
        )
        liste.append((r['name'], r['lat'], r['lon'], popup))

    print(f"{len(liste)} datacenters avec GPS récupérés.")
    return liste


# ============================================================
if __name__ == "__main__":

    # -- Démo avec la liste exemple --
    print("=== Carte exemple (liste fournie dans le sujet) ===")
    creation_carte(
        liste=Liste_exemple,
        centre=(44.2, 2.5),
        zoom=9,
        fichier=os.path.join(BASE_DIR, "output", "carte_exemple.html")
    )

    # -- Carte complète depuis la BDD --
    print("\n=== Carte complète depuis la base de données ===")
    datacenters = recuperer_datacenters_bdd()
    creation_carte(
        liste=datacenters,
        centre=CENTRE_CARTE,
        zoom=ZOOM_DEPART,
        fichier=FICHIER_CARTE
    )
