import pandas as pd

def remove_specific_row_from_csv(file, column_name, *args):
	'''
	Enlève les lignes d'un fichier csv qui ont une valeur spécifique dans une colonne donnée.
	Exemple : remove_specific_row_from_csv("data/datacenter.csv", "region_continent
", "Europe") enlèvera toutes les lignes où la colonne "region_continent" a la valeur "Europe".

	'''
	row_to_remove = []
	for row_name in args:
		row_to_remove.append(row_name)
	try:
		df = pd.read_csv(file)
		df = df.drop(columns=['campus_id', 'name_long','tech_email','tech_phone','available_voltage_services', 'diverse_serving_substations','property','status_dashboard','rencode','npanxx','logo','floor','suite'])
		for row in row_to_remove:
			df = df[eval("df.{}".format(column_name)) == row]
		df.to_csv(file, index=False)
	except Exception  as e:
		raise Exception("Oh nannnnn une erreur : {}".format(e))
		

import os as _os
_BASE = _os.path.dirname(_os.path.abspath(__file__))
remove_specific_row_from_csv(
    _os.path.join(_BASE, "..", "data", "datacenter.csv"),
    "region_continent",
    "Europe"
)

