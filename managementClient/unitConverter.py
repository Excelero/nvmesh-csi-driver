#!/usr/bin/env python

def convertUnitToBytes(unit):
	print("4")
	if isinstance(unit, int) or isinstance(unit, long):
		return unit

	if str.isdigit(unit):
		return long(unit)

	unitChar = unit[-1:]
	unit = unit[:-1]

	if unitChar in 'kK':
		factor = 1
	elif unitChar in 'mM':
		factor = 2
	elif unitChar in 'gG':
		factor = 3
	elif unitChar in 'tT':
		factor = 4
	elif unitChar in 'pP':
		factor = 5
	else:
		assert unit, "Invalid capacity unit {}".format(unit)
		raise ValueError

	return int(unit) * 1024 ** factor
