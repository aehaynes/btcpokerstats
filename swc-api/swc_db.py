#!/usr/bin/python2.7

import re
from time import time, sleep
from datetime import datetime
import psycopg2
import psycopg2.extensions
import sys
import os
import hashlib
from swc_regex_config import *
from swc_parse import SWC_PARSE
from swc_helpers import _epoch


class SWC_DB(SWC_PARSE):
	def __init__(self, db, username, password):
		self.parse = SWC_PARSE()
		self.__db = db
		self.__unm = username
		self.__pwd = password
		self.hasher = hashlib.md5()

	def openConnection(self, db = None, username = None, password = None):
		self.__db = (db if db != None else self.__db)
		self.__unm = (username if username != None else self.__unm)
		self.__pwd = (password if password != None else self.__pwd)
		try:
			self.closeConnection()
		except:
			pass
		self.con = psycopg2.connect(database = self.__db, user = self.__unm, password = self.__pwd)
		self.cur = self.con.cursor()

	def dropTables(self, *tables):
		for t in tables:
			self.cur.execute("DROP TABLE IF EXISTS %s" % t)

	def createStr(self, table):
		if table == 'Hand_Info':
			ret = '''	CREATE TABLE IF NOT EXISTS Hand_Info ( Hand_ID INT PRIMARY KEY, DT BIGINT, 
						Small_Blind FLOAT8, Big_Blind FLOAT8, Limit_Type VARCHAR(4), Game_Type VARCHAR(4), Seat_Type VARCHAR(4)
						)'''
		elif table == 'Player_Info':
			ret = ''' 	CREATE TABLE IF NOT EXISTS Player_Info (Player_ID SERIAL PRIMARY KEY, Player_Name VARCHAR(20)
						)'''
		elif table == 'Hand_Actions':
			ret = '''	CREATE TABLE IF NOT EXISTS Hand_Actions( Hand_ID INT PRIMARY KEY, 
					 	Preflop TEXT, Flop TEXT, Turn TEXT, River TEXT
					 	)'''
		elif table == 'Player_Winnings':
			ret = '''	CREATE TABLE IF NOT EXISTS Player_Winnings ( Hand_ID INT, Player_ID INT, 
						Amount_Won FLOAT8, WTSD INT, WD INT, WSD INT, PRIMARY KEY (Hand_ID, Player_ID)
						)'''
		elif table == 'Player_Stats':
			ret = '''	CREATE TABLE IF NOT EXISTS Player_Stats ( Hand_ID INT, Player_ID INT, vpip INT, op_vpip INT, 
						pfr INT, op_pfr INT, pf3b INT, op_pf3b INT, f_pf3b INT, c_pf3b INT, r_pf3b INT, cbet INT,
						op_cbet INT, f_cbet INT, c_cbet INT, r_cbet INT, PRIMARY KEY (Hand_ID, Player_ID)
						)'''
		elif table == 'File_MD5':
			ret = '''	CREATE TABLE IF NOT EXISTS File_MD5 ( File_Name TEXT, MD5 VARCHAR(100), Pos INT )'''
		elif table == 'Player_Summary':
			ret = '''	CREATE TABLE IF NOT EXISTS Player_Summary ( Apprx_dt timestamp, Player_ID INT, Small_Blind FLOAT8, Big_Blind FLOAT8, 
						Limit_Type VARCHAR(4), Game_Type VARCHAR(4), Seat_Type VARCHAR(4), num_hands INT, vpip INT, op_vpip INT, pfr INT, op_pfr INT, pf3b INT, op_pf3b INT, 
						f_pf3b INT, c_pf3b INT, r_pf3b INT, cbet INT, op_cbet INT, f_cbet INT, c_cbet INT, r_cbet INT, Amount_Won FLOAT8, WTSD INT, WSD INT 
						)'''
		elif table == 'Tournament_Summary':
			ret = '''	CREATE TABLE IF NOT EXISTS Tournament_Summary ( Apprx_dt timestamp, Player_ID INT, Tournament_Name VARCHAR(40), Trunc_Tournament_Name VARCHAR(40),
						Amount_Won FLOAT8, Buy_in FLOAT8, Rake FLOAT8, Num_Players INT, Seats INT, Limit_Type VARCHAR(4), Game_Type VARCHAR(4), SNG BOOL, Scheduled BOOL, MTT BOOL, 
						GTD BOOL, Krill BOOL, Turbo BOOL, Rank INT, Percentile FLOAT8, ROI FLOAT8, ITM BOOL, PRIMARY KEY (Tournament_Name, Apprx_dt, Player_ID)
						)'''
		elif table == 'Menu_Limits':
			ret = ''' 	CREATE TABLE IF NOT EXISTS Menu_Limits (Code VARCHAR(4), Label VARCHAR(12))
						'''
		elif table == 'Menu_Seats':
			ret = ''' 	CREATE TABLE IF NOT EXISTS Menu_Seats (Code_R VARCHAR(8), Code_T VARCHAR(8), Label VARCHAR(12))
						''' 
		elif table == 'Menu_Games':
			ret = ''' 	CREATE TABLE IF NOT EXISTS Menu_Games (Code VARCHAR(4), Label VARCHAR(18))
						''' 
		elif table == 'Menu_Tournament_Type':
			ret = ''' 	CREATE TABLE IF NOT EXISTS Menu_Tournament_type (Code VARCHAR(12), Label VARCHAR(12))
						''' 
		elif table == 'Menu_Stats':
			ret = ''' CREATE TABLE IF NOT EXISTS Menu_Stats (Code VARCHAR(12), Label VARCHAR(58), Percent BOOL)''' 
		return ret
	
	def insertStr(self, table):
		if table == 'Hand_Info':
			ret = '''	INSERT INTO Hand_Info ( Hand_ID, DT, Small_Blind, Big_Blind, Limit_Type , Game_Type, Seat_Type ) 
						SELECT %(hand number)s, %(date time)s, %(sb)s, %(bb)s, %(limit type)s, %(game type)s, %(seat type)s 
						WHERE NOT EXISTS (SELECT Hand_ID FROM Hand_Info WHERE Hand_ID = %(hand number)s)
						 '''
		elif table == 'Player_Info':
			ret = '''	INSERT INTO Player_Info ( Player_name ) SELECT 
						%(player)s WHERE NOT EXISTS (SELECT Player_Name FROM Player_Info WHERE Player_Name = %(player)s 
						)'''
		elif table == 'Hand_Actions':
			ret = '''	INSERT INTO Hand_Actions ( Hand_ID, Preflop, Flop, Turn, River ) SELECT 
						%(hand number)s, %(preflop)s, %(flop)s, %(turn)s, %(river)s	WHERE NOT 
						EXISTS (SELECT Hand_ID FROM Hand_Actions WHERE Hand_ID = %(hand number)s
						)'''
		elif table == 'Player_Winnings':
			ret = '''	INSERT INTO Player_Winnings ( Hand_ID,  Amount_Won, WTSD, WD, WSD, Player_ID ) SELECT 
						%(h_id)s, %(net)s, %(wtsd)s, %(wd)s, %(wsd)s, Player_ID FROM Player_Info WHERE Player_Info.Player_Name = %(player)s 
						AND NOT EXISTS (SELECT Hand_ID, Player_ID FROM Player_Winnings WHERE Player_Winnings.Player_ID = Player_Info.Player_ID AND Hand_ID = %(h_id)s)
						'''
		elif table == 'Player_Stats':
			ret = '''	INSERT INTO Player_Stats ( Hand_ID, vpip, op_vpip, pfr, op_pfr, pf3b, op_pf3b, f_pf3b, c_pf3b,
						r_pf3b, cbet, op_cbet, f_cbet, c_cbet, r_cbet, Player_ID ) SELECT %(h_id)s,	%(vpip)s, %(op vpip)s, %(pfr)s, 
						%(op pfr)s, %(pf3b)s, %(op pf3b)s, %(f pf3b)s, %(c pf3b)s, %(r pf3b)s, %(cbet)s, %(op cb)s, 
						%(f cb)s, %(c cb)s, %(r cb)s, Player_ID FROM Player_Info WHERE Player_Info.Player_Name = %(player)s AND 
						NOT EXISTS (SELECT Hand_ID, Player_ID FROM Player_Stats WHERE 
						Player_Stats.Player_ID = Player_Info.Player_ID AND Hand_ID = %(h_id)s
						)'''
		elif table == 'Player_Summary':
			ret = '''	INSERT INTO Player_Summary ( Apprx_dt, Small_Blind, Big_Blind, Limit_Type , Game_Type, Seat_Type, num_hands, vpip, 
						op_vpip, pfr, op_pfr, pf3b, op_pf3b, f_pf3b, c_pf3b, r_pf3b, cbet, op_cbet, f_cbet, c_cbet, r_cbet, Amount_Won, WTSD, 
						WSD, Player_ID) SELECT date_trunc('hour', to_timestamp(%(date time)s) at time zone 'UTC'), %(sb)s, %(bb)s, %(limit type)s, 
						%(game type)s, %(seat type)s, 1, %(vpip)s, %(op vpip)s, %(pfr)s, %(op pfr)s, %(pf3b)s, %(op pf3b)s, %(f pf3b)s, %(c pf3b)s, %(r pf3b)s, %(cbet)s, 
						%(op cb)s, %(f cb)s, %(c cb)s, %(r cb)s, %(net)s, %(wtsd)s, %(wsd)s, Player_ID FROM Player_Info WHERE Player_Info.Player_Name = %(player)s AND 
						NOT EXISTS ( SELECT Hand_ID FROM Hand_Info 	WHERE Hand_ID = %(h_id)s ) AND NOT EXISTS ( SELECT Apprx_dt, Player_ID, Small_Blind, Big_Blind, Limit_Type ,
						Game_Type, Seat_Type FROM Player_Summary WHERE Apprx_dt = date_trunc('hour', to_timestamp(%(date time)s) at time zone 'UTC') AND 
						Player_Summary.Player_ID = Player_Info.Player_ID  AND Small_Blind = %(sb)s AND Big_Blind = %(bb)s AND Limit_Type = %(limit type)s AND 
						Game_Type = %(game type)s AND Seat_Type = %(seat type)s
						)  '''
		elif table == 'File_MD5':
			ret = '''	INSERT INTO File_MD5 (File_Name, MD5, Pos) SELECT %(name)s, %(md5)s, %(pos)s WHERE NOT EXISTS (SELECT File_Name FROM File_MD5 WHERE File_Name=%(name)s
						) '''
		elif table == 'Tournament_Summary':
			ret = '''	INSERT INTO Tournament_Summary ( Apprx_dt, Tournament_Name, Trunc_Tournament_Name, Amount_Won, Buy_in, Rake, Num_Players, Seats, Limit_Type, 
						Game_Type, SNG, Scheduled, MTT, GTD, Krill, Turbo, Rank, Percentile, ROI, ITM, Player_ID ) 
						SELECT to_timestamp(%(end time)s) at time zone 'UTC', %(name)s, %(trunc)s, %(net)s, %(buy in)s, %(rake)s, %(num players)s, %(seats)s, %(limit type)s,
						%(game type)s, %(sng)s, %(sch)s, %(mtt)s, %(gtd)s, %(krill)s, %(turbo)s, %(rank)s, %(percentile)s, %(roi)s, %(itm)s, Player_ID FROM Player_Info WHERE 
						Player_Info.Player_Name = %(player)s AND NOT EXISTS (SELECT Tournament_Name, Apprx_dt, Rank, Num_Players, Player_ID FROM Tournament_Summary WHERE 
								Tournament_Summary.Player_ID = Player_Info.Player_ID
								AND Tournament_Name = %(name)s 
								AND Apprx_dt = to_timestamp(%(end time)s) at time zone 'UTC' 
								AND Num_Players = %(num players)s 
						)'''
		elif table == 'Menu_Limits':
			ret = ''' 	INSERT INTO Menu_Limits (Code, Label) SELECT %(code)s, %(label)s
						'''
		elif table == 'Menu_Games':
			ret = ''' 	INSERT INTO Menu_Games (Code, Label) SELECT %(code)s, %(label)s
						''' 
		elif table == 'Menu_Seats':
			ret = ''' 	INSERT INTO Menu_Seats (Code_R, Code_T, Label) SELECT %(code_r)s, %(code_t)s, %(label)s
						''' 
		elif table == 'Menu_Tournament_Type':
			ret = ''' 	INSERT INTO  Menu_Tournament_type (Code, Label) SELECT %(code)s, %(label)s
						''' 
		elif table == 'Menu_Stats':
			ret = ''' INSERT INTO Menu_Stats (Code, Label, Percent) SELECT %(code)s, %(label)s, %(percent)s::BOOL''' 

		return ret

	def updateStr(self, table):
		if table == 'Player_Summary':
			ret = '''	UPDATE Player_Summary SET 
							num_hands 	= num_hands + 1, 
							vpip 		= vpip 		+ %(vpip)s, 
							op_vpip 	= op_vpip 	+ %(op vpip)s, 
							pfr 		= pfr 		+ %(pfr)s,
							op_pfr 		= op_pfr 	+ %(op pfr)s,
							pf3b 		= pf3b 		+ %(pf3b)s,
							op_pf3b 	= op_pf3b 	+ %(op pf3b)s,
							f_pf3b 		= f_pf3b 	+ %(f pf3b)s,
							c_pf3b 		= c_pf3b 	+ %(c pf3b)s,
							r_pf3b 		= r_pf3b 	+ %(r pf3b)s,
							cbet 		= cbet 		+ %(cbet)s,
							op_cbet 	= op_cbet 	+ %(op cb)s,
							f_cbet 		= f_cbet 	+ %(f cb)s,
							c_cbet 		= c_cbet 	+ %(c cb)s,
							r_cbet 		= r_cbet 	+ %(r cb)s,
							Amount_Won 	= Amount_Won+ %(net)s,
							WTSD 		= WTSD 		+ %(wtsd)s,
							WSD 		= WSD 		+ %(wsd)s
						FROM (SELECT Player_ID FROM Player_Info WHERE Player_Info.Player_Name = %(player)s) AS PI
						WHERE 	Apprx_dt 					= date_trunc('hour', to_timestamp(%(date time)s) at time zone 'UTC') AND 
								Player_Summary.Player_ID 	= PI.Player_ID AND 
								Small_Blind 				= %(sb)s AND
								Big_Blind 					= %(bb)s AND
								Limit_Type 					= %(limit type)s AND
								Game_Type 					= %(game type)s AND
								Seat_Type 					= %(seat type)s AND
								NOT EXISTS ( SELECT hand_id FROM Hand_Info WHERE hand_id = %(h_id)s )'''
		elif table == 'File_MD5':
			ret = '''	UPDATE File_MD5 SET MD5= %(md5)s, Pos=%(pos)s WHERE File_Name=%(name)s '''
			
		return ret


	def joinStr(self, num):
		if num == 0:
			ret = ''' 	CREATE TABLE Player_Summary as
						SELECT 	Count(*) AS num_hands,
								PW.player_ID AS Player_ID, 
								SUM(vpip) AS vpip, 
								SUM(op_vpip) AS op_vpip, 
								SUM(pfr) AS pfr, 
								SUM(op_pfr) AS op_pfr, 
								SUM(pf3b) AS pf3b, 
								SUM(op_pf3b) AS op_pf3b, 
								SUM(f_pf3b) AS f_pf3b, 
								SUM(c_pf3b) AS c_pf3b, 
								SUM(r_pf3b) AS r_pf3b, 
								SUM(cbet) AS cbet, 
								SUM(op_cbet) AS op_cbet, 
								SUM(f_cbet) AS f_cbet, 
								SUM(c_cbet) AS c_cbet, 
								SUM(r_cbet) AS r_cbet,

								SUM(Amount_Won) AS Amount_Won, 
								SUM(WTSD) AS WTSD,
								SUM(WSD) AS WSD,
								date_trunc('hour', to_timestamp(dt) at time zone 'UTC') AS Apprx_dt, 
								Small_Blind, 
								Big_Blind, 
								Limit_Type, 
								Game_Type,
								Seat_Type

							FROM Player_Stats AS PS INNER JOIN Player_Winnings AS PW 
							ON ( PS.hand_id = PW.hand_id AND 
								PS.player_ID = PW.player_ID ) 
							INNER JOIN Hand_Info AS HI 
							ON ( HI.hand_id = PW.hand_id ) 
							GROUP BY 
								PW.player_ID,
								seat_type,
								game_type, 
								limit_type, 
								small_blind, 
								big_blind,
								date_trunc('hour', to_timestamp(dt) at time zone 'UTC')'''
			return ret

	# Strings for Django queries. see swc_django
	def queryStr(self, num = 1, player = ''):
		if num == -1.1:
			ret = ''' SELECT player_name FROM Player_Info 
						WHERE UPPER(player_name) = UPPER('%s') limit 1''' % player
			 
		elif num == 3:
			ret = '''SELECT 	
						Apprx_dt, 
						limit_type || game_type || ' ' || seat_type || ' ' || small_blind || '/' || big_blind, 
						sum(num_hands), sum(amount_won)
						FROM 
							Player_Summary AS PS INNER JOIN Player_Info AS PI ON (PI.Player_ID = PS.Player_ID)
						WHERE UPPER(player_name) = UPPER('%s') 
						GROUP BY 
							game_type, seat_type, limit_type, small_blind, big_blind,
							Apprx_dt
							ORDER BY apprx_dt DESC ''' % player
		elif num == 10.5:
			ret = '''SELECT num, player_name, rank FROM (SELECT 
						num, player_id, ROUND(CAST(rank as NUMERIC),2) as rank FROM  
							(SELECT COUNT(*) as num, player_id, %(rank_qstr)s AS rank FROM tournament_summary 
								WHERE player_id > -1 %(where_qstr)s GROUP BY player_id ) AS T 
						%(range_qstr)s) AS R INNER JOIN Player_Info AS PI ON (PI.Player_ID = R.Player_ID) ORDER BY rank ASC, num DESC'''
		elif num == 10.3:
			ret = '''SELECT player_name, net FROM (SELECT player_id, net FROM
						(SELECT player_id, 
							sum(amount_won) AS net
							FROM
								Player_Summary AS PS 
							WHERE player_id > -1 %(where_qstr)s
							GROUP BY player_id) AS PSwN) AS R INNER JOIN Player_Info AS PI ON (PI.Player_ID = R.Player_ID) ORDER BY net ASC'''		
		elif num == 3.1:
			ret = '''SELECT 
						Tournament_Name, Apprx_dt, Amount_Won, Buy_in, Num_Players, Rank, roi
						FROM 
							Tournament_Summary AS TS INNER JOIN Player_Info AS PI ON (PI.Player_ID = TS.Player_ID) 
						WHERE
							UPPER(player_name) = UPPER('%s')'''  % player
		elif num == 3.2:
			ret = '''SELECT
						count(*),
						buy_in,
						sum(amount_won), 
						sum(roi*buy_in)/(0.0001+sum(buy_in)) AS ROI,
						sum(ITM::int)/count(*)::float AS ITM,
						sum(Percentile)/count(*)::float AS Percentile
						FROM 
							Tournament_Summary AS TS INNER JOIN Player_Info AS PI ON (PI.Player_ID = TS.Player_ID) 
						WHERE
							UPPER(player_name) = UPPER('%s')
						GROUP BY player_name, Buy_in'''  % player
		elif num == 11.3:
			ret = '''SELECT
						player_name, 
						sum(amount_won) AS Amount_Won, 
						sum(num_hands) AS Num_hands,
						sum(vpip)/(%(offset)s+sum(op_vpip))::float AS VPIP,
						(sum(pfr)+sum(pf3b)+sum(r_pf3b))/(%(offset)s+sum(op_pfr) +sum(op_pf3b) + sum(f_pf3b) + sum(c_pf3b) + sum(r_pf3b) )::float AS PFR,
						sum(pf3b)/(%(offset)s+sum(op_pf3b))::float AS PF3B,
						sum(cbet)/(%(offset)s+sum(op_cbet))::float AS CBET,
						sum(f_pf3b)/(%(offset)s+(sum(f_pf3b) + sum(c_pf3b) + sum(r_pf3b) ))::float AS F_PF3B,
						sum(c_pf3b)/(%(offset)s+(sum(f_pf3b) + sum(c_pf3b) + sum(r_pf3b) ))::float AS C_PF3B,
						sum(r_pf3b)/(%(offset)s+(sum(f_pf3b) + sum(c_pf3b) + sum(r_pf3b) ))::float AS R_PF3B,
						sum(f_cbet)/(%(offset)s+(sum(f_cbet) + sum(c_cbet) + sum(r_cbet) ))::float AS F_FCbet,
						sum(c_cbet)/(%(offset)s+(sum(f_cbet) + sum(c_cbet) + sum(r_cbet) ))::float AS C_FCbet,
						sum(r_cbet)/(%(offset)s+(sum(f_cbet) + sum(c_cbet) + sum(r_cbet) ))::float AS R_FCbet,
						sum(wtsd)/sum(num_hands)::float AS WTSD,
						sum(wsd)/(%(offset)s+sum(wtsd))::float AS WSD
						FROM 
							Player_Summary AS PS INNER JOIN Player_Info AS PI ON (PI.Player_ID = PS.Player_ID) 
						WHERE
							UPPER(player_name) IN %(pname)s AND
							apprx_dt > (current_date - interval %(time)s) AND 
							limit_type IN %(limit_type)s AND
							game_type IN %(game_type)s AND
							seat_type IN %(seat_type)s AND
							big_blind IN %(blinds)s
						GROUP BY player_name limit %(num_res)s
					'''
		elif num == 11.55:
			ret = '''SELECT
						player_name, 
						sum(amount_won) AS Amount_Won, 
						sum(num_hands) AS Num_hands,
						sum(vpip)/(%(offset)s+sum(op_vpip))::float AS VPIP,
						(sum(pfr)+sum(pf3b)+sum(r_pf3b))/(%(offset)s+sum(op_pfr) +sum(op_pf3b) + sum(f_pf3b) + sum(c_pf3b) + sum(r_pf3b) )::float AS PFR,
						sum(pf3b)/(%(offset)s+sum(op_pf3b))::float AS PF3B,
						sum(cbet)/(%(offset)s+sum(op_cbet))::float AS CBET,
						sum(f_pf3b)/(%(offset)s+(sum(f_pf3b) + sum(c_pf3b) + sum(r_pf3b) ))::float AS F_PF3B,
						sum(c_pf3b)/(%(offset)s+(sum(f_pf3b) + sum(c_pf3b) + sum(r_pf3b) ))::float AS C_PF3B,
						sum(r_pf3b)/(%(offset)s+(sum(f_pf3b) + sum(c_pf3b) + sum(r_pf3b) ))::float AS R_PF3B,
						sum(f_cbet)/(%(offset)s+(sum(f_cbet) + sum(c_cbet) + sum(r_cbet) ))::float AS F_FCbet,
						sum(c_cbet)/(%(offset)s+(sum(f_cbet) + sum(c_cbet) + sum(r_cbet) ))::float AS C_FCbet,
						sum(r_cbet)/(%(offset)s+(sum(f_cbet) + sum(c_cbet) + sum(r_cbet) ))::float AS R_FCbet,
						sum(wtsd)/sum(num_hands)::float AS WTSD,
						sum(wsd)/(%(offset)s+sum(wtsd))::float AS WSD
						FROM 
							Player_Summary AS PS INNER JOIN Player_Info AS PI ON (PI.Player_ID = PS.Player_ID) 
						WHERE
							date_trunc('minute',apprx_dt) >= '%(start_date)s' AND
							date_trunc('minute', apprx_dt) <= '%(end_date)s' AND
							UPPER(player_name) IN %(pname)s %(where_qstr)s
							
						GROUP BY player_name
					'''					
		elif num == -20.1:
			ret = ''' 	SELECT name FROM 
						(SELECT DISTINCT trunc_tournament_name AS name, buy_in, krill FROM tournament_summary WHERE scheduled = true ORDER BY buy_in, krill, name ASC) AS T
						'''
		elif num == -20.2:
			ret = ''' 	SELECT DISTINCT buy_in FROM tournament_summary ORDER BY buy_in ASC
						'''
		elif num == -20.3:
			ret = ''' 	SELECT DISTINCT big_blind, small_blind || '/' || big_blind FROM Player_Summary ORDER BY big_blind ASC
						'''
		elif num == -20.5:
			ret = ''' 	SELECT * from Menu_Limits
						'''
		elif num == -20.6:
			ret = ''' 	SELECT * from Menu_Games
						''' 
		elif num == -20.7:
			ret = ''' 	SELECT * from Menu_Tournament_Type
						''' 
		elif num == -20.8:
			ret = ''' SELECT * from Menu_Stats
					''' 
		elif num == -20.9:
			ret = ''' SELECT * from Menu_Seats
					''' 
		elif num == 50.66:
			ret = ''' 	SELECT apprx_dt, tournament_name, buy_in, player_name, rank, amount_won, itm 
						FROM 
							Tournament_Summary AS TS INNER JOIN Player_Info AS PI ON (PI.Player_ID = TS.Player_ID) 
						WHERE
							date_trunc('day',apprx_dt) >= '%(start_date)s'
						AND date_trunc('day', apprx_dt) <= '%(end_date)s' %(constructed query)s ORDER BY apprx_dt DESC, tournament_name ASC, rank ASC
						'''
		elif num == 50.76:
			ret = ''' 	SELECT apprx_dt, tournament_name, buy_in, player_name, rank, amount_won, itm 
						FROM 
							Tournament_Summary AS TS INNER JOIN Player_Info AS PI ON (PI.Player_ID = TS.Player_ID) 
						WHERE date_trunc('minute',apprx_dt) >= '%(start_date)s'
						AND date_trunc('minute', apprx_dt) <= '%(end_date)s' %(constructed query)s ORDER BY apprx_dt DESC, tournament_name ASC, rank ASC
						'''
		elif num == 100.01:
			ret = ''' SELECT DISTINCT apprx_dt FROM player_summary'''
		elif num == 100.02:
			ret = ''' SELECT DISTINCT date_trunc('hour', apprx_dt) FROM tournament_summary'''
		elif num == 100.1:
			ret = ''' SELECT COUNT(*) FROM (SELECT DISTINCT tournament_name, apprx_dt FROM tournament_summary) AS T'''
		elif num == 100.11:
			ret = ''' SELECT COUNT(*) FROM hand_info'''

		return ret

	def closeConnection(self):
		self.con.commit()
		self.con.close()
