
from config import *
from swc_db import *
from swc_helpers import *
from datetime import datetime
from swc_regex_config import *


# Error Messages
ERROR_MSG = "ERROR: Try again"
ERROR_MSG_STATS = "ERROR: Select Stats"
ERROR_MSG_NOT_FOUND = "ERROR: No matching results"
ERROR_MSG_NUM_INV = "ERROR: Invalid number for Min. Played"
ERROR_MSG_NUM_NE = "ERROR: Enter number for Min. Played"

# Menu Selections
SELECT_LIMITS 	= [	('L', 	'Limit'),
					('PL', 	'Pot Limit'),
					('NL', 	'No Limit') ]

SELECT_GAMES 	= [	('HE', 	'Holdem'),
					('O', 	'Omaha'),
					('O8', 	'Omaha Hi-Lo')]

SELECT_SEATS	= [	('HU', 		'2', 'Heads up'), 
					('6max', 	'6', '6 max'), 
					('9max', 	'9', '9 max')]

SELECT_TTYPE 	= [ ('mtt', 		'MTT'), 
					('scheduled', 	'Scheduled'), 
					('sng', 		'SNG'), 
					('krill', 		'Krill'), 
					('turbo', 		'Turbo')]

SELECT_STATS	= [	(0,	'num_hands',	'Summary: Hands'), 
					(0,	'amount_won',	'Summary: Winnings'),
					(1,	'vpip', 		'Preflop: Voluntarily Put chips In Pot (%)'), 
					(1,	'pfr', 			'Preflop: Raise (%)'),
					(1,	'pf3b', 		'Preflop: 3bet (%)'),
					(1,	'f_pf3b', 		'Preflop: Fold to 3bet (%)'),
					(1,	'c_pf3b', 		'Preflop: Call 3bet (%)'),
					(1,	'r_pf3b', 		'Preflop: 4bet (%)'), 
					(1,	'cbet', 		'Flop: Continuation Bet (%)'), 
					(1,	'f_cbet', 		'Flop: Fold to Continuation Bet (%)'), 
					(1,	'c_cbet', 		'Flop: Call Continuation Bet (%)'),
					(1,	'r_cbet', 		'Flop: Raise Continuation Bet (%)'), 
					(1,	'wtsd', 		'Showdown: Went to Showdown (%)'),
					(1,	'wsd', 			'Showdown: Won chips at Showdown (%)')]

SELECT_RANK = [	('amount_won', 'Net Profit'),
				('roi', 'ROI (%)'),
				('percentile', 'Normalized Rank (/100)'),
				('itm', 'ITM (%)')]

stats_map = {
				'amount_won': 	(1, 'Summary: Winnings'),
				'num_hands'	: 	(2, 'Summary: Hands'),
				'vpip'		: 	(3, 'Preflop: Voluntarily Put chips In Pot (%)'),
				'pfr'		: 	(4, 'Preflop: Raise (%)'),
				'pf3b'		: 	(5, 'Preflop: 3Bet (%)'),
				'cbet'		: 	(6, 'Flop: Continuation Bet (%)'),
				'f_pf3b'	: 	(7, 'Preflop: Fold to 3Bet (%)'),
				'c_pf3b'	: 	(8, 'Preflop: Call 3Bet (%)'),
				'r_pf3b'	: 	(9, 'Preflop: 4Bet (%)'),
				'f_cbet'	: 	(10, 'Flop: Fold to Continuation Bet (%)'),
				'c_cbet'	: 	(11, 'Flop: Call Continuation Bet (%)'),
				'r_cbet'	: 	(12, 'Flop: Raise Continuation Bet (%)'),
				'wtsd'		: 	(13, 'Showdown: Went to Showdown (%)'),
				'wsd' 		: 	(14, 'Showdown: Won chips at Showdown (%)') }

stats_percents = (3,4,5,6,7,8,9,10,11,12,13,14)

qualifier_map = {
			'EAND'	: ['!=', 'INTERSECT'],
			'EOR'	: ['!=', 'UNION'],
			'IAND'	: ['=', 'INTERSECT'],
			'IOR'	: ['=', 'UNION'],
			}

def player_search(pname):
	time_start = time()
	qtype = [3,3.1, 3.2]
	ret = {}

	ret['found'] = False
	valid_name = False

	valid_name = bool(RGX_CONF_pname.search(pname))

	if valid_name:
		S = SWC_DB(DB_INFO[0], DB_INFO[1],DB_INFO[2]) 
		S.openConnection()

		S.cur.execute(S.queryStr(-1.1, pname))
		name = S.cur.fetchall()

		if name:
			ret['name'] = name[0][0]
			ret['total_won'] = 0
			ret['found'] = True

			S.cur.execute(S.queryStr(qtype[0], pname))
			ringgames = S.cur.fetchall()
			S.cur.execute(S.queryStr(qtype[1], pname))
			tourneys_graph = S.cur.fetchall()
			
			S.cur.execute(S.queryStr(qtype[2], pname))
			tourneys_table = S.cur.fetchall()
		
		# Ring Games
			z_r = [list(t) for t in zip(*ringgames)]
			if z_r:
				_timestamp, _game, _hands, _won_chips = z_r[0], z_r[1], z_r[2], z_r[3]
				idx = sorted(range(len(_timestamp)), key = _timestamp.__getitem__)

				datetimestamp = []
				timestamp = []
				game = []
				hands = []
				won_chips = []
				won_bb = []
				cum_won_chips = [0]
				cum_won_bb = [0]
				cum_hands = [0]
				game_tables = {}

				dyg_all = ''

				for i in idx:
					dt = str(_timestamp[i])
					datetimestamp.append( dt )
					game.append( _game[i] )
					hands.append( int(_hands[i]) )
					won_chips.append(  _won_chips[i] )
					game_bb = float( _game[i][ _game[i].find('/')+1:]  )
					won_bb.append(  float(_won_chips[i] )/game_bb  )

					cum_won_chips.append( cum_won_chips[-1] + won_chips[-1] )
					cum_won_bb.append( cum_won_bb[-1] + won_bb[-1] )
					cum_hands.append( cum_hands[-1] + hands[-1] )

					dyg_all 	= "%s%s,%s,%s,%s\\n" % ( dyg_all,
													datetimestamp[-1], 
													cum_won_chips[-1], 
													cum_won_bb[-1], 
													cum_hands[-1] )

					if game[-1] in game_tables.keys():
						_gt = game_tables[ game[-1] ]
						game_tables[ game[-1] ] = {	'game': game[-1], 
													'won_chips': _gt['won_chips'] + won_chips[-1] , 
													'won_bb': _gt['won_bb'] + won_bb[-1] , 
													'dt': datetimestamp[-1], 
													'hands': hands[-1]+_gt['hands'] }
					else:
						game_tables[ game[-1] ] = { 
													'game': game[-1], 
													'won_chips': won_chips[-1], 
													'won_bb': won_bb[-1], 
													'dt': datetimestamp[-1], 
													'hands': hands[-1] }
				tmp_tables = {}
				for t in game_tables.keys():
					limit_type = t[:t.find(' ')]
					if limit_type in tmp_tables.keys():
						_t = tmp_tables[ limit_type]
						tmp_tables[ limit_type ] = {'limit_type': limit_type, 
													'l_won': _t['l_won'] + game_tables[t]['won_chips'], 
													'l_hands': _t['l_hands'] + game_tables[t]['hands'],
													'games': _t['games'] + [game_tables[t]] }
					else:	
						tmp_tables[ limit_type ] = {'limit_type': limit_type, 
													'l_won': game_tables[t]['won_chips'], 
													'l_hands': game_tables[t]['hands'],
													'games': [game_tables[t]] }
				# Format hands and btc values
				for k in tmp_tables.keys():
					tmp_tables[k]['l_won'] = '{:20,.2f}'.format( tmp_tables[k]['l_won'] )
					tmp_tables[k]['l_hands'] = '{:20,.0f}'.format( tmp_tables[k]['l_hands'] )
					for j in tmp_tables[k]['games']:
						bb = float( j['game'][ j['game'].find('/')+1:]  )
						j['bb_100'] = '{:20,.2f}'.format(( j['won_chips']/bb ) * ( 100.0/j['hands'] ))
						j['won_chips'] 	= '{:20,.2f}'.format( j['won_chips'] )
						j['won_bb'] 	= '{:20,.2f}'.format( j['won_bb'] )
						j['hands'] 	= '{:20,.0f}'.format( j['hands'] )
						j['_dt'] 	= j['dt']
						j['dt']		= datetime.strptime(j['dt'], "%Y-%m-%d %H:%M:%S").strftime("%A %d. %B %Y")
					_sorted_tables 	= sorted(tmp_tables[k]['games'], key=lambda q: q['won_chips'])	
					sorted_tables 	= sorted(_sorted_tables, key=lambda q: q['_dt'])
					sorted_tables.reverse()
					tmp_tables[k]['games'] = sorted_tables

				tables_r = [tmp_tables[t] for t in tmp_tables.keys() ]

				ret['total_hands'] 		= '{:20,.0f}'.format(cum_hands[-1])
				ret['total_won_ring'] 	= '{:20,.2f}'.format(cum_won_chips[-1])
				ret['total_won'] 		= cum_won_chips[-1] + ret['total_won']
				ret['dygraph_r']		= dyg_all
				ret['tables_r']			= tables_r

		# Tournaments
			dyg_all_t = ''

			z_r = [list(t) for t in zip(*tourneys_graph)]
			if z_r:
				_tourn_name, _timestamp, _won_chips, _buy_in, _num_players, _rank, _roi = z_r[0], z_r[1], z_r[2], z_r[3], z_r[4], z_r[5], z_r[6]
				idx = sorted(range(len(_timestamp)), key = _timestamp.__getitem__)

				datetimestamp = []
				timestamp = []
				num_games = []
				won_chips = []
				buy_in = []
				cum_buy_in = [0]
				cum_won_chips = [0]
				cum_won_roi = [0]
				cum_roiXbuy_in = [0]
				cum_games = [0]			
				
				for i in idx:
					dt = str(_timestamp[i])
					datetimestamp.append( dt )
					num_games.append( 1 )
					won_chips.append(  _won_chips[i] )
					buy_in.append(_buy_in[i])
									
					cum_buy_in.append( cum_buy_in[-1] + buy_in[-1] )
					cum_won_chips.append( cum_won_chips[-1] + won_chips[-1] )
					cum_roiXbuy_in.append( cum_roiXbuy_in[-1] + _buy_in[i]*_roi[i] )
					cum_won_roi.append( float(100 * cum_roiXbuy_in[-1]/(0.00001+cum_buy_in[-1]) ) )
					cum_games.append( cum_games[-1] + num_games[-1] )

					dyg_all_t	= "%s%s,%s,%s,%s\\n" % ( 	dyg_all_t,
															datetimestamp[-1], 
															cum_won_chips[-1], 
															cum_won_roi[-1], 
															cum_games[-1] )
				# Last tourneys table
				ret['last_tourneys'] = []
				num_recent = 0
				for i in reversed(idx):
					num_recent += 1
					if num_recent > 10:
						break
					tmp_last_tourneys = {}
					tmp_last_tourneys['name'] 		= _tourn_name[i]
					tmp_last_tourneys['date'] 		= datetime.strptime(str(_timestamp[i]), "%Y-%m-%d %H:%M:%S").strftime("%A %d. %B %Y")
					tmp_last_tourneys['entrants']	= _num_players[i]
					tmp_last_tourneys['buy_in'] 	= '{:20,.2f}'.format(_buy_in[i] )
					tmp_last_tourneys['won_chips'] 	= '{:20,.1f}'.format(_won_chips[i] )
					tmp_last_tourneys['rank'] 		= '{:20,.0f}'.format(_rank[i] )
					tmp_last_tourneys['roi'] 		= '{:20,.1f}'.format( float(100 *_roi[i]))
					ret['last_tourneys'].append( tmp_last_tourneys )

				# Summary Table
				ret['tables_t'] = []
				for i in range(len(tourneys_table)):
					tmp_tables_t = {}
					tmp_tables_t['num_games'] 	= tourneys_table[i][0]
					tmp_tables_t['buy_in'] 		= '{:20,.2f}'.format( tourneys_table[i][1] )
					tmp_tables_t['net'] 		= '{:20,.2f}'.format( tourneys_table[i][2] )
					tmp_tables_t['roi'] 		= '{:20,.1f}'.format( tourneys_table[i][3]*100 )
					tmp_tables_t['itm'] 		= '{:20,.0f}'.format( tourneys_table[i][4]*100 )
					tmp_tables_t['rank'] 		= '{:20,.0f}'.format( tourneys_table[i][5] )
					ret['tables_t'].append(tmp_tables_t)
				sorted_tables 	= sorted(ret['tables_t'], key=lambda q: q['buy_in'])
				ret['tables_t'] = sorted_tables
				
				ret['dygraph_t']		= dyg_all_t
				ret['tourneys_table']	= tourneys_table
				ret['total_won_tourn'] 	= cum_won_chips[-1]
				ret['total_roi'] 		= '{:20,.1f}'.format(cum_won_roi[-1] )
				ret['total_games'] 		= cum_games[-1]
				ret['total_won'] 		= ret['total_won'] + cum_won_chips[-1]

			#Final formatting
			ret['total_won'] = '{:20,.2f}'.format( ret['total_won'] )
			time_dur = time() - time_start	
			ret['time']	= time_dur
		else:
			ret['name'] = ERROR_MSG_NOT_FOUND
		S.closeConnection()
	else:
		ret['name'] = ERROR_MSG
	return ret


def leaderboard_ring(qd = None):
	S = SWC_DB(DB_INFO[0], DB_INFO[1],DB_INFO[2]) 
	S.openConnection()
	ret = {}
	limit = 20

	# Menu selects
	S.cur.execute(S.queryStr(-20.3))
	ret['select_blinds'] = S.cur.fetchall()
	ret['select_limits'] = SELECT_LIMITS
	ret['select_games'] = SELECT_GAMES
	ret['select_seats'] = SELECT_SEATS

	if qd != None:
		qd['min_blinds'] 	= qd['min_blinds'][0]
		qd['max_blinds'] 	= qd['max_blinds'][0]
		qd['limit_type'] 	= qd['limit_type'][0]
		qd['game_type'] 	= qd['game_type'][0]
		qd['seat_type'] 	= qd['seat_type'][0]
		
		qd['where_qstr'] = ''
		if qd['min_blinds'] != 'All':
			qd['where_qstr'] = qd['where_qstr'] + ' AND big_blind >= %s' % qd['min_blinds']
		if qd['max_blinds'] != 'All':
			qd['where_qstr'] = qd['where_qstr'] + ' AND big_blind <= %s' % qd['max_blinds']					
		if qd['limit_type'] != 'All':
			qd['where_qstr'] = qd['where_qstr'] + " AND limit_type = '%s'" % qd['limit_type']
		if qd['game_type'] != 'All':
			qd['where_qstr'] = qd['where_qstr'] + " AND game_type = '%s'" % qd['game_type']
		if qd['seat_type'] != 'All':
			qd['where_qstr'] = qd['where_qstr'] + " AND seat_type = '%s'" % qd['seat_type']

		_where_str = qd['where_qstr']
		intervals = ['1 day', '1 week', '1 month', '1 year']

		for i in intervals:
			qd['where_qstr'] = _where_str + " AND apprx_dt > (current_date - interval '%s')" % i
			qd['query'] = S.queryStr(10.3) % qd
			S.cur.execute(qd['query'])
			_res= S.cur.fetchall()

			if _res:
				ret['name'] = ''
				_res_lose = [ {'player': r[0], 'chips': '{:20,.2f}'.format( r[1] ) } for r in _res][0:limit]
				ret[ 'lose_' + i.replace(' ','') ] = _res_lose

				_res.reverse()
				_res_win = [ {'player': r[0], 'chips': '{:20,.2f}'.format( r[1] ) } for r in _res][0:limit]
				ret[ 'win_' + i.replace(' ','') ] = _res_win

			else:
				ret['name'] = ERROR_MSG_NOT_FOUND
	S.closeConnection()
	return ret


def leaderboard_tourney(qd = None):
	S = SWC_DB( DB_INFO[0], DB_INFO[1],DB_INFO[2] ) 
	S.openConnection()
	ret = {}
	limit = 20
	# Menu selects
	S.cur.execute(S.queryStr(-20.1))
	select_sch_names = S.cur.fetchall()
	ret['select_sch_names'] = [k[0] for k in select_sch_names]
	S.cur.execute(S.queryStr(-20.2))
	select_buyin= S.cur.fetchall()
	ret['select_buyin'] 	= [k[0] for k in select_buyin]
	ret['select_ttype'] 	= SELECT_TTYPE
	ret['select_limits'] 	= SELECT_LIMITS
	ret['select_games'] 	= SELECT_GAMES
	ret['select_rank'] 		= SELECT_RANK
	ret['select_seats'] 	= SELECT_SEATS

	if qd != None:
		valid_num = False

		qd['min_buyin'] 	= qd['min_buyin'][0]
		qd['max_buyin'] 	= qd['max_buyin'][0]
		qd['rank_type'] 	= qd['rank_type'][0]
		qd['limit_type'] 	= qd['limit_type'][0]
		qd['game_type'] 	= qd['game_type'][0]
		qd['seat_type'] 	= qd['seat_type'][0]
		qd['tourney_type'] 	= qd['tourney_type'][0]
		qd['tourney_name'] 	= qd['tourney_name'][0]
		qd['min_num_played'] = qd['min_num_played'][0]
		qd['max_num_played'] = qd['max_num_played'][0]

		if qd['min_num_played'] and qd['max_num_played']:
			if RGX_CONF_number.search(qd['min_num_played']) and RGX_CONF_number.search(qd['max_num_played']):
				if int(qd['min_num_played']) > 0 and int(qd['max_num_played']) > 0:
					valid_num = True

			if valid_num:
				qd['where_qstr'] = ''
				if qd['min_buyin'] != 'All':
					qd['where_qstr'] = qd['where_qstr'] + ' AND buy_in >= %s' % qd['min_buyin']
				if qd['max_buyin'] != 'All':
					qd['where_qstr'] = qd['where_qstr'] + ' AND buy_in <= %s' % qd['max_buyin']					
				if qd['limit_type'] != 'All':
					qd['where_qstr'] = qd['where_qstr'] + " AND limit_type = '%s'" % qd['limit_type']
				if qd['game_type'] != 'All':
					qd['where_qstr'] = qd['where_qstr'] + " AND game_type = '%s'" % qd['game_type']
				if qd['seat_type'] != 'All':
					qd['where_qstr'] = qd['where_qstr'] + ' AND seats = %s' % qd['seat_type']
				if qd['tourney_type'] != 'All':
					qd['where_qstr'] = qd['where_qstr'] + ' AND %s = true' % qd['tourney_type']
				if qd['tourney_name'] != 'All':
					qd['where_qstr'] = qd['where_qstr'] + " AND tournament_name = '%s'" % qd['tourney_name']

				qd['range_qstr'] = 'WHERE num >= %s' % qd['min_num_played'] + ' AND num <= %s' % qd['max_num_played']
				qd['rank_qstr'] = ''

				if qd['rank_type'] == 'amount_won':
					qd['rank_qstr'] = 'sum(amount_won)'
				elif qd['rank_type'] == 'itm':
					qd['rank_qstr'] = '100*sum(ITM::int)/count(*)::float'
				elif qd['rank_type'] == 'roi':
					qd['rank_qstr'] = '100*sum(roi*buy_in)/(0.0001+sum(buy_in))'
				elif qd['rank_type'] == 'percentile':
					qd['rank_qstr'] = 'sum(Percentile)/count(*)::float'

				intervals = ['1 day', '1 week', '1 month', '1 year']
				_where_str = qd['where_qstr']
			

				for i in intervals:
					ret['colnames'] = tuple(['#', 'Player'] + [k[1] for k in SELECT_RANK if k[0] == qd['rank_type'] ])
					qd['where_qstr'] = _where_str + " AND apprx_dt > (current_date - interval '%s')" % i
					
					qd['query'] = S.queryStr(10.5) % qd
					S.cur.execute(qd['query'])
					_res= S.cur.fetchall()

					if _res:
						ret['name'] = ''
						if qd['rank_type'] == 'percentile':
							_res.reverse()
						_res_lose = [ {'player': r[1], 'chips': '%s' % r[2] } for r in _res][0:limit]
						ret[ 'lose_' + i.replace(' ','') ] = _res_lose

						_res.reverse()
						_res_win = [ {'player': r[1], 'chips': '%s' % r[2] } for r in _res][0:limit]
						ret[ 'win_' + i.replace(' ','') ] = _res_win

					else:
						ret['name'] = ERROR_MSG_NOT_FOUND
			else:
				ret['name'] = ERROR_MSG
		else:
			ret['name'] = ERROR_MSG_NUM_NE
	S.closeConnection()
	return ret


def hud_stats(qd = None):
	ret = {}
	S = SWC_DB(DB_INFO[0], DB_INFO[1],DB_INFO[2]) 
	S.openConnection()

	# Menu selects
	S.cur.execute(S.queryStr(-20.3))
	SELECT_BLINDS= S.cur.fetchall()
	ret['select_blinds'] = SELECT_BLINDS
	ret['select_limits'] = SELECT_LIMITS
	ret['select_games'] = SELECT_GAMES
	ret['select_seats'] = SELECT_SEATS
	ret['select_stats'] = SELECT_STATS

	if qd != None:
		offset = 0.001
		num_res = 10
		char_limit = 200
		results = []

		qd['start_date'] 	= qd['start_date'][0]
		qd['end_date'] 		= qd['end_date'][0]
		qd['min_blinds'] 	= qd['min_blinds'][0]
		qd['max_blinds'] 	= qd['max_blinds'][0]
		qd['limit_type'] 	= qd['limit_type'][0]
		qd['game_type'] 	= qd['game_type'][0]
		qd['seat_type'] 	= qd['seat_type'][0]		
		qd['players'] 		= [str(i.strip().upper()) for i in qd['players'][0].split(',') if i.strip()]

		valid_dt = False
		valid_stats = False
		if len(qd['players']) > 0:
			valid_names = True
		else:
			valid_names = False

		if 'stats_selected' in qd.keys():
			valid_stats = True
			qd['stats_selected'] 	= tuple(qd['stats_selected'])
		else:
			ret['name'] = ERROR_MSG_STATS
		if RGX_CONF_dt.search(qd['start_date']) and RGX_CONF_dt.search(qd['end_date']):
			valid_dt = True
		else: 
			ret['name'] = ERROR_MSG
		for p in qd['players']:
			valid_names = bool(RGX_CONF_pname.search(p)) and valid_names

		if valid_dt == True and valid_names == True and valid_stats == True:
			qd['where_qstr'] = ''
			if qd['min_blinds'] != 'All':
				qd['where_qstr'] = qd['where_qstr'] + ' AND big_blind >= %s' % qd['min_blinds']
			if qd['max_blinds'] != 'All':
				qd['where_qstr'] = qd['where_qstr'] + ' AND big_blind <= %s' % qd['max_blinds']					
			if qd['limit_type'] != 'All':
				qd['where_qstr'] = qd['where_qstr'] + " AND limit_type = '%s'" % qd['limit_type']
			if qd['game_type'] != 'All':
				qd['where_qstr'] = qd['where_qstr'] + " AND game_type = '%s'" % qd['game_type']
			if qd['seat_type'] != 'All':
				qd['where_qstr'] = qd['where_qstr'] + " AND seat_type = '%s'" % qd['seat_type']			

			qd['offset'] = offset

			#player name
			if len(qd['players']) == 1:
				qd['pname'] =  repr(tuple(qd['players'])).replace(',','')
			else:
				qd['pname'] = tuple( [i.upper() for i in qd['players'][0:num_res] ] )

			S.cur.execute(S.queryStr(11.55) % qd)
			_res = S.cur.fetchall()

			if _res:
				result_names = ['Player']
				for k in qd['stats_selected']:
					result_names.append( stats_map[k][1] )
				for r in _res:
					_res_list = [r[0]]
					for k in qd['stats_selected']:
						idx = stats_map[k][0]
						_res_list.append( int(r[idx]) if idx == 2 else \
											'{:20,.2f}'.format( float(r[idx]) ) if idx == 1 else \
											'{:20,.0f}'.format( 100*float(r[idx]) ) if idx in stats_percents else r[idx] )
					results.append( _res_list )
				
				ret['colnames'] = result_names
				ret['results'] = results
			else:
				ret['name'] = ERROR_MSG_NOT_FOUND
		else:
			ret['name'] = ERROR_MSG

	S.closeConnection()
	return ret 

def tourney_search(qd = None):
	# Get fields to fill selection boxes
	ret = {}
	
	S = SWC_DB(DB_INFO[0], DB_INFO[1],DB_INFO[2]) 
	S.openConnection()

	# Menu selects
	S.cur.execute(S.queryStr(-20.1))
	select_sch_names = S.cur.fetchall()
	ret['select_sch_names'] = [k[0] for k in select_sch_names]
	S.cur.execute(S.queryStr(-20.2))
	select_buyin= S.cur.fetchall()
	ret['select_buyin'] = [k[0] for k in select_buyin]
	ret['select_limits'] = SELECT_LIMITS
	ret['select_games'] = SELECT_GAMES
	ret['select_seats'] = SELECT_SEATS
	ret['select_ttype'] = SELECT_TTYPE

	if qd != None:
		valid_dt = False
		valid_names = True
		valid_qualifier = True

		qd['start_date'] 	= qd['start_date'][0]
		qd['end_date'] 		= qd['end_date'][0]
		qd['min_buyin']		= qd['min_buyin'][0]
		qd['max_buyin']		= qd['max_buyin'][0]		
		qd['limit_type'] 	= qd['limit_type'][0]
		qd['game_type'] 	= qd['game_type'][0]
		qd['seat_type'] 	= qd['seat_type'][0]
		qd['tourney_type'] 	= qd['tourney_type'][0]
		qd['tourney_name'] 	= qd['tourney_name'][0]
		qd['players'] 		= [str(i.strip().upper()) for i in qd['players'][0].split(',') if i.strip()]
		
		if RGX_CONF_dt.search(qd['start_date']) and RGX_CONF_dt.search(qd['end_date']):
			valid_dt = True
		else:
			ret['name'] = ERROR_MSG

		if qd['players']:
			if 'inclusion_qualifier' not in qd.keys():
				valid_qualifier = False
				ret['name'] = ERROR_MSG

		for p in qd['players']:
			valid_names = bool(RGX_CONF_pname.search(p)) and valid_names

		if valid_dt == True and valid_names == True and valid_qualifier == True:
			num_res = 10
			base_qstr = ''

			if qd['min_buyin'] != 'All':
				base_qstr = base_qstr + ' AND buy_in >= %s' % qd['min_buyin']
			if qd['max_buyin'] != 'All':
				base_qstr = base_qstr + ' AND buy_in <= %s' % qd['max_buyin']				
			if qd['limit_type'] != 'All':
				base_qstr = base_qstr + " AND limit_type = '%s'" % qd['limit_type']
			if qd['game_type'] != 'All':
				base_qstr = base_qstr + " AND game_type = '%s'" % qd['game_type']
			if qd['seat_type'] != 'All':
				base_qstr = base_qstr + ' AND seats = %s' % qd['seat_type']
			if qd['tourney_type'] != 'All':
				base_qstr = base_qstr + ' AND %s = true' % qd['tourney_type']
			if qd['tourney_name'] != 'All':
				base_qstr = base_qstr + " AND tournament_name = '%s'" % qd['tourney_name']
		
			if qd['players']:
				base_name = ''' SELECT tournament_name 
								FROM Tournament_Summary AS TS INNER JOIN Player_Info AS PI ON (PI.Player_ID = TS.Player_ID) 
								WHERE date_trunc('minute',apprx_dt) >= '%(start_date)s' 
						 		AND date_trunc('minute', apprx_dt) <= '%(end_date)s' AND UPPER(player_name) ''' % qd
				base_date = ''' SELECT apprx_dt 
								FROM Tournament_Summary AS TS INNER JOIN Player_Info AS PI ON (PI.Player_ID = TS.Player_ID) 
								WHERE date_trunc('minute',apprx_dt) >= '%(start_date)s' \
						 		AND date_trunc('minute', apprx_dt) <= '%(end_date)s' AND UPPER(player_name) ''' % qd
				qstr_name = ''
				qstr_date = ''

				qualifier = (qualifier_map[qd['inclusion_qualifier'][0]] if 'inclusion_qualifier' in qd.keys() else [])
				length = min( len(qd['players']), num_res )
				for i in range(length):
					p = qd['players'][i]
					if i != length -1:
						qstr_name = qstr_name + base_name+ qualifier[0] + "'%s'" % p + ' ' + qualifier[1] + ' '
						qstr_date = qstr_date + base_date+ qualifier[0] + "'%s'" % p + ' ' + qualifier[1] + ' '
					else:
						qstr_name = ' AND tournament_name IN (' + qstr_name + base_name+ qualifier[0] + "'%s')" % p 
						qstr_date = ' AND apprx_dt IN (' + qstr_date + base_date+ qualifier[0] + "'%s')" % p 
				base_qstr = base_qstr + qstr_name + qstr_date
			qd['constructed query'] = base_qstr
			qd['query'] = S.queryStr(50.76) % qd
			S.cur.execute(qd['query'])
			tourney_list = S.cur.fetchall()			
			
			zip_tl = [list(t) for t in zip(*tourney_list) ]
			if zip_tl:
				tl_apprx_dt, tl_tournament_name, tl_buy_in, tl_name, tl_rank, tl_amount_won, tl_itm = zip_tl[0], zip_tl[1], zip_tl[2], zip_tl[3], zip_tl[4], zip_tl[5], zip_tl[6]
				
				results = {}
				names = 	{ 	'name': 'Tournament Name', 
								'buy_in': 'Buy in', 
								'player': 'Player Name', 
								'rank': 'Rank', 
								'won': 'Won (chips)', 
								'itm': 'ITM' }
				keys = []
				_info = []

				for i in range(len(tourney_list)):
					tourneyKey = (str(tl_apprx_dt[i]) + tl_tournament_name[i]).replace(' ', '')
					if tourneyKey in results.keys():
						results[tourneyKey].append({	'name': tl_tournament_name[i], 'buy_in': tl_buy_in[i], 
														'player': tl_name[i], 'rank': tl_rank[i], 'won': tl_amount_won[i], 'itm': tl_itm[i] } )
					else:
						results[tourneyKey] = [{	'name': tl_tournament_name[i], 'buy_in': tl_buy_in[i], 
													'player': tl_name[i], 'rank': tl_rank[i], 'won': tl_amount_won[i], 'itm': tl_itm[i] }]
						#keys.append(tourneyKey)
						_info.append({	'name': tl_tournament_name[i], 
										'buy_in': tl_buy_in[i], 
										'key': tourneyKey, 
										'date': datetime.strptime(str(tl_apprx_dt[i]), "%Y-%m-%d %H:%M:%S").strftime("%H:%M %A %d. %B %Y")
									}) 
				#result = [results[k] for k in keys]
				info = []
				for i in _info:
					r = {'tourney_info': results[i['key']] }
					info.append(dict(i.items() + r.items()))
				#ret['tournaments'] = results
				ret['tournament_info'] = info
				ret['NAMES'] = names
			else:
				ret['name'] = ERROR_MSG_NOT_FOUND 
		else:
			ret['name'] = ERROR_MSG
	S.closeConnection()
	return ret



# Experimental

def site_stats():
	qtype = [100.01, 100.02, 100.1, 100.11]
	target = ["sealswithclubs.eu"]
	ret = {}

	S = SWC_DB(DB_INFO[0], DB_INFO[1],DB_INFO[2]) 
	S.openConnection()

	S.cur.execute(S.queryStr(qtype[0]))
	r_uptime = S.cur.fetchall()
	r_uptime = [str(r[0]) for r in r_uptime]
	S.cur.execute(S.queryStr(qtype[1]))
	t_uptime = S.cur.fetchall()
	t_uptime = [str(t[0]) for t in t_uptime]
	S.cur.execute(S.queryStr(qtype[2]))
	t_total = S.cur.fetchall()[0][0]
	S.cur.execute(S.queryStr(qtype[3]))
	r_total = S.cur.fetchall()[0][0]

	start = min(t_uptime + r_uptime)
	# Ring Games
	full_range = getDateSeries(start)
	dyg = ''
	ret['test'] = r_uptime
	up_count = 0
	for i in full_range:
		if i in r_uptime:
			dyg	= "%s%s,%s\\n" % ( dyg, i,1)
			up_count += 1
		else:
			dyg	= "%s%s,%s\\n" % ( dyg, i,0)
	ret['dygraph_r'] = dyg
	ret['r_percent_up'] = '{:20,.2f}'.format(100*float(up_count) / len(full_range))


	# Tournaments
	full_range = getDateSeries(start)
	dyg = ''
	up_count = 0
	for i in full_range:
		if i in t_uptime:
			dyg	= "%s%s,%s\\n" % ( dyg, i,1)
			up_count +=1
		else:
			dyg	= "%s%s,%s\\n" % ( dyg, i,0)
	ret['dygraph_t'] = dyg
	ret['t_percent_up'] = '{:20,.2f}'.format(100*float(up_count) / len(full_range))
	ret['target'] = target[0]
	ret['total_hands'] = '{:20,.0f}'.format(r_total)
	ret['total_games'] = '{:20,.0f}'.format(t_total)
	ret['start_date'] = datetime.strptime(start, "%Y-%m-%d %H:%M:%S").strftime("%A %d. %B %Y")

	S.closeConnection()
	return ret
