import re

NO_RAKE_TABLES = ['No Rake Micro Stakes', 'NLHE 9max .01/.02 #0', 'Rake (0)']

GAME_MAP = {
	"Hold'em"		:	'HE',
	'Omaha Hi-Lo'	:	'O8',
	'Omaha'			:	'O',
	'Limit'			:	'L',
	'L'				:	'L',
	'NL'			:	'NL',
	'PL'			:	'PL',
	'O'				:	'O',
	'O8'			:	'O8',
	'HE'			:	'HE',
}

TOURNEY_TEMPLATE = \
'''

Name: %(name)s;
Trunc_name: %(trunc name)s;
Date: %(datetime)s;
Seats: %(seat type)s;
Limit: %(limit type)s;
Game: %(game type)s;
Buyin: %(buyin)s;
Rake: %(rake)s;
SNG: %(sng)s;
Scheduled: %(scheduled)s;
MTT: %(mtt)s;
GTD: %(gtd)s;
Krill: %(krill)s;
Turbo: %(turbo)s;
Player: %(positions)s;

'''

RGX_CONF_SUB = { 
	'SEAT'		: r'(?:Seat\s(?P<seat>\d):)',
	'PLYR'		: r'(?P<player>[a-zA-Z0-9_-]+)',
	'CHIPS'		: r'(?P<chips>[.0-9]+)',
	'HNUM'		: r'(?P<hand_num>\d+\D\d+)',
	'HTIME'		: r'(?P<hand_time>\d{2}:\d{2}:\d{2})',
	'HDATE'		: r'(?P<hand_date>\d{4}\D\d{2}\D\d{2})',
	'LIMIT'		: r'(?P<limit>PL|NL|L)', #'NLHE 6max .25/.5 #1',
	'GAMETYPE'	: r'(?P<game>HE|O8|O)',
	'SEATTYPE'	: r'(?P<seat_type>HU|6max|9max)',
	'BUYIN'		: r'\((?P<min_buyin>[.0-9]+)\s\-\s(?P<max_buyin>[.0-9]+)\)',
	'CARDS'		: r'(?:\[(?P<cards>[AJKQTchds 0-9]+)\])',
	'ACTS'		: r'(?P<action>folds|checks|calls|bets|raises)',
	
	'game'		: r'Game\:',
	'table'		: r'Table\:',
	'hand'		: r'Hand \#',
	'rake'		: r'Rake \(',
	'winners'	: r'(?:wins|splits)(?:\s\w+)* Pot(?:\s\w+)*',
	
	'preflop'	: r'\*\* Hole Cards \*\*',
	'flop'		: r'\*\* Flop \*\*',
	'turn'		: r'\*\* Turn \*\*',
	'river'		: r'\*\* River \*\*',
	'SD'		: r'\*\*[ \w+]* Pot[ \w+]* Show Down \*\*', 
	'allin'		: r'All\-in',

	'sb'		: r'posts small blind',
	'bb'		: r'posts big blind',
	'sbbb'		: r'posts small \& big blind',
	'dealer'	: r'has the dealer button',

	'all bet'	: r'(?P<seat>\d{1})(?:[RCFXB][0-9]+(?:[.]\d{2}))',
	'no bet'	: r'(?:\d{1}[CFX][0-9]+(?:[.]\d{2}))',
	'no check'	: r'(?:\d{1}[CFR][0-9]+(?:[.]\d{2}))',
	'bet'		: r'(?:\d{1}[B][0-9]+(?:[.]\d{2}))',
	'raise'	  	: r'(?:\d{1}[R][0-9]+(?:[.]\d{2}))',
	'fold'		: r'(?:\d{1}[F][0-9]+(?:[.]\d{2}))',
	'call'		: r'(?:\d{1}[C][0-9]+(?:[.]\d{2}))',

	'vpip' 		: r'(?P<seat>\d{1})(?:R|C)(?:[0-9]+(?:[.]\d{2}))',
	'op vpip' 	: r'(?:(?P<seat>\d{1})[CFR][0-9]+(?:[.]\d{2}))',
	'pfr' 		: r'^(?:%(no bet)s*(?:(?P<seat>\d{1})R[0-9]+(?:[.]\d{2})))',
	
	'pf3b' 		: r'^(?:%(no bet)s*%(raise)s%(no bet)s*(?:(?P<seat>\d{1})R[0-9]+(?:[.]\d{2})))',
	'f pf3b' 	: r'^(?:%(no bet)s*%(raise)s%(no bet)s*%(raise)s%(call)s*(?:(?P<seat>\d{1})[F][0-9]+(?:[.]\d{2})))',
	'c pf3b' 	: r'^(?:%(no bet)s*%(raise)s%(no bet)s*%(raise)s%(fold)s*(?:(?P<seat>\d{1})[C][0-9]+(?:[.]\d{2})))',
	'r pf3b' 	: r'^(?:%(no bet)s*%(raise)s%(no bet)s*%(raise)s(?:\d{1}[CF][0-9]+(?:[.]\d{2}))*(?:(?P<seat>\d{1})[R][0-9]+(?:[.]\d{2})))',

	'initiative': r'(?:%(no bet)s*(?:(?P<seat>\d{1})[RB][0-9]+(?:[.]\d{2}))%(no bet)s*)$',

	'cb pfx'	: r'(?:%s[B][0-9]+(?:[.]\d{2}))',
	'cbet'		: r'(?:(?P<seat>%s)[B][0-9]+(?:[.]\d{2}))',
	'op cb'		: r'(?:(?P<seat>%s)[XB][0-9]+(?:[.]\d{2}))',
	'f cb'		: r'(?:%s(?:\d{1}[C][0-9]+(?:[.]\d{2}))*(?:(?P<seat>\d{1})[F][0-9]+(?:[.]\d{2})))',
	'c cb'		: r'(?:%s(?:\d{1}[F][0-9]+(?:[.]\d{2}))*(?:(?P<seat>\d{1})[C][0-9]+(?:[.]\d{2})))',
	'r cb'		: r'(?:%s(?:\d{1}[CF][0-9]+(?:[.]\d{2}))*(?:(?P<seat>\d{1})[R][0-9]+(?:[.]\d{2})))',


	'rank' 			: r'(?:Place\s+\#(?P<rank>\d+)\:\s+(?P<chips>[.0-9]+))',
	'buy in'		: r'(?:Buy\s+in\:\s+(?P<chips>[.0-9\+]+))',
	'tourney'		: r'(?:Tournament\s+name\:\s+(?P<table_name>[\s\w+\W+]+))',
	'scheduled'		: r'(?:Start\s+at\s+time\:\s+(?P<scheduled>Yes))',
	'sng'			: r'(?:Start\s+when\s+full\:\s+(?P<sng>Yes))',
	't_seat_type'	: r'(?:Seats\s+per\s+table\:\s+(?P<seats>[0-9]))',
	't_game_type'	: r'(?:Game\:\s+(?P<limit>PL|NL|Limit)\s+(?P<game>Hold\'em|Omaha\s+Hi\-Lo|Omaha))',
	'mtt'			: r'(?:Tables\:\s+(?P<table_num>[0-9]+))',
	'gtd'			: r'(?:Prize\s+bonus\:\s+(?P<gtd>[.0-9]+\s+\(guaranteed\s+min\)))',

	'trny info'	: r'^(?P<name>[\s\w+\W+]+);\s*(?P<datetime>\d{4}\D\d{2}\D\d{2}\s\d{2}:\d{2});\s*%(CHIPS)s;',
	'plyr info'	: r'%(PLYR)s,\s*(?P<rank>\d+),\s*%(CHIPS)s;', 

	'parse_tourney'	: 	r'^(?:Name\:\s(?P<name>[\s\w+\W+]+)\;)\n' + \
						r'(?:Trunc\_name\:\s(?P<trunc>[\s\w+\W+]+)\;)\n' + \
						r'(?:Date\:\s(?P<datetime>\d{4}\D\d{2}\D\d{2}\s\d{2}:\d{2})\;)\n' + \
						r'(?:Seats\:\s(?P<seat>[0-9]+)\;)\n' + \
						r'(?:Limit\:\s(?P<limit>NL|PL|L)\;)\n' + \
						r'(?:Game\:\s(?P<game>O8|HE|O)\;)\n' + \
						r'(?:Buyin\:\s(?P<buyin>[.0-9]+)\;)\n' + \
						r'(?:Rake\:\s(?P<rake>[.0-9]+)\;)\n' + \
						r'(?:SNG\:\s(?P<sng>1|0)\;)\n' + \
						r'(?:Scheduled\:\s(?P<sch>1|0)\;)\n' + \
						r'(?:MTT\:\s(?P<mtt>1|0)\;)\n' + \
						r'(?:GTD\:\s(?P<gtd>1|0)\;)\n' + \
						r'(?:Krill\:\s(?P<krill>1|0)\;)\n' + \
						r'(?:Turbo\:\s(?P<turbo>1|0)\;)',
	'parse_results'	: 	r'(?:%(PLYR)s\,(?P<rank>[0-9]+)\,%(CHIPS)s\;)',

	'ring game hh'	: 	r'\d{4}\D\d{2}\D\d{2}\sHH\sNL|L|PL|No\sRake\sMicro\sStakes', 
	'tournament hh'	: 	r'TH\d{4}\D\d{2}\D\d{2}', 

	'number'		: r'[0-9]+',
	}

RGX_CONF_info 			= re.compile(r'^%(hand)s%(HNUM)s - %(HDATE)s %(HTIME)s$' % RGX_CONF_SUB, re.MULTILINE)
RGX_CONF_buyin			= re.compile(r'^%(game)s\s(?:[\s\w+\'\-])+\s%(BUYIN)s' % RGX_CONF_SUB, re.MULTILINE)
RGX_CONF_table			= re.compile(r'^%(table)s %(LIMIT)s%(GAMETYPE)s %(SEATTYPE)s' % RGX_CONF_SUB, re.MULTILINE)
RGX_CONF_players 		= re.compile(r'^%(SEAT)s %(PLYR)s \(%(CHIPS)s\)' % RGX_CONF_SUB, re.MULTILINE)
RGX_CONF_date 			= re.compile(r'%(HDATE)s' % RGX_CONF_SUB, re.MULTILINE)
RGX_CONF_hand			= re.compile(r'^%(hand)s%(HNUM)s{1}' % RGX_CONF_SUB, re.MULTILINE)
RGX_CONF_rake			= re.compile(r'^%(rake)s%(CHIPS)s\){1}' % RGX_CONF_SUB, re.MULTILINE)
RGX_CONF_winner 		= re.compile(r'^%(PLYR)s %(winners)s \(%(CHIPS)s\)' % RGX_CONF_SUB, re.MULTILINE)

RGX_CONF_sb 			= re.compile(r'^%(PLYR)s %(sb)s %(CHIPS)s' % RGX_CONF_SUB, re.MULTILINE ) 
RGX_CONF_bb 			= re.compile(r'^%(PLYR)s %(bb)s %(CHIPS)s' % RGX_CONF_SUB, re.MULTILINE)
RGX_CONF_sbbb 			= re.compile(r'^%(PLYR)s %(sbbb)s %(CHIPS)s' % RGX_CONF_SUB, re.MULTILINE)
RGX_CONF_dealer 		= re.compile(r'^%(PLYR)s %(dealer)s$' % RGX_CONF_SUB, re.MULTILINE)
	
RGX_CONF_action 		= re.compile(r'^%(PLYR)s %(ACTS)s(?:[a-z A-Z])*%(CHIPS)s?(?:\s\((%(allin)s)\))?' % RGX_CONF_SUB, re.MULTILINE)
RGX_CONF_refund			= re.compile(r'^%(PLYR)s refunded %(CHIPS)s' % RGX_CONF_SUB, re.MULTILINE)
RGX_CONF_shown 			= re.compile(r'^%(PLYR)s shows %(CARDS)s' % RGX_CONF_SUB, re.MULTILINE)
RGX_CONF_hero			= re.compile(r'^Dealt to %(PLYR)s %(CARDS)s' % RGX_CONF_SUB, re.MULTILINE)

RGX_CONF_preflop		= re.compile(r'^(?:%(preflop)s)' % RGX_CONF_SUB, re.MULTILINE)
RGX_CONF_flop			= re.compile(r'^(?:%(flop)s) %(CARDS)s' % RGX_CONF_SUB, re.MULTILINE)
RGX_CONF_turn			= re.compile(r'^(?:%(turn)s) %(CARDS)s' % RGX_CONF_SUB, re.MULTILINE)
RGX_CONF_river			= re.compile(r'^(?:%(river)s) %(CARDS)s' % RGX_CONF_SUB, re.MULTILINE)
RGX_CONF_sd 			= re.compile(r'^(?:%(SD)s) %(CARDS)s' % RGX_CONF_SUB, re.MULTILINE)

RGX_CONF_all_bet		= re.compile(r'%(all bet)s' % RGX_CONF_SUB)
RGX_CONF_raise 			= re.compile(r'%(raise)s' % RGX_CONF_SUB)
RGX_CONF_vpip 			= re.compile(r'%(vpip)s' % RGX_CONF_SUB)
RGX_CONF_op_vpip		= re.compile(r'%(op vpip)s' % RGX_CONF_SUB)
RGX_CONF_pfr 			= re.compile(r'%(pfr)s' % RGX_CONF_SUB % RGX_CONF_SUB)
RGX_CONF_pf3b 			= re.compile(r'%(pf3b)s' % RGX_CONF_SUB % RGX_CONF_SUB)
RGX_CONF_f_pf3b 		= re.compile(r'%(f pf3b)s' % RGX_CONF_SUB % RGX_CONF_SUB)
RGX_CONF_c_pf3b 		= re.compile(r'%(c pf3b)s' % RGX_CONF_SUB % RGX_CONF_SUB)
RGX_CONF_r_pf3b 		= re.compile(r'%(r pf3b)s' % RGX_CONF_SUB % RGX_CONF_SUB)
RGX_CONF_initiative 	= re.compile(r'%(initiative)s' % RGX_CONF_SUB % RGX_CONF_SUB)

RGX_CONF_rank			= re.compile(r'%(rank)s' % RGX_CONF_SUB)
RGX_CONF_tourney_buyin	= re.compile(r'%(buy in)s' % RGX_CONF_SUB)
RGX_CONF_tourney_name	= re.compile(r'%(tourney)s' % RGX_CONF_SUB)
RGX_CONF_sng			= re.compile(r'%(sng)s' % RGX_CONF_SUB)
RGX_CONF_scheduled 		= re.compile(r'%(scheduled)s' % RGX_CONF_SUB)
RGX_CONF_mtt			= re.compile(r'%(mtt)s' % RGX_CONF_SUB)
RGX_CONF_gtd			= re.compile(r'%(gtd)s' % RGX_CONF_SUB)
RGX_CONF_tseat			= re.compile(r'%(t_seat_type)s' % RGX_CONF_SUB)
RGX_CONF_tgame			= re.compile(r'%(t_game_type)s' % RGX_CONF_SUB)

RGX_CONF_tourney_info	= re.compile(r'%(trny info)s' % RGX_CONF_SUB % RGX_CONF_SUB)
RGX_CONF_player_info	= re.compile(r'%(plyr info)s' % RGX_CONF_SUB % RGX_CONF_SUB)
RGX_CONF_parse_tourney	= re.compile(r'%(parse_tourney)s' % RGX_CONF_SUB)
RGX_CONF_parse_results	= re.compile(r'%(parse_results)s' % RGX_CONF_SUB % RGX_CONF_SUB)

RGX_CONF_dt 			= re.compile(r'^%(HDATE)s \d{2}:\d{2}$' % RGX_CONF_SUB)
RGX_CONF_pname			= re.compile(r'^%(PLYR)s$' % RGX_CONF_SUB)

RGX_CONF_tourneyHH		= re.compile(r'^%(tournament hh)s' % RGX_CONF_SUB)
RGX_CONF_ringHH			= re.compile(r'^%(ring game hh)s' % RGX_CONF_SUB)

RGX_CONF_number			= re.compile(r'^%(number)s' % RGX_CONF_SUB)