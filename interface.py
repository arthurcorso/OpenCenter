# ============================================================
# ACTIVITÉ 8 : Interface graphique Tkinter – OpenCenter
# Gestion et visualisation des datacenters européens
# ============================================================

import sqlite3
import webbrowser
import os
import tkinter as tk
from tkinter import ttk, messagebox
import folium
from folium.plugins import MarkerCluster

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
FICHIER_BDD   = os.path.join(BASE_DIR, "data",   "datacenter.sqlite3")
OUTPUT_DIR    = os.path.join(BASE_DIR, "output")
CENTRE_EUROPE = (50.0, 15.0)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# FONCTIONS UTILITAIRES BDD
# ============================================================

def get_connexion():
    conn = sqlite3.connect(FICHIER_BDD)
    conn.row_factory = sqlite3.Row
    return conn


def get_stats_globales():
    conn = get_connexion()
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(*)                  AS total,
               ROUND(AVG(net_count), 1)  AS moy_reseau,
               MAX(net_count)            AS max_reseau,
               ROUND(AVG(ix_count), 1)   AS moy_ix,
               MAX(ix_count)             AS max_ix,
               SUM(CASE WHEN latitude!='' AND latitude IS NOT NULL THEN 1 ELSE 0 END) AS avec_gps
        FROM datacenter
    """)
    row = c.fetchone()
    conn.close()
    return row


def get_liste_pays():
    conn = get_connexion()
    c = conn.cursor()
    try:
        c.execute("""
            SELECT p.code_pays, p.nom_pays, COUNT(d.id) AS nb
            FROM pays p
            LEFT JOIN datacenter d ON d.country = p.code_pays
            GROUP BY p.code_pays
            ORDER BY p.nom_pays
        """)
    except sqlite3.OperationalError:
        c.execute("""
            SELECT country AS code_pays, country AS nom_pays, COUNT(*) AS nb
            FROM datacenter GROUP BY country ORDER BY country
        """)
    rows = c.fetchall()
    conn.close()
    return rows


def get_datacenters_pays(code_pays):
    conn = get_connexion()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, city, net_count, ix_count,
               CAST(latitude  AS REAL) AS lat,
               CAST(longitude AS REAL) AS lon,
               website
        FROM datacenter
        WHERE country = ?
        ORDER BY net_count DESC
    """, (code_pays,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_top_dc(n=20):
    conn = get_connexion()
    c = conn.cursor()
    c.execute("""
        SELECT name, city, country, net_count, ix_count
        FROM datacenter
        ORDER BY net_count DESC
        LIMIT ?
    """, (n,))
    rows = c.fetchall()
    conn.close()
    return rows


# ============================================================
# GÉNÉRATION DE CARTES
# ============================================================

def generer_carte_tous(fichier=None):
    if fichier is None:
        fichier = os.path.join(OUTPUT_DIR, "carte_interface_tous.html")
    conn = get_connexion()
    c = conn.cursor()
    c.execute("""
        SELECT name, city, country, net_count, ix_count, website,
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

    carte = folium.Map(location=CENTRE_EUROPE, zoom_start=5,
                       attr='© Contributeurs OpenStreetMap')
    cluster = MarkerCluster(name="Datacenters").add_to(carte)
    for r in rows:
        folium.Marker(
            location=(r['lat'], r['lon']),
            popup=folium.Popup(
                f"<b>{r['name']}</b><br>{r['city']} ({r['country']})<br>"
                f"Réseaux : {r['net_count']} | IX : {r['ix_count']}", max_width=250),
            tooltip=r['name'],
            icon=folium.Icon(color='blue', icon='server', prefix='fa')
        ).add_to(cluster)
    folium.LayerControl().add_to(carte)
    carte.save(fichier)
    return fichier, len(rows)


def generer_carte_pays(code_pays, nom_pays, fichier=None):
    if fichier is None:
        fichier = os.path.join(OUTPUT_DIR, f"carte_{code_pays.lower()}_interface.html")
    conn = get_connexion()
    c = conn.cursor()
    c.execute("""
        SELECT name, city, net_count, ix_count, website,
               CAST(latitude  AS REAL) AS lat,
               CAST(longitude AS REAL) AS lon
        FROM datacenter
        WHERE country = ?
          AND latitude  IS NOT NULL AND latitude  != ''
          AND longitude IS NOT NULL AND longitude != ''
          AND CAST(latitude  AS REAL) BETWEEN -90  AND 90
          AND CAST(longitude AS REAL) BETWEEN -180 AND 180
    """, (code_pays,))
    rows = c.fetchall()
    conn.close()
    if not rows:
        return None, 0
    centre_lat = sum(r['lat'] for r in rows) / len(rows)
    centre_lon = sum(r['lon'] for r in rows) / len(rows)
    carte = folium.Map(location=(centre_lat, centre_lon), zoom_start=6,
                       attr='© Contributeurs OpenStreetMap')
    cluster = MarkerCluster(name=f"DC {nom_pays}").add_to(carte)
    for r in rows:
        folium.Marker(
            location=(r['lat'], r['lon']),
            popup=folium.Popup(
                f"<b>{r['name']}</b><br>{r['city']}<br>"
                f"Réseaux : {r['net_count']} | IX : {r['ix_count']}", max_width=250),
            tooltip=r['name'],
            icon=folium.Icon(color='red', icon='server', prefix='fa')
        ).add_to(cluster)
    folium.LayerControl().add_to(carte)
    carte.save(fichier)
    return fichier, len(rows)


# ============================================================
# INTERFACE TKINTER
# ============================================================

class AppOpenCenter(tk.Tk):
    """Fenêtre principale de l'application OpenCenter."""

    # ---- Palette de couleurs -----------------------------------
    BG        = "#1e1e2e"
    BG_PANEL  = "#2a2a3e"
    FG        = "#cdd6f4"
    ACCENT    = "#89b4fa"
    GREEN     = "#a6e3a1"
    RED       = "#f38ba8"
    YELLOW    = "#f9e2af"
    BORDER    = "#45475a"

    def __init__(self):
        super().__init__()
        self.title("OpenCenter – Datacenters Européens")
        self.geometry("1100x700")
        self.configure(bg=self.BG)
        self.resizable(True, True)

        self._style()
        self._build_ui()
        self._charger_stats()
        self._charger_pays()

    # ----------------------------------------------------------
    def _style(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure(".", background=self.BG, foreground=self.FG,
                        font=("Segoe UI", 10))
        style.configure("TFrame",  background=self.BG)
        style.configure("Panel.TFrame", background=self.BG_PANEL,
                        relief="flat", borderwidth=1)
        style.configure("TLabel",  background=self.BG, foreground=self.FG)
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"),
                        foreground=self.ACCENT, background=self.BG)
        style.configure("Stat.TLabel", font=("Segoe UI", 11),
                        foreground=self.FG, background=self.BG_PANEL)
        style.configure("StatVal.TLabel", font=("Segoe UI", 16, "bold"),
                        foreground=self.GREEN, background=self.BG_PANEL)
        style.configure("TButton", font=("Segoe UI", 10, "bold"),
                        background=self.ACCENT, foreground="#1e1e2e",
                        borderwidth=0, padding=6)
        style.map("TButton",
                  background=[("active", "#74c7ec"), ("pressed", "#89dceb")])
        style.configure("Treeview", background=self.BG_PANEL,
                        foreground=self.FG, fieldbackground=self.BG_PANEL,
                        rowheight=24, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=self.BORDER,
                        foreground=self.ACCENT, font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#313244")])
        style.configure("TCombobox", fieldbackground=self.BG_PANEL,
                        background=self.BG_PANEL, foreground=self.FG)

    # ----------------------------------------------------------
    def _build_ui(self):
        # --- En-tête ---
        header = ttk.Frame(self)
        header.pack(fill="x", padx=16, pady=(14, 4))
        ttk.Label(header, text="🌍  OpenCenter",
                  style="Title.TLabel",
                  font=("Segoe UI", 18, "bold")).pack(side="left")
        ttk.Label(header,
                  text="Visualisation des datacenters européens (PeeringDB)",
                  foreground=self.BORDER,
                  background=self.BG).pack(side="left", padx=12, pady=6)

        # --- Séparateur ---
        sep = tk.Frame(self, height=1, bg=self.BORDER)
        sep.pack(fill="x", padx=16)

        # --- Corps principal (2 colonnes) ---
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=16, pady=10)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        # ---- Colonne gauche : stats + filtres ----
        left = ttk.Frame(body, style="Panel.TFrame")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ttk.Label(left, text="Statistiques globales",
                  foreground=self.ACCENT, background=self.BG_PANEL,
                  font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 4))

        self.frame_stats = ttk.Frame(left, style="Panel.TFrame")
        self.frame_stats.pack(fill="x", padx=10, pady=4)

        ttk.Label(left, text="Filtrer par pays",
                  foreground=self.ACCENT, background=self.BG_PANEL,
                  font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(14, 4))

        self.combo_pays = ttk.Combobox(left, state="readonly", width=28)
        self.combo_pays.pack(padx=10, pady=4, fill="x")
        self.combo_pays.bind("<<ComboboxSelected>>", self._on_pays_change)

        btn_frame = ttk.Frame(left, style="Panel.TFrame")
        btn_frame.pack(fill="x", padx=10, pady=6)

        ttk.Button(btn_frame, text="Carte ce pays",
                   command=self._carte_pays).pack(fill="x", pady=3)
        ttk.Button(btn_frame, text="Carte tous les DC",
                   command=self._carte_tous).pack(fill="x", pady=3)
        ttk.Button(btn_frame, text="Carte par pays (bulles)",
                   command=self._carte_bulles).pack(fill="x", pady=3)

        # ---- Colonne droite : tableaux ----
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        # Onglets
        self.notebook = ttk.Notebook(right)
        self.notebook.grid(row=0, column=0, sticky="nsew", rowspan=2)
        right.rowconfigure(0, weight=1)

        # Tab 1 : Datacenters du pays sélectionné
        self.tab_pays = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_pays, text="  Datacenters (pays)  ")
        self._build_tree_pays()

        # Tab 2 : Top 20 mondial
        self.tab_top = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_top, text="  Top 20 (réseaux)  ")
        self._build_tree_top()

        # --- Barre de statut ---
        self.status_var = tk.StringVar(value="Prêt")
        status_bar = tk.Label(self, textvariable=self.status_var,
                              bg=self.BORDER, fg=self.FG,
                              anchor="w", padx=10, pady=3,
                              font=("Segoe UI", 9))
        status_bar.pack(fill="x", side="bottom")

    # ----------------------------------------------------------
    def _build_tree_pays(self):
        cols = ("name", "city", "net_count", "ix_count")
        self.tree_pays = ttk.Treeview(self.tab_pays, columns=cols,
                                      show="headings", selectmode="browse")
        for col, header, w in [
            ("name",      "Nom",           300),
            ("city",      "Ville",         130),
            ("net_count", "Réseaux",        80),
            ("ix_count",  "IX",             60),
        ]:
            self.tree_pays.heading(col, text=header)
            self.tree_pays.column(col, width=w, anchor="w")

        sb = ttk.Scrollbar(self.tab_pays, orient="vertical",
                           command=self.tree_pays.yview)
        self.tree_pays.configure(yscrollcommand=sb.set)
        self.tree_pays.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _build_tree_top(self):
        cols = ("name", "city", "country", "net_count", "ix_count")
        self.tree_top = ttk.Treeview(self.tab_top, columns=cols,
                                     show="headings", selectmode="browse")
        for col, header, w in [
            ("name",      "Nom",     280),
            ("city",      "Ville",   120),
            ("country",   "Pays",     60),
            ("net_count", "Réseaux",  80),
            ("ix_count",  "IX",       60),
        ]:
            self.tree_top.heading(col, text=header)
            self.tree_top.column(col, width=w, anchor="w")

        sb = ttk.Scrollbar(self.tab_top, orient="vertical",
                           command=self.tree_top.yview)
        self.tree_top.configure(yscrollcommand=sb.set)
        self.tree_top.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Remplissage immédiat
        for r in get_top_dc(20):
            self.tree_top.insert("", "end",
                                 values=(r['name'], r['city'], r['country'],
                                         r['net_count'], r['ix_count']))

    # ----------------------------------------------------------
    def _charger_stats(self):
        s = get_stats_globales()
        donnees = [
            ("Total datacenters",    s['total'],      self.GREEN),
            ("Avec coordonnées GPS", s['avec_gps'],   self.ACCENT),
            ("Moy. réseaux conn.",   s['moy_reseau'], self.YELLOW),
            ("Max réseaux conn.",    s['max_reseau'], self.RED),
            ("Moy. pts d'échange",   s['moy_ix'],     self.YELLOW),
        ]
        for key, val, color in donnees:
            row = ttk.Frame(self.frame_stats, style="Panel.TFrame")
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=key, style="Stat.TLabel").pack(anchor="w")
            tk.Label(row, text=str(val), fg=color, bg=self.BG_PANEL,
                     font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=4)

    def _charger_pays(self):
        self._pays_data = get_liste_pays()
        labels = [f"{r['nom_pays']} ({r['code_pays']}) – {r['nb']} DC"
                  for r in self._pays_data]
        self.combo_pays['values'] = labels
        if labels:
            self.combo_pays.current(0)
            self._on_pays_change(None)

    # ----------------------------------------------------------
    def _on_pays_change(self, _event):
        idx = self.combo_pays.current()
        if idx < 0:
            return
        code = self._pays_data[idx]['code_pays']
        rows = get_datacenters_pays(code)
        self.tree_pays.delete(*self.tree_pays.get_children())
        for r in rows:
            self.tree_pays.insert("", "end",
                                  values=(r['name'], r['city'],
                                          r['net_count'], r['ix_count']))
        self.status_var.set(f"{len(rows)} datacenters chargés pour {code}")

    # ----------------------------------------------------------
    def _ouvrir_carte(self, fichier):
        path = os.path.abspath(fichier)
        webbrowser.open(f"file://{path}")
        self.status_var.set(f"Carte ouverte : {fichier}")

    def _carte_pays(self):
        idx = self.combo_pays.current()
        if idx < 0:
            return
        r = self._pays_data[idx]
        self.status_var.set("Génération de la carte en cours…")
        self.update()
        fichier, nb = generer_carte_pays(r['code_pays'], r['nom_pays'])
        if fichier:
            self._ouvrir_carte(fichier)
            self.status_var.set(f"Carte {r['nom_pays']} : {nb} marqueurs → {fichier}")
        else:
            messagebox.showwarning("Avertissement",
                                   "Aucun datacenter avec GPS pour ce pays.")
            self.status_var.set("Aucun point GPS disponible.")

    def _carte_tous(self):
        self.status_var.set("Génération carte globale…")
        self.update()
        fichier, nb = generer_carte_tous()
        self._ouvrir_carte(fichier)
        self.status_var.set(f"Carte globale : {nb} marqueurs → {fichier}")

    def _carte_bulles(self):
        self.status_var.set("Génération carte bulles par pays…")
        self.update()
        try:
            from jointure import carte_par_pays
            f = os.path.join(OUTPUT_DIR, "carte_bulles_interface.html")
            carte_par_pays(f)
            self._ouvrir_carte(f)
            self.status_var.set("Carte bulles générée.")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))


# ============================================================
if __name__ == "__main__":
    app = AppOpenCenter()
    app.mainloop()
