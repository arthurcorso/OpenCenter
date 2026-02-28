# Note : fac-0.json est le fichier source brut téléchargé depuis PeeringDB.
# Pour le re-télécharger : https://www.peeringdb.com/api/fac?depth=0
import json
import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, '..', 'fac-0.json')) as jf:
    d = json.load(jf)

Ed = d['data']

df = open(os.path.join(BASE_DIR, '..', 'data', 'datacenter.csv'), 'w')

cw = csv.writer(df)

c = 0

for emp in Ed:
    if c == 0:

        # Writing headers of CSV file
        h = emp.keys()
        cw.writerow(h)
        c += 1

    # Writing data of CSV file
    cw.writerow(emp.values())

df.close()
