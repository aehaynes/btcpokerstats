#!/usr/bin/python2.7

import os
import re
import sys
import re
import mmap
from swc_regex_config import *
from swc_helpers import _epoch


class SWC_PARSE:
	# Parses hand history and returns tuples indexing lines of valid hands
	def getHistoryList(self, hh_dir):
		file_list = []
		for root,dirs,files in os.walk(hh_dir):
			for file in files:
				if file.endswith(".txt"):
					f = os.path.join(root, file)
					file_list.append( str(f) + os.linesep.strip('\n') )
		return file_list

	def parseHistory(self, hh, htype = 'R'):
		hand_idx = 	[]
		nn_idx 	 = 	[0] + [l.start() for l in re.finditer('\n\n', hh)] + [len(hh)]

		for i in range( len(nn_idx) - 1 ):
			start 	= nn_idx[i]
			end 	= nn_idx[i+1]

			if htype =='R':
				p_hand 	= hh[start:end]
				h_idx 	= self.__hasHand(p_hand)
				if (h_idx):
					hand_idx.append([start+h_idx[0], start+h_idx[1]])
			if htype == 'T':
				hand_idx.append([start, end])

		return hand_idx

	# Parses hand to determine if valid. Returns dictionary hand fields
	def parseHand(self, hand):
		hand_dict = dict()
		if ([m.groupdict() for m in RGX_CONF_table.finditer(hand)]):
			hand_dict = {
				'info' 		: [m.groupdict() for m in RGX_CONF_info.finditer(hand)][0],
				'buyin'		: [m.groupdict() for m in RGX_CONF_buyin.finditer(hand)][0], 
				'game type'	: [m.groupdict() for m in RGX_CONF_table.finditer(hand)][0],
				'players' 	: [m.groupdict() for m in RGX_CONF_players.finditer(hand)],
				'dealer'	: [m.groupdict() for m in RGX_CONF_dealer.finditer(hand)][0],
				'sb'		: [m.groupdict() for m in RGX_CONF_sb.finditer(hand)],
				'bb'		: [m.groupdict() for m in RGX_CONF_bb.finditer(hand)],
				'sbbb'		: [m.groupdict() for m in RGX_CONF_sbbb.finditer(hand)],
				'winnings'	: [m.groupdict() for m in RGX_CONF_winner.finditer(hand)],
				'hero'		: [m.groupdict() for m in RGX_CONF_hero.finditer(hand)],
				'refund'	: [m.groupdict() for m in RGX_CONF_refund.finditer(hand)],
				'preflop' 	: RGX_CONF_preflop.search(hand),
				'flop'		: RGX_CONF_flop.search(hand),
				'turn'		: RGX_CONF_turn.search(hand),
				'river'		: RGX_CONF_river.search(hand),
				'showdown' 	: RGX_CONF_sd.search(hand),
				'rake'		: RGX_CONF_rake.search(hand) }

		if ( self.__isValidHand(hand_dict) ):
			#preflop actions
			if (hand_dict['flop']):
				h = hand[ hand_dict['preflop'].end():hand_dict['flop'].start() ]
				hand_dict['actions preflop']  = [m.groupdict() for m in RGX_CONF_action.finditer(h)]
				hand_dict['cards flop'] = hand_dict['flop'].groups()[0]
				#flop actions
				if (hand_dict['turn']):
					h = hand[ hand_dict['flop'].end():hand_dict['turn'].start() ]
					hand_dict['actions flop']  = [m.groupdict() for m in RGX_CONF_action.finditer(h)]
					hand_dict['cards turn'] = hand_dict['turn'].groups()[0]
					#turn actions
					if (hand_dict['river']):
						h = hand[ hand_dict['turn'].end():hand_dict['river'].start() ]
						hand_dict['actions turn']  = [m.groupdict() for m in RGX_CONF_action.finditer(h)]
						hand_dict['cards river'] = hand_dict['river'].groups()[0]
						#river actions
						if (hand_dict['river']):
							h = hand[ hand_dict['river'].end():hand_dict['rake'].start() ]
							hand_dict['actions river'] = [m.groupdict() for m in RGX_CONF_action.finditer(h)]
							# shown hands
							if (hand_dict['showdown']):
								hand_dict['cards showdown'] = hand_dict['showdown'].groups()[0]
								hand_dict['cards shown'] = [m.groupdict() for m in RGX_CONF_shown.finditer(h)]
							else:
								hand_dict['cards showdown'] = ''
								hand_dict['cards shown'] = ''
						else:
							hand_dict['actions river'] = []
							hand_dict['cards showdown'] = ''
							hand_dict['cards shown'] = ''
					else:
						h = hand[ hand_dict['turn'].end():hand_dict['rake'].start() ]
						hand_dict['actions turn'] = [m.groupdict() for m in RGX_CONF_action.finditer(h)]
						hand_dict['cards river'] = ''
						hand_dict['actions river'] = []
						hand_dict['cards showdown'] = ''
						hand_dict['cards shown'] = ''
				else:
					h = hand[ hand_dict['flop'].end():hand_dict['rake'].start() ]
					hand_dict['actions flop'] = [m.groupdict() for m in RGX_CONF_action.finditer(h)]
					hand_dict['cards turn'] = ''
					hand_dict['actions turn'] = []
					hand_dict['cards river'] = ''
					hand_dict['actions river'] = []
					hand_dict['cards showdown'] = ''
					hand_dict['cards shown'] = ''
			else:
				h = hand[ hand_dict['preflop'].end():hand_dict['rake'].start() ]
				hand_dict['actions preflop'] = [m.groupdict() for m in RGX_CONF_action.finditer(h)]
				hand_dict['cards flop'] = ''
				hand_dict['actions flop'] = []
				hand_dict['cards turn'] = ''
				hand_dict['actions turn'] = []
				hand_dict['cards river'] = ''
				hand_dict['actions river'] = []
				hand_dict['cards showdown'] = ''
				hand_dict['cards shown'] = ''
			hand_dict['rake paid'] = hand_dict['rake'].groups()[0]

			try:
				del hand_dict['preflop']
				del hand_dict['rake']
				del hand_dict['showdown']
			except KeyError:
				pass
		else:
			return False
		return hand_dict
	
	def getHandAttributes(self, hand_dict):
		#-------------------------------HAND ATTRIBUTES--------------------------#
		hand_attr 	= {}
		keep 		= ['blinds', 'preflop', 'turn', 'river', 'winners', 'dealer', 'refund']
		player_map 	= {a['player']:a['seat'] for a in hand_dict['players']}
		action_map 	= {'raises': 'R', 'bets': 'B', 'folds' : 'F', 'calls': 'C', 'checks': 'X'}
		blind_map 	= {'sb': 'SB', 'bb': 'BB', 'sbbb': 'SBBB'}
		streets 	= ['preflop', 'flop', 'turn', 'river']
		hand_attr['blinds'] = ''
		hand_attr['preflop'] = ''
		hand_attr['flop'] = ''
		hand_attr['turn'] = ''
		hand_attr['river'] = ''
		hand_attr['winners'] = ''
		hand_attr['refund'] = ''

		bb = hand_dict['bb'][0]['chips']
		sb = hand_dict['sb'][0]['chips']

		date = hand_dict['info']['hand_date']
		hand_attr['time'] = hand_dict['info']['hand_time']
		hand_attr['date time'] = _epoch("%s %s" % (date, hand_attr['time']) )
		hand_attr['bb'] = ("%.2f" % float(bb))
		hand_attr['sb'] = ("%.2f" % float(sb))
		hnum = hand_dict['info']['hand_num']
		hand_attr['hand number'] = hnum[:hnum.index('-')]
		hand_attr['limit type'] = hand_dict['game type']['limit']
		hand_attr['game type'] = hand_dict['game type']['game']
		hand_attr['seat type'] = hand_dict['game type']['seat_type']
		#hand_attr['min buyin'] = hand_dict['buyin']['min_buyin']
		#hand_attr['max buyin'] = hand_dict['buyin']['max_buyin']

		if hand_dict['dealer']:
			hand_attr['dealer'] = player_map[ hand_dict['dealer']['player'] ]
		for blind in blind_map.keys():
			if hand_dict[blind]:
				for b in hand_dict[blind]:
					hand_attr['blinds'] = "%s%s%s" % ( hand_attr['blinds'],	player_map[ b['player'] ],\
												blind_map[ blind ]	)
		for s in streets:
			if hand_dict['actions %s' % s]:
				for actions in hand_dict['actions %s' % s]:
					hand_attr[s] = "%s%s%s%.2f" % (hand_attr[s], 	player_map[ actions['player'] ], \
										action_map[ actions['action'] ], \
										(float('0') if actions['chips'] is None \
										 		 	else float(actions['chips'])))
		for w in hand_dict['winnings']:
			hand_attr['winners'] = "%s%s%s%.2f" % ( hand_attr['winners'], player_map[w['player']], \
										'W', float(w['chips']) )
		for r in hand_dict['refund']:
			hand_attr['refund'] = "%s%s%s%.2f" % ( hand_attr['refund'], player_map[w['player']], \
										'U', float(r['chips']) )

		
		#-------------------------------PLAYER ATTRIBUTES--------------------------#
		players = [ p for i in hand_dict['players'] \
					for p in [i['player']] ]

		player_attr = { p: {'amt sb'		: 0, \
						'amt bb'			: 0, \
						'amt sbbb'			: 0, \
						'amt preflop'		: 0, \
						'amt flop'			: 0, \
						'amt turn'			: 0, \
						'amt river'			: 0, \
						'amt refunded'		: 0, \
						'amt won'			: 0, \
						'amt net'			: 0, \
												 \
						'wtsd'				: 0, \
						'wsd'				: 0, \
						'w$'				: 0, \
							} for p in players 	}

		for a in hand_dict['sb']:
			plyr = a['player']
			player_attr_p = player_attr[plyr]
			player_attr_p['amt sb'] = 	player_attr_p['amt sb'] - \
									float(0 if a['chips'] is None else a['chips'])
		for a in hand_dict['bb']:
			plyr = a['player']
			player_attr_p = player_attr[plyr]
			player_attr_p['amt bb'] = 	player_attr_p['amt bb'] - \
									float(0 if a['chips'] is None else a['chips'])
		for a in hand_dict['sbbb']:
			plyr = a['player']
			player_attr_p = player_attr[plyr]
			player_attr_p['amt sbbb'] = 	player_attr_p['amt sbbb'] - \
									float(0 if a['chips'] is None else a['chips'])
		# Preflop 
		for a in hand_dict['actions preflop']:
			plyr = a['player']
			player_attr_p = player_attr[plyr]
			# Update Wagers Made
			if (a['action'] == 'raises'):
				player_attr_p['amt preflop'] = -float(0 if a['chips'] is None else a['chips'])
				player_attr_p['amt sb'] = 0
				player_attr_p['amt bb'] = 0
				player_attr_p['amt bb'] = 0
			else:
				player_attr_p['amt preflop'] = player_attr_p['amt preflop'] - \
										 float(0 if a['chips'] is None else a['chips'])
		# Flop
		for a in hand_dict['actions flop']:
			plyr = a['player']
			player_attr_p = player_attr[plyr]
			# Update Wagers Made
			if (a['action'] == 'raises'):
				player_attr_p['amt flop'] = 	-float(0 if a['chips'] is None else a['chips'])
			else:
				player_attr_p['amt flop'] = 	player_attr_p['amt flop'] - \
										float(0 if a['chips'] is None else a['chips'])
		# Turn
		for a in hand_dict['actions turn']:
			plyr = a['player']
			player_attr_p = player_attr[plyr]

			if (a['action'] == 'raises'):
				player_attr_p['amt turn'] = 	-float(0 if a['chips'] is None else a['chips'])
			else:
				player_attr_p['amt turn'] = 	player_attr_p['amt turn'] - \
										float(0 if a['chips'] is None else a['chips'])
		# River
		for a in hand_dict['actions river']:
			plyr = a['player']
			player_attr_p = player_attr[plyr]
			# Update Wagers Made
			if (a['action'] == 'raises'):
				player_attr_p['amt river'] = 	-float(0 if a['chips'] is None else a['chips'])
			else:
				player_attr_p['amt river'] = 	player_attr_p['amt river'] - \
										float(0 if a['chips'] is None else a['chips'])
		#Showdown
		for a in hand_dict['cards shown']:
			plyr = a['player']
			player_attr_p = player_attr[plyr]
			player_attr_p['wtsd'] = 1
	
		for a in hand_dict['refund']:
			plyr = a['player']
			player_attr_p = player_attr[plyr]
			player_attr_p['amt refunded'] = 	float(0 if a['chips'] is None else a['chips'])
		for a in hand_dict['winnings']:
			plyr = a['player']
			player_attr_p = player_attr[plyr]
			player_attr_p['w$'] = 1
			if player_attr_p['wtsd'] == 1:
				player_attr_p['wsd'] = 1
			player_attr_p['amt won'] = 		player_attr_p['amt won'] + \
										float(0 if a['chips'] is None else a['chips'])

		for p in player_attr.keys():
			player_attr[p]['net amt'] = float('%.2f' % (				\
								player_attr[p]['amt sb']		+ \
								player_attr[p]['amt bb']		+ \
								player_attr[p]['amt sbbb']		+ \
								player_attr[p]['amt preflop']	+ \
								player_attr[p]['amt flop']		+ \
								player_attr[p]['amt turn']		+ \
								player_attr[p]['amt river']		+ \
								player_attr[p]['amt refunded']	+ \
								player_attr[p]['amt won'] ))

		
		#-------------------------------PLAYER STATS--------------------------#
		player_map 	= {a['seat']:a['player'] for a in hand_dict['players']}
		stats = {	'vpip'		: [],
					'pfr'		: [],
					'op pfr'	: [],
					'pf3b' 		: [],
					'op pf3b'	: [],
					'f pf3b'	: [],
					'c pf3b'	: [],
					'r pf3b'	: [],

				'flop intv'		: [],

					'cbet'		: [],
					'op cb'		: [],
					'f cb'		: [],
					'c cb'		: [],
					'r cb'		: [],
					}
		preflop = hand_attr['preflop']

		stats['vpip'] 		= list(set(RGX_CONF_vpip.findall(preflop)))
		stats['op vpip']	= list(set(RGX_CONF_op_vpip.findall(preflop)))
		op_pfr = RGX_CONF_raise.search(preflop)
		if op_pfr:
			stats['op pfr'] = list(set(RGX_CONF_all_bet.findall(preflop[:op_pfr.end()])))
			op_pf3b = RGX_CONF_raise.search(preflop[op_pfr.end():])
			if op_pf3b:
				stats['op pf3b'] = list(set(RGX_CONF_all_bet.findall(preflop[ op_pfr.end():op_pf3b.end() ])))
			else:
				stats['op pf3b'] = list(set(RGX_CONF_all_bet.findall(preflop[op_pfr.end():])))	
		else:
			stats['op pfr'] = list(set(RGX_CONF_all_bet.findall(preflop)))

		stats['pfr'] 	= RGX_CONF_pfr.findall(preflop)
		stats['pf3b'] 	= RGX_CONF_pf3b.findall(preflop)
		stats['f pf3b'] = RGX_CONF_f_pf3b.findall(preflop)
		stats['c pf3b'] = RGX_CONF_c_pf3b.findall(preflop)
		stats['r pf3b'] = RGX_CONF_r_pf3b.findall(preflop)

		flop = hand_attr['flop']
		if flop:
			flop_intv = RGX_CONF_initiative.findall(preflop)
			for i in flop_intv:
				stats['cbet'] 	= re.compile(RGX_CONF_SUB['cb pfx'] % '(?P<seat>%s)' % i).findall(flop)
				prefix 			= RGX_CONF_SUB['cb pfx'] % i
				stats['op cb']	= re.compile(RGX_CONF_SUB['op cb'] % i).findall(flop)
				stats['f cb']	= re.compile(RGX_CONF_SUB['f cb'] % prefix).findall(flop)
				stats['c cb']	= re.compile(RGX_CONF_SUB['c cb'] % prefix).findall(flop)
				stats['r cb']	= re.compile(RGX_CONF_SUB['r cb'] % prefix).findall(flop)

		turn = hand_attr['turn']
		river = hand_attr['river']

		#-------------------------------DB SETUP--------------------------#
		p_attr = []
		for k in player_attr.keys():
			p_attr.append({	'h_id'	: hand_attr['hand number'],
							'player': k,
							'net'	: player_attr[k]['net amt'],
							'wtsd'	: player_attr[k]['wtsd'], 
							'wd'	: player_attr[k]['w$'],
							'wsd'	: player_attr[k]['wsd'] }	)
		
		p_stats = []
		p_summary = []
		for k in player_map.keys():
			p_stats.append({	'h_id' 		:	hand_attr['hand number'],
								'player'	:	player_map[k],
								'vpip'		:  	(1 if k in stats['vpip'] else 0),
								'op vpip'	:  	(1 if k in stats['op vpip'] else 0),
								'pfr'		:  	(1 if k in stats['pfr'] else 0),
								'op pfr'	:  	(1 if k in stats['op pfr'] else 0),
								'pf3b'		:  	(1 if k in stats['pf3b'] else 0),
								'op pf3b'	:  	(1 if k in stats['op pf3b'] else 0),
								'f pf3b'	:  	(1 if k in stats['f pf3b'] else 0),
								'c pf3b'	:  	(1 if k in stats['c pf3b'] else 0),
								'r pf3b'	:  	(1 if k in stats['r pf3b'] else 0),
								'cbet'		:  	(1 if k in stats['cbet'] else 0),
								'op cb' 	:  	(1 if k in stats['op cb'] else 0),
								'f cb'		:  	(1 if k in stats['f cb'] else 0),
								'c cb'		:  	(1 if k in stats['c cb'] else 0),
								'r cb'		:	(1 if k in stats['r cb'] else 0)
							  	})

			p_summary.append({	'h_id' 		:	hand_attr['hand number'],
								'bb'		: 	hand_attr['bb'],
								'sb'		: 	hand_attr['sb'],
								'limit type': 	hand_attr['limit type'],
								'game type'	: 	hand_attr['game type'],
								'seat type'	: 	hand_attr['seat type'],
								'date time'	: 	hand_attr['date time'],

								'player'	:	player_map[k],
								'vpip'		:  	(1 if k in stats['vpip'] else 0),
								'op vpip'	:  	(1 if k in stats['op vpip'] else 0),
								'pfr'		:  	(1 if k in stats['pfr'] else 0),
								'op pfr'	:  	(1 if k in stats['op pfr'] else 0),
								'pf3b'		:  	(1 if k in stats['pf3b'] else 0),
								'op pf3b'	:  	(1 if k in stats['op pf3b'] else 0),
								'f pf3b'	:  	(1 if k in stats['f pf3b'] else 0),
								'c pf3b'	:  	(1 if k in stats['c pf3b'] else 0),
								'r pf3b'	:  	(1 if k in stats['r pf3b'] else 0),
								'cbet'		:  	(1 if k in stats['cbet'] else 0),
								'op cb' 	:  	(1 if k in stats['op cb'] else 0),
								'f cb'		:  	(1 if k in stats['f cb'] else 0),
								'c cb'		:  	(1 if k in stats['c cb'] else 0),
								'r cb'		:	(1 if k in stats['r cb'] else 0),

								'net'		: 	player_attr[ player_map[k] ]['net amt'],
								'wtsd'		: 	player_attr[ player_map[k] ]['wtsd'], 
								'wsd'		: 	player_attr[ player_map[k] ]['wsd']
							  	})
		return [ [hand_attr], p_attr, p_stats, p_summary]


	# checks segment of HH for existence of a hand
	def __hasHand(self, str):
		h = RGX_CONF_hand.search(str)
		r = RGX_CONF_rake.search(str)
		if (h and r):
			return [h.start(), r.end()]
		else:
			return []

	# checks segments of hand to determine if valid
	def __isValidHand(self, d):
		if d:
			valid_setup = 	bool(d['info'] and d['buyin'] and  d['game type'] and d['players'] \
								 and d['dealer'] and d['sb'] and d['bb'] and d['preflop'] \
								 and d['rake'] and d['winnings'])
			if valid_setup:
				valid_segments = True
				if (d['showdown']):
					if (d['flop'] and d['turn'] and d['river']):
						valid_segments = True
					else:
						valid_segments = False
				elif (d['river']):
					if (d['flop'] and d['turn']):
						valid_segments = True
					else:
						valid_segments = False
				elif (d['turn']):
					if (d['flop']):
						valid_segments = True
					else:
						valid_segments = False
			else:
				return False
			return bool(valid_segments and valid_setup)
		else: 
			return False


	def parseTourney(self, tourney_str):
		tourney_str = tourney_str.strip('\n\n').strip('\n').strip(' ')
		print tourney_str
		tourney_info = {}
		player_info = []
		if tourney_str:
			print "YOLO"
			tourney	= RGX_CONF_parse_tourney.search(tourney_str)
			if tourney:
				print "YOLOLO"
				places_str = tourney_str[tourney.end():]
				player 	= RGX_CONF_parse_results.finditer(places_str)

				if player:
					tourney						= tourney.groups()
					tourney_info['name']		= tourney[0]
					tourney_info['trunc']		= tourney[1]
					tourney_info['end time']	= tourney[2]
					tourney_info['seats']		= tourney[3]
					tourney_info['limit type'] 	= tourney[4]
					tourney_info['game type'] 	= tourney[5]
					tourney_info['buy in'] 		= tourney[6]
					tourney_info['rake']	 	= tourney[7]
					tourney_info['sng']		 	= tourney[8]
					tourney_info['sch']		 	= tourney[9]
					tourney_info['mtt']		 	= tourney[10]
					tourney_info['gtd']		 	= tourney[11]
					tourney_info['krill']		= tourney[12]
					tourney_info['turbo']		= tourney[13]

					places						= [m.groupdict() for m in player]
					tourney_info['num players'] = len(places)
					
					for p in places:
						net = '%.2f' % (float(p['chips']) - float(tourney_info['buy in']))
						player_info.append({
											'name' 			: tourney_info['name'],
											'trunc' 		: tourney_info['trunc'],
											'end time'		: _epoch(tourney_info['end time'], '%Y-%m-%d %H:%M-%Z'),
											'buy in'		: tourney_info['buy in'],
											'rake' 			: tourney_info['rake'],
											'num players'	: tourney_info['num players'],
											'seats' 		: tourney_info['seats'],
											'limit type'	: tourney_info['limit type'],
											'game type' 	: tourney_info['game type'],
											'sng' 			: tourney_info['sng'],
											'sch' 			: tourney_info['sch'],
											'mtt' 			: tourney_info['mtt'],
											'gtd' 			: tourney_info['gtd'],
											'krill'			: tourney_info['krill'],
											'turbo' 		: tourney_info['turbo'],

											'player'		: p['player'],
											'net'			: net,
											'rank'			: p['rank'],
											'percentile'	: '%.2f' % (float(100/float(tourney_info['num players']))*(float(p['rank']) - 0.5)), 
											'roi'			: ('%.2f' % ( float(net)/float(tourney_info['buy in'])) if tourney_info['buy in'] != '0' else '0'),
											'itm'			: ('1' if float(p['chips']) > 0 else '0')
											})
		return player_info

