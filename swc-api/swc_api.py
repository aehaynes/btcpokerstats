#!/usr/bin/python2.7
'''
Class to interface with the seals mavens api
'''
import sys
import socket
import pycurl
import StringIO
import urllib
import urlparse
import json
import select
from config import *
from swc_helpers import dt_offset

class SWC_API:
	username 		= ''
	userData 		= ''
	serverTime 		= ''
	depositAddress 	= ''
	location 		= ''
	title 			= ''
	chipsTotal 		= ''
	chipsInPlay 	= ''
	chipsAvailable 	= ''
	sessionKey 		= ''
	sessionHeader 	= ''
	version 		= ''
	__password 		= ''
	__packetCounter = 0
	__ID 			= ''
	__pcid 			= ''
	__curlHandle 	= ''
	__socket 		= ''


	# Initialize all state variables
	def __init__(self, username, password):
		self.username = username
		self.userData = ''
		self.__socket = None
		self.__packetCounter = 1
		self.__pcid = self.__randomHex()
		self.__registerdFunctions = []
		self.__password = password
		try:
		    self.address = socket.gethostbyname(SERVICE_URL)
		except:
			pass
			#NOTE: fill this in
	
	# Send SSL Curl request with credentials and create socket connection for receiving commands
	def openConnection(self):
		self.__resetConnection()
		try:
			self.__socket.connect((self.address, SERVICE_PORT))
			self.__socket.settimeout(30.0)
			print "Socket open...\nConnected to %s on remote port %s successfully" % (self.address, SERVICE_PORT)
			print "Connected from %s on local port %s" % self.__socket.getsockname()
		except:
			print "OpenConnection() Failed"
			pass
		self.__curlHandle.setopt(pycurl.URL, SERVICE_URL)
		print "Connecting to %s" % SERVICE_URL
		self.__curlHandle.setopt(pycurl.HEADER, 0) 
		self.__curlHandle.setopt(pycurl.USERAGENT, USER_AGENT_STR) 
		self.__curlHandle.setopt(pycurl.SSL_VERIFYHOST, 2) 
		self.__curlHandle.setopt(pycurl.SSL_VERIFYPEER, False)
		self.__curlHandle.setopt(pycurl.CAINFO, SWC_CERT_FILEPATH)
		self.__getMeaningfulColors()
		self.userData = self.__getSession()
		self.sessionKey = self.userData['MavensKey']
		self.version = self.userData['Version']
		self.serverTime = self.userData['ServerTime']
		self.timeOffset = dt_offset(self.serverTime)
		print self.timeOffset
		print self.serverTime
		self.__sendPolicyRequest()
		self.__sendSessionInitialization()
		self.__sendLogin()
		self.sendBalanceRequest()
	
	# Exit and close connection
	def closeConnection(self):
		print "Closing socket..."
		try:
			self.__curlHandle.close()
			self.__socket.close()
			self.__socket = ''
		except:
			pass
		print"Socket closed."
	
	# Used to buffer responses from the server.
	def stream(self, raw = False, log = False):
		logname = "%s-%s.txt" % (self.serverTime.replace(' ', ''), self.__ID)
		
		r, _, _ = select.select([self.__socket], [], [])
		S = ''
		
		if r:
			S = self.__recv()
		if (S):
			while (not S.endswith(END_STR)): # NOTE: is this a good condition?? potential for inf loop
				r, _, _ = select.select([self.__socket], [], [])
				if r:
					S = S + self.__recv()
			if (log == True):
				with open(logname, 'a') as f:
					f.write(S)
		L = S.split(END_STR)

		if (raw == True):
			return [l for l in L if l != '']
		else:
			return [urlparse.parse_qs(l) for l in L if l != ''] #returns empty list if end of buffer

	# Request our chip and kirll balance
	def sendBalanceRequest(self):
		self.__sendPacket('Response=Balance')
		
	def sendLoginRequest(self):
		self.__sendPacket('Response=Logins')

	# Open a table so the server will start sending us the various table actions and state
	def sendOpenTable(self, ttype, tableName):
		tableName = urllib.quote(tableName)
		self.__sendPacket('Response=GameSelected&Type=%s&Table=%s' % (ttype, tableName)) #can it work without this line?
		self.__sendPacket('Response=OpenTable&Type=%s&Table=%s&Seat=0'   % (ttype, tableName))

	# Close a table so the server stops sending us actions associated with it
	def sendCloseTable(self, ttype, tableName):
		tableName = urllib.quote(tableName)
		self.__sendPacket('Response=CloseTable&Type=%s&Table=%s' % (ttype, tableName))

	# Tell the server which game we selected so that it will send us information about it
	def sendSelectTable(self, ttype, tableName):
		tableName = urllib.quote(tableName)
		self.__sendPacket('Response=GameSelected&Type=%s&Table=%s' % (ttype, tableName))

	def sendTableInfo(self, ttype, tableName):
		tableName = urllib.quote(tableName)
		self.__sendPacket('Response=GameSelected&Type=%s&Table=%s' % (ttype, tableName))
		self.__sendPacket('Response=TableInfo&Type=%s&Table=%s' % (ttype, tableName))

	# Send chat to the lobby
	def sendLobbyChat(self, text):
		self.__sendPacket('Response=LobbyChat&Text=%s' % urllib.quote_plus(text))

	# Register for a tourney
	def sendTourneyRegistration(self, tableName):
		tableName = urllib.quote(tableName)
		self.__sendPacket('Response=RegisterRequest&Table=' + tableName)
		self.__processInput()
		self.__sendPacket('Response=Register&Seat=0&Type=T&Table=' + tableName)
		self.__processInput()
		return True

	# Tell the server which button we pressed
	def sendDecision(self, ttype, tableName, decision): #NOTE: check that this is the right response string to pass
		button = decision['action'].lower().capitalize()
		self.__sendPacket('Response=Button&Amount=%s&Type=%s&Button=%s&Table=%s'\
							% (decsion['amount'], ttype, button, urllib.quote(tableName)))

	# Search for a player
	def sendSearch(self, player):
		self.__sendPacket('Response=PlayerSearch&Player=' + player.lower() ) 
		#try search names with special characters to see what responses are sent in wireshark

	# Convert the numerical card to the 2 character text representation
	def cardNumToText(self, cardNum):
		cardTable = {
			1 : '2c', 2 : '2d', 3 : '2h', 4 : '2s', 5 : '3c', 6 : '3d', 7 : '3h', 8 : '3s',
			9 : '4c', 10 : '4d', 11 : '4h', 12 : '4s', 13 : '5c', 14 : '5d', 15 : '5h', 16 : '5s',
			17 : '6c', 18 : '6d', 19 : '6h', 20 : '6s', 21 : '7c', 22 : '7d', 23 : '7h', 24 : '7s',
			25 : '8c', 26 : '8d', 27 : '8h', 28 : '8s', 29 : '9c', 30 : '9d', 31 : '9h', 32 : '9s',
			33 : 'Tc', 34 : 'Td', 35 : 'Th', 36 : 'Ts', 37 : 'Jc', 38 : 'Jd', 39 : 'Jh', 40 : 'Js',
			41 : 'Qc', 42 : 'Qd', 43 : 'Qh', 44 : 'Qs', 45 : 'Kc', 46 : 'Kd', 47 : 'Kh', 48 : 'Ks',
			49 : 'Ac', 50 : 'Ad', 51 : 'Ah', 52 : 'As', 53 : 'X'}
		try:
			cardTable[cardNum]
			return cardTable[cardNum]
		except NameError:
			return False
			
	# Decrypt the encrypted cards sent by the server
	def decryptCards(self, cards, salt, sessionKey):
		import hashlib
		cardList = []
		h = hashlib.new('sha256')
		h.update(sessionKey + salt)
		var1 = h.hexdigest() #hash('sha256', sessionKey . salt)
		var2 = int(var1[0:2], 16)
		var3 = int(var1[2:4], 16)
		var4 = int(var1[4:6], 16)
		var5 = int(var1[6:8], 16)
		var6 = int(cards[0], 16) ^ var2
		var7 = int(cards[1], 16) ^ var3
		var8 = int(cards[2], 16) ^ var4
		var9 = int(cards[3], 16) ^ var5
		if (var6 < 0 or var6 > 53): var6 = 0
		if (var7 < 0 or var7 > 53): var7 = 0
		if (var8 < 0 or var8 > 53): var8 = 0
		if (var9 < 0 or var9 > 53):	var9 = 0
		if (var6 != 0): cardList.append( self.cardNumToText(var6) )
		if (var7 != 0): cardList.append( self.cardNumToText(var7) )
		if (var8 != 0): cardList.append( self.cardNumToText(var8) )
		if (var9 != 0): cardList.append( self.cardNumToText(var9) )
		return cardList

	# Reset connection
	def __resetConnection(self):
		self.closeConnection()
		self.__curlHandle = ''
		self.__packetCounter = 1
		self.__pcid = self.__randomHex()
		self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.__curlHandle = pycurl.Curl()
	
	# Convert a hex value to the string equivalent
	def __hex2str(self, hex):
		return hex.decode('hex')

	# Send a packet and append ID and packet number
	def __sendPacket(self, data):
		if (self.__ID):
			data = '%s&ID=%s' % (data, self.__ID)#is this the right condition?
		data = '%s&PNum=%s%s' % (data, self.__packetCounter, self.__hex2str('00'))
		self.__sendRawPacket(data)
		self.__packetCounter +=1

	# send a packet without appending anything
	def __sendRawPacket(self, data):
		self.__socket.send(data)

	# Receive data on the socket
	def __recv(self, size = 32768):
		ret = END_STR
		try:
			ret = self.__socket.recv(size)
		except:
			pass
		return ret

	# Send the command to intialize the session
	def __sendSessionInitialization(self): 
		self.__sendPacket('Response=Session&PC=%s&Version=%s' % (self.__pcid, self.version))
		response = self.__recv()
		self.sessionHeader = urlparse.parse_qs(response)
		print self.sessionHeader
		try:
			r = self.sessionHeader['ID']
			if isinstance(r, list):
				self.__ID = r[0]
			else:
				self.__ID = r
		except KeyError:
			pass

	# Send the command to login along with the session key
	def __sendLogin(self):
	    self.__sendPacket('Response=Login&SessionKey=%s&Player=%s' % (self.sessionKey, self.username))
	
	# Mimic the policy request sent by the official client
	def __sendPolicyRequest(self): 
		if (self.__socket):
			self.__sendRawPacket("<policy-file-request/>" + self.__hex2str('00'))
			self.__recv()
		else: sys.exit('You dun goofed...no connection nigga')

	# Use the curl handle to post values to the authentication server
	def __curlPost(self, url, fields):
		curlBuffer = StringIO.StringIO() 
		self.__curlHandle.setopt(pycurl.POST, 1)
		self.__curlHandle.setopt(pycurl.URL, url)
		fields_string = ''.join([ '%s=%s&' % (i,j) for i,j in fields.iteritems() ])
		fields_string.rstrip('&')
		self.__curlHandle.setopt(pycurl.POSTFIELDS, fields_string)
		self.__curlHandle.setopt(pycurl.WRITEFUNCTION, curlBuffer.write)
		self.__curlHandle.perform()
		return curlBuffer.getvalue()

	# Use curl handle to GET a page
	def __curlGet(self, url):
		curlBuffer = StringIO.StringIO()
		self.__curlHandle.setopt(pycurl.POST, 0) 
		self.__curlHandle.setopt(pycurl.URL, url) 
		self.__curlHandle.setopt(pycurl.WRITEFUNCTION, curlBuffer.write)
		self.__curlHandle.perform()
		return curlBuffer.getvalue()
	
	# Mimic the request for the meaningful colors script from the official client
	def __getMeaningfulColors(self):
		self.__curlGet(MEANINGFUL_COLORS_URL)

	# Generate a random hex string of a given length
	def __randomHex(self, count = 8):
		import random
		chars = ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F")
		return ''.join([random.choice(chars) for _ in range(count)])

	# Sends the login credentials via an encrypted CURL request
	def __getSession(self):
		fields = {
			'UserName':urllib.quote_plus(self.username),
			'GoogleAuth':'',
			'PassWord':urllib.quote_plus(self.__password),
			'MyAccount':urllib.quote_plus('My Account')	}	
		response = self.__curlPost(GET_SESSION_URL, fields)
		r = json.loads(response)
		return r
	