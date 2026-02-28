import pandas as pd

def remove_specific_row_from_csv(file, column_name, *args):
	'''
	:param file: file to remove the rows from
	:param column_name: The column that determines which row will be 
		   deleted (e.g. if Column == Name and row-*args
		   contains "Gavri", All rows that contain this word will be deleted)
	:param args: Strings from the rows according to the conditions with 
				 the column
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
		raise Exception("Error message....")
		

import os as _os
_BASE = _os.path.dirname(_os.path.abspath(__file__))
remove_specific_row_from_csv(
    _os.path.join(_BASE, "..", "data", "datacenter.csv"),
    "region_continent",
    "Europe"
)

