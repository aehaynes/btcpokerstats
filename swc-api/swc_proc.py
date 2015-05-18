#!/usr/bin/python2.7

'''
Class for processes based on the swc api
'''

import datetime
from time import time 
import re
import os
from swc_api import SWC_API
from config import *
from swc_regex_config import *
from swc_helpers import dt_correct, getDateDir

class SWC_PROC(SWC_API):

	def __init__(self, username = SWC_USERNAME[0], password = SWC_PASSWORD):
		SWC_API.__init__(self, username, password )
		self.openConnection()

	def History_Chat(self, stream):
		for s in stream:
			if( 'LobbyChat' in s['Command']):
				try:
					datetimestamp =  dt_correct(self.timeOffset, "%Y-%m-%d %H:%M:%S")
					text 	= "[%s] %s: %s %s\n" % \
								(datetimestamp, s['Player'][0], \
									s['Text'][0], s['Color'])
					logname = "%s Chat.txt"%dt_correct(self.timeOffset)
					
					with open(CHAT_PATH + logname, 'a') as f:
						f.write(text)
					return True
				except:
					pass
			else:
				return False


	def History_RingGame(self, stream, lines):
		whitelist = [' ', '.', '#',':', '-']
		reset = ['',False, False, '']
		
		for s in stream:
			if 'History' in s['Command']: # move higher up
				if 'Text' in s.keys() and 'Table' in s.keys():
					text = s['Text'][0]
					name = s['Table'][0]
					date = RGX_CONF_date.findall(text)
					if name not in lines.keys():
						lines[name] = reset[:]
					l = lines[name]

					if (name in NO_RAKE_TABLES): #Delay writing to catch split pots properly
						if (RGX_CONF_hand.search(text) and RGX_CONF_hand.search(l[0])):
							l[0] =  '%s\n%s' % ( l[0].replace(NO_RAKE_TABLES[0],NO_RAKE_TABLES[1]), NO_RAKE_TABLES[2] )
							filename = "".join(x for x in ('HH %s'% name) \
										if x.isalnum() or x in whitelist)+'.txt'
							date_dir =  HH_PATH + getDateDir(self.timeOffset)
							try:
								os.stat(date_dir)
							except:
								try:
									os.mkdir(date_dir)
								except:
									os.makedirs(date_dir)
							with open(date_dir + dt_correct(self.timeOffset) + ' ' + filename,'a') as f:						
								f.write(l[0])
							l[0:] = reset[:]

					if (date):
						hh_buffer 	= '\n\n%s' % text
						suffix 		= date[0] #date stamp
						l[0:] 		= [ hh_buffer, True, False, suffix]
					elif (RGX_CONF_rake.search(text)):
						hh_buffer 	= '%s\n%s' % (l[0], text)
						l[0:] 		= [hh_buffer, l[1], True, l[3]]
					else:
						hh_buffer 	= '%s\n%s' % (l[0], text)
						l[0:] 		= [hh_buffer, l[1], l[2], l[3]]
					if (l[1] == True and l[2] == True):
						l[0] = l[0].replace(NO_RAKE_TABLES[0],NO_RAKE_TABLES[1])
						filename = "".join(x for x in ('HH %s' % name ) \
									if x.isalnum() or x in whitelist)+'.txt'
						date_dir =  HH_PATH + getDateDir(self.timeOffset)
						try:
							os.stat(date_dir)
						except:
							try:
								os.mkdir(date_dir)
							except:
								os.makedirs(date_dir)
						with open(date_dir + dt_correct(self.timeOffset) + ' ' + filename,'a') as f:
							f.write(l[0])
						l[0:] = reset[:]


	def History_TournamentTables(self, stream, tourney_info):
		table_name = ''
		for s in stream:
			#print s
			if 'Type' in s.keys():
				if 'T' in s['Type']:
					if 'TableInfo' in s['Command']:
						line_count = len(s.keys()) - 3
						for i in range(1,line_count):
							if 'Line%s' % i in s.keys():
								line = s['Line%s' % i][0]
								rgx_rank = RGX_CONF_rank.search(line)
								rgx_buyin = RGX_CONF_tourney_buyin.search(line)
								rgx_table_name = RGX_CONF_tourney_name.search(line)
								rgx_gtd = RGX_CONF_gtd.search(line)
								rgx_sng = RGX_CONF_sng.search(line)
								rgx_sch = RGX_CONF_scheduled.search(line)
								rgx_mtt = RGX_CONF_mtt.search(line)
								rgx_tst = RGX_CONF_tseat.search(line)
								rgx_tgm = RGX_CONF_tgame.search(line)											

								#Table name
								if rgx_table_name:
									table_name = rgx_table_name.groups()[0]

								if table_name in tourney_info['tracked tables'].keys():
									#Krill, Turbo, Truncated Name
									tourney_info['tracked tables'][table_name]['name'] = table_name
									tourney_info['tracked tables'][table_name]['krill'] = (1 if "krill" in table_name.lower() else 0)
									tourney_info['tracked tables'][table_name]['turbo'] = (1 if "turbo" in table_name.lower() else 0)
									tourney_info['tracked tables'][table_name]['trunc name'] = (table_name[:table_name.find('#')].strip() if \
																										table_name.find('#') > 0 else table_name)

									#GTD
									if "Prize bonus:" in line:
										tourney_info['tracked tables'][table_name]['gtd'] = (1 if rgx_gtd else 0)
									#MTT
									if "Tables:" in line and rgx_mtt:
										tourney_info['tracked tables'][table_name]['mtt'] = (1 if int(rgx_mtt.groups()[0]) > 1 else 0)
									#SNG
									if "Start when full:" in line:
										tourney_info['tracked tables'][table_name]['sng'] = (1 if rgx_sng else 0)
									#Scheduled
									if "Start at time:" in line:
										tourney_info['tracked tables'][table_name]['scheduled'] = (1 if rgx_sch else 0)
									# Seat Type
									if rgx_tst:
										tourney_info['tracked tables'][table_name]['seat type'] = rgx_tst.groups()[0]
									# Game Type
									if rgx_tgm:
										tourney_info['tracked tables'][table_name]['limit type'] 	= GAME_MAP[ rgx_tgm.groups()[0] ]
										tourney_info['tracked tables'][table_name]['game type'] 	= GAME_MAP[ rgx_tgm.groups()[1] ]
									#Player payout
									if rgx_rank:
										if 'payout' in tourney_info['tracked tables'][table_name].keys():
											tourney_info['tracked tables'][table_name]['payout'][ rgx_rank.groups()[0] ] = rgx_rank.groups()[1]
										else:
											tourney_info['tracked tables'][table_name]['payout'] = {}
											tourney_info['tracked tables'][table_name]['payout'][ rgx_rank.groups()[0] ] = rgx_rank.groups()[1]
									#Buyin and rake
									if rgx_buyin:
										buyin_str = rgx_buyin.groups()[0].strip('+')
										tourney_info['tracked tables'][table_name]['buyin'] = eval(buyin_str)
										tourney_info['tracked tables'][table_name]['rake'] = buyin_str[buyin_str.find('+')+1:]

					if 'PlayerInfo' in s['Command']:
						table_name = s['Table'][0]
						if table_name in tourney_info['active tables']:
							tourney_info['selected queue'] = tourney_info['selected queue'] - set([table_name])
							player_count = int(s['Count'][0])
							if player_count > 0:
								finished = True
							else:
								finished = False
							if table_name not in tourney_info['tracked tables'].keys():
								tourney_info['tracked tables'][table_name] = {}
								print "\t-- Tracking Table--", table_name
								print "\t| Tracked Tables:", tourney_info['tracked tables'].keys()
							tourney_info['tracked tables'][table_name]['player rank'] = {}
							tourney_info['tracked tables'][table_name]['finished'] = finished
							for i in range(1, player_count + 1):
								player_name = s['Player%s'%i][0]
								if 'Finished' in s['Chips%s'%i]:
									tourney_info['tracked tables'][table_name]['player rank'][player_name] = s['Rank%s'%i][0]
									tourney_info['tracked tables'][table_name]['finished'] = True and tourney_info['tracked tables'][table_name]['finished']
								else:
									tourney_info['tracked tables'][table_name]['finished'] = tourney_info['tracked tables'][table_name]['finished'] and False
									tourney_info['tracked tables'][table_name]['player rank'] = {}
									break

					if table_name in tourney_info['tracked tables'].keys():
						if  tourney_info['tracked tables'][table_name]['finished'] and \
									'payout' in tourney_info['tracked tables'][table_name].keys() and \
											tourney_info['tracked tables'][table_name]['player rank']:
							pos = ''
							filename = "TH%s.txt" % dt_correct(self.timeOffset)

							tourney_info['tracked tables'][table_name]['datetime'] =  dt_correct(self.timeOffset, '%Y-%m-%d %H:%M')
							for k in tourney_info['tracked tables'][table_name]['player rank'].keys():
								rank = tourney_info['tracked tables'][table_name]['player rank'][k]
								pos = "%s%s,%s,%s;" % 	(pos, k, rank, \
														( tourney_info['tracked tables'][table_name]['payout'][rank] if rank in \
															tourney_info['tracked tables'][table_name]['payout'].keys() else 0) )
							tourney_info['tracked tables'][table_name]['positions'] =  pos
							
							th = TOURNEY_TEMPLATE % tourney_info['tracked tables'][table_name]
							date_dir =  HH_PATH + getDateDir(self.timeOffset)

							duplicate = False
							if (time() - tourney_info['last tourney time'] ) < 30 and tourney_info['last tourney name'] == table_name:
								duplicate = True

							if not duplicate:
								try:
									os.stat(date_dir)
								except:
									try:
										os.mkdir(date_dir)
									except:
										os.makedirs(date_dir)
								with open(date_dir + filename,'a') as f:
									f.write(th)
								print "\t***Tournament Finished:",table_name, tourney_info['tracked tables'][table_name]
							else:
								print "\t***Duplicate:",table_name, tourney_info['tracked tables'][table_name]
							
							tourney_info['last tourney time'] = time()
							tourney_info['last tourney name'] = table_name
							tourney_info['active tables'] = tourney_info['active tables'] - set([table_name])
							tourney_info['selected queue'] = tourney_info['selected queue'] - set([table_name])
							print "\t|  Dectivated: %s" % table_name
							del tourney_info['tracked tables'][table_name]


	def _diagnostics(self, mins):
		out = []
		self.openConnection()
		timeout = time() + mins*60
		
		while time() < timeout:
			out = out + self.stream()
		self.closeConnection()
		return out

	# add to active tables if players at table is > 1, deactivate tables if in active list and players < 2
	def update_RingGameTables(self, stream, active_list= set()):
		ret = set(active_list if active_list != None else [])
		
		for s in stream:
			if( 'RingGameLobby' in s['Command']):
				table_count		= int(s['Count'][0])
				active 			= set([s['ID%s'%i][0] for i in range(1, table_count+1) \
									for k in s['Players%s'%i] if int(k) > 1 ])
				deactive 		= set([s['ID%s'%i][0] for i in range(1, table_count+1) \
									for k in s['Players%s'%i] if (int(k) < 2  \
									and s['ID%s'%i][0] in active_list) ])
				ret 			= (set(ret) | active) - deactive
		return ret


	def update_Logins(self, stream, login_list = set()):
		ret = set(login_list if login_list != None else [])
		for s in stream:
			if( 'Logins' in s['Command']):
				logins = [ [i,k[:pos]] for i,j in s.iteritems() \
							for k in j \
							for pos in [k.find('|')] \
							if i[:2] in ['LI', 'LO'] ]
				log_in = set([name for l in logins \
							for name in [l[1]] if l[0][:2] == 'LI'] )
				log_out = set([name for l in logins \
							for name in [l[1]] if l[0][:2] == 'LO'] )
				ret = (ret | log_in ) - log_out
		return ret
		

	def update_TournamentTables(self, stream, active_list= set()):
		ret = set(active_list if active_list != None else [])
		for s in stream:
			if( 'TournamentLobby' in s['Command']):
				table_count		= int(s['Count'][0])
				active 			= set([s['ID%s'%i][0] for i in range(1, table_count+1) \
									for k in s['Starts%s'%i] if ("Playing" in k or "Starting" in k)])
				#deactive 		= set([s['ID%s'%i][0] for i in range(1, table_count+1) \
				#					for k in s['Starts%s'%i] if ("Playing" not in k and "Starting" not in k and "Resetting" not in k)])
				ret 			= (set(ret) | active) #- deactive
				#for i in deactive:
				#	if i in active_list:
				#		print "\t|  Deactived: %s" % (i)
				for i in active:
					if i not in active_list:
						print "\t|  Activated: %s" % (i)
		return ret
