# OpenCenter

Projet NSI Terminale — Traitement et visualisation des datacenters européens à partir des données [PeeringDB](https://www.peeringdb.com).

---

## Présentation

Ce projet analyse **2 020 datacenters européens** issus de l'API publique PeeringDB. Il couvre l'ensemble du pipeline de données : acquisition, nettoyage, stockage en base de données, requêtes SQL, cartographie interactive et interface graphique.

| Indicateur | Valeur |
|---|---|
| Enregistrements | 2 020 |
| Pays représentés | 38 |
| Datacenters localisés (GPS) | 2 018 |
| Max réseaux connectés (Digital Realty FRA1-16) | 604 |
| Max points d'échange internet (IX) | 34 |

---

## Structure du projet

```
OpenCenter/
├── data/
│   ├── datacenter.csv          ← Jeu de données nettoyé (Europe, 2 020 lignes)
│   ├── datacenter.sqlite3      ← Base SQLite3 (tables : datacenter, pays)
│   └── pays_europe.csv         ← 46 pays européens (référence pour JOIN)
│
├── scripts/                    ← Pipeline de données (à lancer une seule fois)
│   ├── json_to_csv.py          ← fac-0.json → datacenter.csv
│   ├── clean_csv.py            ← Nettoyage et filtrage Europe
│   ├── csv_to_sqlite.py        ← datacenter.csv → SQLite3
│   └── import_pays.py          ← pays_europe.csv → table pays
│
├── output/                     ← Cartes HTML générées (ignorées par git)
│
├── queries.sql                 ← 15 requêtes SQL commentées
├── db_query.py                 ← Accès Python → base de données
├── carte.py                    ← Cartes Folium (cluster + bulles)
├── jointure.py                 ← Jointure datacenter ⨝ pays + cartes
├── geocode.py                  ← Géocodage des adresses manquantes (Nominatim)
└── interface.py                ← Interface graphique Tkinter
```

---

## Installation

```bash
# 1. Cloner le dépôt
git clone <url-du-depot>
cd OpenCenter

# 2. Créer et activer l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate       # macOS / Linux
# .venv\Scripts\activate        # Windows

# 3. Installer les dépendances
pip install pandas folium geopy certifi
```

---

## Recréer la base de données

> La base `data/datacenter.sqlite3` est incluse dans le dépôt. Ces étapes ne sont nécessaires qu'après une mise à jour du jeu de données.

```bash
# 1. Télécharger le JSON brut depuis PeeringDB
#    URL : https://www.peeringdb.com/api/fac?depth=0
#    → Renommer le fichier en fac-0.json à la racine

# 2. Convertir JSON → CSV
python scripts/json_to_csv.py

# 3. Nettoyer et filtrer (Europe uniquement)
python scripts/clean_csv.py

# 4. Importer dans SQLite3
python scripts/csv_to_sqlite.py
# Option --reset pour recréer la table si elle existe déjà

# 5. Importer la table des pays
python scripts/import_pays.py

# 6. Géocoder les adresses manquantes (~4 min)
python geocode.py
# Option --dry-run --limite 10 pour tester sans modifier la BDD
```

---

## Utilisation

```bash
# Requêtes SQL (affichage dans la console)
python db_query.py

# Générer les cartes (→ output/)
python carte.py
python jointure.py

# Lancer l'interface graphique
python interface.py
```

### Interface graphique

- Panneau gauche : statistiques globales + sélecteur de pays
- Onglet **Datacenters (pays)** : liste des DC du pays sélectionné, triés par nombre de réseaux
- Onglet **Top 20 (réseaux)** : classement des DC les plus connectés d'Europe
- Boutons de génération de cartes (ouverture automatique dans le navigateur)

### Cartes générées

| Fichier | Description |
|---|---|
| `carte_interface_tous.html` | Tous les datacenters (cluster) |
| `carte_bulles_interface.html` | Bulles proportionnelles par pays |
| `carte_fr.html` / `carte_de.html` | Zoom France / Allemagne |

---

## Requêtes SQL notables (`queries.sql`)

```sql
-- Top 5 pays par nombre de datacenters
SELECT country, COUNT(*) AS nb FROM datacenter
GROUP BY country ORDER BY nb DESC LIMIT 5;

-- Datacenter le plus connecté
SELECT name, city, country, MAX(net_count) AS max_reseaux FROM datacenter;

-- Évolution des créations par année
SELECT SUBSTR(created,1,4) AS annee, COUNT(*) AS nb
FROM datacenter GROUP BY annee ORDER BY annee;

-- Jointure : nom complet du pays + densité DC
SELECT p.nom_pays, COUNT(*) AS nb_dc, ROUND(AVG(d.net_count),1) AS moy
FROM datacenter d JOIN pays p ON d.country = p.code_pays
GROUP BY d.country ORDER BY nb_dc DESC;
```

---

## Dépendances

| Package | Usage |
|---|---|
| `pandas` | Nettoyage du CSV |
| `folium` | Cartes HTML interactives |
| `geopy` | Géocodage Nominatim |
| `certifi` | Fix SSL macOS pour geopy |
| `sqlite3` | Accès base de données (stdlib) |
| `tkinter` | Interface graphique (stdlib) |

---

## Source des données

**PeeringDB** — [https://www.peeringdb.com](https://www.peeringdb.com)  
API publique, sans authentification : `https://www.peeringdb.com/api/fac?depth=0`  
Données sous licence [PeeringDB Database License](https://www.peeringdb.com/apidocs/#section/License-and-Acceptable-Use-Policy).
