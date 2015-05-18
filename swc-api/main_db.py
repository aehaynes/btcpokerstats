#!/usr/bin/python2.7
import sys
from swc_managers import db_manager

if __name__ == '__main__':
	if len(sys.argv) > 2:
		db_manager(mins = float(sys.argv[1]), init = bool(sys.argv[2]))
	elif len(sys.argv) > 1:
		db_manager(mins = float(sys.argv[1]))
	else:
		db_manager(init=True)

