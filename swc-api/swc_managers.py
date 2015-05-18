from config import *
from swc_regex_config import *
from swc_helpers import *
from swc_api import *
from swc_proc import *
from swc_parse import *
from swc_db import *
from datetime import datetime
from time import time, sleep
import hashlib

def createBaseTables():
	dbObj = SWC_DB(DB_INFO[0], DB_INFO[1],DB_INFO[2])
	dbObj.openConnection()

	limits 	= [	{'code': 'L', 'label': 'Limit'}, 
				{'code': 'PL', 'label': 'Pot Limit'}, 
				{'code': 'NL', 'label': 'No Limit'}]
	
	games 	= [	{'code': 'HE', 'label': 'Holdem'}, 
				{'code': 'O', 'label': 'Omaha'}, 
				{'code': 'O8', 'label': 'Omaha Hi-Lo'}]

	seats 	= [	{'code_r': 'HU', 'code_t': '2', 'label': 'Heads up'}, 
				{'code_r': '6max', 'code_t': '6', 'label': '6 max'}, 
				{'code_r': '9max', 'code_t': '9', 'label': '9 max'}]
	
	ttype 	= [ {'code': 'mtt', 'label': 'MTT'}, 
				{'code': 'scheduled', 'label': 'Scheduled'}, 
				{'code': 'sng', 'label': 'SNG'}, 
				{'code': 'krill', 'label': 'Krill'}, 
				{'code': 'turbo', 'label': 'Turbo'}]
	
	stats 	= [	{'percent': 0,	'code': 'num_hands',	'label': 'Summary: Hands', }, 
				{'percent': 0,	'code': 'amount_won',	'label': 'Summary: Winnings'},
				{'percent': 1,	'code': 'vpip', 		'label': 'Preflop: Voluntarily Put chips In Pot (%)'}, 
				{'percent': 1,	'code': 'pfr', 			'label': 'Preflop: Raise (%)'},
				{'percent': 1,	'code': 'pf3b', 		'label': 'Preflop: 3bet (%)'},
				{'percent': 1,	'code': 'f_pf3b', 		'label': 'Preflop: Fold to 3bet (%)'},
				{'percent': 1,	'code': 'c_pf3b', 		'label': 'Preflop: Call 3bet (%)'},
				{'percent': 1,	'code': 'r_pf3b', 		'label': 'Preflop: 4bet (%)'}, 
				{'percent': 1,	'code': 'cbet', 		'label': 'Flop: Continuation Bet (%)'}, 
				{'percent': 1,	'code': 'f_cbet', 		'label': 'Flop: Fold to Continuation Bet (%)'}, 
				{'percent': 1,	'code': 'c_cbet', 		'label': 'Flop: Call Continuation Bet (%)'},
				{'percent': 1,	'code': 'r_cbet', 		'label': 'Flop: Raise Continuation Bet (%)'}, 
				{'percent': 1,	'code': 'wtsd', 		'label': 'Showdown: Went to Showdown (%)'},
				{'percent': 1,	'code': 'wsd', 			'label': 'Showdown: Won chips at Showdown (%)'}]
	
	dbObj.dropTables('Menu_Limits', 'Menu_Games', 'Menu_Tournament_Type', 'Menu_Stats', 'Menu_seats')
	dbObj.cur.execute(dbObj.createStr('Menu_Limits'))
	dbObj.cur.execute(dbObj.createStr('Menu_Games'))
	dbObj.cur.execute(dbObj.createStr('Menu_Tournament_Type'))
	dbObj.cur.execute(dbObj.createStr('Menu_Stats'))
	dbObj.cur.execute(dbObj.createStr('Menu_Seats'))
	dbObj.cur.executemany(dbObj.insertStr('Menu_Limits'), limits)
	dbObj.cur.executemany(dbObj.insertStr('Menu_Games'), games)
	dbObj.cur.executemany(dbObj.insertStr('Menu_Seats'), seats)
	dbObj.cur.executemany(dbObj.insertStr('Menu_Tournament_Type'), ttype)
	dbObj.cur.executemany(dbObj.insertStr('Menu_Stats'), stats)

	dbObj.closeConnection()


def _db_manager( clean_run = False, path = HH_PATH):
	time_start = time()
	file_info = {}
	file_idx = []
	hand_list = []
	history = ''
	hhcount = 0
	tcount = 0

	print "Opening Connection to Database"
	S = SWC_DB(DB_INFO[0], DB_INFO[1],DB_INFO[2])
	file_list = S.parse.getHistoryList(path)
	S.openConnection()

	if clean_run == True:
		S.dropTables('Player_Winnings', 'Hand_Info', 'Hand_Actions', 'Player_Stats', 'File_MD5', 'Player_Summary', 'Tournament_Summary', 'Player_Info')
	else:
		print "START: Fetching File_MD5 records"
		S.cur.execute("SELECT * from File_MD5")
		file_idx = S.cur.fetchall()
		print "END: Fetching File_MD5 records"

	fname_list 	= [i[0] for i in file_idx]
	md5_list 	= [i[1] for i in file_idx]
	pos_list	= [i[2] for i in file_idx]
	
	for txt_file in file_list:
		print "START: Compare Hashes for", txt_file
		with open(txt_file, 'r') as f:
			history = f.read()
			hasher = hashlib.md5()
			hasher.update(history)
			file_info = { 	'name'	: f.name.replace('/', '').replace(' ','').replace('-',''),
							'_name'	: f.name.split('/')[-1],
							'md5'	: hasher.hexdigest(),
							'pos'	: len(history)}
		if file_info['name'] in fname_list:
			fidx = fname_list.index(file_info['name'])
			if file_info['md5'] == md5_list[fidx]:
				continue
			else:
				hasher = hashlib.md5()
				hasher.update(history[:pos_list[fidx]])
				if hasher.hexdigest() == md5_list[fidx]:
					history = history[pos_list[fidx]:]
					print "\n\nNew HH in %s"  % file_info['name']
		print "END: Compare Hashes for", txt_file
		
		if RGX_CONF_ringHH.search(file_info['_name']):
			idx = S.parse.parseHistory(history)
			h_attr = []
			p_attr = []
			s_attr = []
			p_smry = []

			for i in idx:
				hand = history[ i[0]: i[1] ]
				hand_dict = S.parse.parseHand(hand)

				if (hand_dict):
					attr = S.getHandAttributes(hand_dict)
					hand_attr = attr[0]
					player_attr = attr[1]
					stats_attr = attr[2]
					player_summary = attr[3]

					hnum = int(hand_attr[0]['hand number'])
					hhcount +=1
					print i, hnum, hhcount, file_info['name'], datetime.now()
					h_attr = h_attr + hand_attr
					p_attr = p_attr + player_attr
					s_attr = s_attr + stats_attr
					p_smry = p_smry + player_summary

			#S.cur.execute(S.createStr('Player_Summary'))
			S.cur.execute(S.createStr('Player_Info'))
			S.cur.execute(S.createStr('Player_Winnings'))
			S.cur.execute(S.createStr('Hand_Info'))
			S.cur.execute(S.createStr('Player_Stats'))
	
			if not clean_run:
				for p in p_smry:
					S.cur.execute(S.updateStr('Player_Summary'), p)
					S.cur.execute(S.insertStr('Player_Summary'), p)
					
			S.cur.executemany(S.insertStr('Hand_Info'), h_attr)
			S.cur.executemany(S.insertStr('Player_Info'), p_attr)
			S.con.commit()
			S.cur.executemany(S.insertStr('Player_Winnings'), p_attr)
			S.cur.executemany(S.insertStr('Player_Stats'), s_attr)
		
		elif RGX_CONF_tourneyHH.search(file_info['_name']):
			trny_summary = []
			idx = S.parse.parseHistory(history, 'T')
			for i in idx:
				tourney_history = history[ i[0]: i[1] ]
				if (tourney_history):
					tcount +=1
					print i, tcount, file_info['name'], datetime.now()
					trny_summary = trny_summary + S.parse.parseTourney(tourney_history)
			S.cur.execute(S.createStr('Player_Info'))
			S.cur.execute(S.createStr('Tournament_Summary'))
			S.cur.executemany(S.insertStr('Player_Info'), trny_summary)
			S.cur.executemany(S.insertStr('Tournament_Summary'), trny_summary)

		S.cur.execute(S.createStr('File_MD5'))
		S.cur.execute(S.updateStr('File_MD5'), file_info)
		S.cur.execute(S.insertStr('File_MD5'), file_info)

	S.con.commit()

	if clean_run:
		print "joining..", time() - time_start
		S.cur.execute(S.joinStr(0))
	S.closeConnection()
	print time() - time_start

	return time() - time_start
	

def db_manager(mins= 5000, init = False):
	print "Options:", mins, init
	if init ==True:
		createBaseTables()
		_db_manager(True)

	timeout = time() + 60*mins
	while time() < timeout:
		_db_manager()
		sleep(2)
		print "Time Elapsed: %.2f mins" % ((timeout - time() )/60.0)


# streamtype: Tournaments, Ring Games, Logins, Chat
def stream_manager(mins, streamtype, account_num):
	import sys
	if streamtype == 'All':
		streamtype= ['T', 'R', 'L', 'C']

	P 		= SWC_PROC( SWC_USERNAME[account_num], SWC_PASSWORD)
	timeout = time() + mins*60

	if 'R' in streamtype:
		open_tables 	= list()
		lines 			= dict()
		active_Rtables 	= set()
		reset_lines 	= ['', False, False, '']
	if 'T' in streamtype:
		tourney_info	= dict()
		selected_tourneys				= list()
		time_last_select				= time()
		tourney_info['selected queue'] 	= set([])
		tourney_info['active tables']	= set([])
		tourney_info['tracked tables'] 	= {}
		tourney_info['last tourney time'] = time()
		tourney_info['last tourney name'] = ''
		t_resolution = 0.1
	if 'L' in streamtype:
		logins 				= set()
		l_resolution = 0
	
	while time() < timeout:
		#try:
		stream = P.stream()
		
		# LOGIN TRACKING
		if 'L' in streamtype:
			logins = P.update_Logins(stream, logins)

		# CHAT TRACKING
		if 'C' in streamtype:
			P.History_Chat(stream)

		# RING GAME TRACKING
		if 'R' in streamtype:
			# Open Active Ring Game Tables
			active_Rtables 	= P.update_RingGameTables(stream, active_Rtables)
			to_open 		= active_Rtables - set(open_tables)
			to_close 		= set(open_tables) - active_Rtables
		
			for t in to_open:
				P.sendOpenTable('R', t)
				open_tables.append(t)
				print "open %s | %s" % (t, len(open_tables))
				lines[t] = reset_lines[:]
			for t in to_close:
				P.sendCloseTable('R',t)
				open_tables.remove(t)
				lines[t] = reset_lines[:]
				print "close %s | %s" % (t, len(open_tables))
			P.History_RingGame(stream, lines)

		# TOURNAMENT TRACKING
		if 'T' in streamtype:
			# Open Active Tournament Tables
			tourney_info['active tables'] 	= P.update_TournamentTables(stream, tourney_info['active tables'])
			if time() - time_last_select > t_resolution:
				for t in tourney_info['active tables']:
					if t not in tourney_info['selected queue']:
						P.sendTableInfo('T', t)
						tourney_info['selected queue'] = tourney_info['selected queue'] | set([t])
						time_last_select = time()
			P.History_TournamentTables(stream, tourney_info)

	P.closeConnection()


def trackFileChanges(dir = HH_PATH):
	mins = 2
	file_info = {}
	S = SWC_PARSE()	
	changes = {}
	changes['R'] = True
	changes['T'] = True

	while changes['R']: #and changes['T']:
		changes['R'] = False
		sleep(mins*60)
		file_list = S.getHistoryList(dir)
		print "--Changes Found--"
		# Initialize Hashes
		for txt_file in file_list:
			ftype = ''
			with open(txt_file, 'r') as f:
				fname = f.name.split('/')[-1] 
				if RGX_CONF_ringHH.search(fname):
					ftype = 'R'
				elif RGX_CONF_tourneyHH.search(fname):
					ftype = 'T'
				if ftype:
					history = f.read()
					hasher 	= hashlib.md5()
					hasher.update(history)
					name 	= f.name.replace('/', '').replace(' ','').replace('-','')
					fhash 	= hasher.hexdigest()
					if name in file_info.keys():
						if fhash != file_info[name]:
							changes[ftype] = True or changes[ftype]
							file_info[name] = fhash
						else:
							changes[ftype] = False or changes[ftype]
					else:
						file_info[name] = fhash
						changes[ftype] = True or changes[ftype]
		

def stream_all_process(mins):
	try:
		stream_manager(mins,['T', 'R'],0)
	except:
		sleep(15)
		print "Process Exception"


def timer_process():
	sleep(20)


