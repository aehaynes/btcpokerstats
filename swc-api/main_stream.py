import sys
import multiprocessing
from time import time
from swc_managers import stream_all_process, trackFileChanges

if __name__ == '__main__':
	if len(sys.argv) > 1:
		mins = float(sys.argv[1])
		end_time = time() + mins*60
		while time() < end_time:
			games = multiprocessing.Process(name='all', target=stream_all_process, args =(mins,))
			games.daemon = True
			tracker = multiprocessing.Process(name = 'tracker', target=trackFileChanges)
			tracker.daemon = False
			games.start()
			tracker.start()
			tracker.join()
	else:
		print "Error -- Insufficient parameters"