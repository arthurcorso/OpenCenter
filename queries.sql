-- ============================================================
-- ACTIVITÉ 4 : Requêtes SQL – Base de données Datacenters
-- Jeu de données : PeeringDB – Datacenters européens
-- ============================================================

-- 1. Nombre total de datacenters
SELECT COUNT(*) AS nb_total_datacenters
FROM datacenter;

-- 2. Nombre de datacenters par pays
SELECT country AS pays, COUNT(*) AS nb_datacenters
FROM datacenter
GROUP BY country
ORDER BY nb_datacenters DESC;

-- 3. Top 10 des villes avec le plus de datacenters
SELECT city AS ville, country AS pays, COUNT(*) AS nb_datacenters
FROM datacenter
GROUP BY city, country
ORDER BY nb_datacenters DESC
LIMIT 10;

-- 4. Nombre de datacenters par organisation (top 10)
SELECT org_name AS organisation, COUNT(*) AS nb_datacenters
FROM datacenter
GROUP BY org_name
ORDER BY nb_datacenters DESC
LIMIT 10;

-- 5. Moyenne du nombre de réseaux connectés (net_count)
SELECT ROUND(AVG(net_count), 2) AS moy_net_count,
       MAX(net_count)           AS max_net_count,
       MIN(net_count)           AS min_net_count
FROM datacenter;

-- 6. Datacenters avec le plus de réseaux connectés (TOP 10)
SELECT name AS datacenter, city AS ville, country AS pays, net_count
FROM datacenter
ORDER BY net_count DESC
LIMIT 10;

-- 7. Datacenters avec le plus de points d'échange internet (ix_count)
SELECT name AS datacenter, city AS ville, country AS pays, ix_count
FROM datacenter
ORDER BY ix_count DESC
LIMIT 10;

-- 8. Nombre de datacenters disposant de coordonnées GPS valides
SELECT COUNT(*) AS avec_gps
FROM datacenter
WHERE latitude  IS NOT NULL AND latitude  != ''
  AND longitude IS NOT NULL AND longitude != '';

-- 9. Datacenters sans coordonnées GPS
SELECT COUNT(*) AS sans_gps
FROM datacenter
WHERE latitude  IS NULL OR latitude  = ''
   OR longitude IS NULL OR longitude = '';

-- 10. Répartition par statut
SELECT status, COUNT(*) AS nb
FROM datacenter
GROUP BY status
ORDER BY nb DESC;

-- 11. Évolution des créations : nombre de datacenters créés par année
SELECT SUBSTR(created, 1, 4) AS annee, COUNT(*) AS nb_crees
FROM datacenter
GROUP BY annee
ORDER BY annee;

-- 12. France : nombre de datacenters et moyenne de réseaux
SELECT country AS pays,
       COUNT(*)            AS nb_datacenters,
       ROUND(AVG(net_count), 2) AS moy_reseaux,
       ROUND(AVG(ix_count), 2)  AS moy_ix
FROM datacenter
WHERE country = 'FR';

-- 13. Datacenters en France avec coordonnées GPS
SELECT name AS datacenter, city AS ville, latitude, longitude
FROM datacenter
WHERE country = 'FR'
  AND latitude  IS NOT NULL AND latitude  != ''
  AND longitude IS NOT NULL AND longitude != ''
ORDER BY city;

-- 14. Datacenters créés après 2020
SELECT COUNT(*) AS crees_apres_2020
FROM datacenter
WHERE SUBSTR(created, 1, 4) > '2020';

-- 15. Pays avec plus de 50 datacenters
SELECT country AS pays, COUNT(*) AS nb
FROM datacenter
GROUP BY country
HAVING nb > 50
ORDER BY nb DESC;
