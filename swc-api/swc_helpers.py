from datetime import datetime, timedelta
from pytz import utc
from time import time, sleep
from urllib2 import urlopen, Request
from json import loads

def _epoch(dt_str, fmt = "%Y-%m-%d %H:%M:%S-%Z"):
	epoch_start = datetime(1970,1,1,  tzinfo=utc)
	dt = datetime.strptime(dt_str+'-UTC',  fmt).replace(tzinfo = utc)
	# datetime.utcfromtimestamp(_epoch(dt_str)).strftime('%Y-%m-%d %H:%M:%S')
	return (dt-epoch_start).total_seconds()

def dt_offset(dt_str):
	return  datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S') - datetime.now()

def dt_correct(offset, fmt= '%Y-%m-%d'):
	cor_dt = datetime.now() + offset
	return cor_dt.strftime(fmt)

def getDateDir(offset):
	return dt_correct(offset, '%Y-%m-%d') + '/'

def getDateSeries(start):
	if type(start) == str:
		fmt = "%Y-%m-%d %H:%M:%S"
		start = datetime.strptime(start, fmt)

	end = datetime.now()
	step = timedelta(hours = 1)

	result = []

	while start < end:
		result.append(start.strftime('%Y-%m-%d %H:%M:%S'))
		start += step
	return result

def getAddressInfo(address):
	 req = Request('http://btc.blockr.io/api/v1/address/info/' + address)
	 response = urllib2.urlopen(req)
	 info = loads(response.read())
	 if info['status'] == 'success':
	 	return 0
