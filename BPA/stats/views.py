from django.shortcuts import render
from imports import *
from django.http import HttpResponseRedirect
from django.template.defaulttags import register

max_length_playernames = 200

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

# Create your views here.
def search_redirect(request):
	context_dict = {}
	context_dict['max_length_playernames'] = max_length_playernames
	if request.method == 'POST':
		# do a whitelist and strip
		query = request.POST['query'].strip()
		if query:
			return HttpResponseRedirect( '/stats/players/%s' % query)
	return render(request, 'stats/index.html', context_dict)	
def search(request, pname=None):
	context_dict = {}
	context_dict['max_length_playernames'] = max_length_playernames
	if request.method == 'GET':
		# do a whitelist and strip
		#pname.whitelist
		if pname:
			results = db.player_search(pname)
			if results:
				context_dict = results
	return render(request, 'stats/index.html', context_dict)


def top_players_ring(request):
	context_dict = db.leaderboard_ring()
	context_dict['max_length_playernames'] = max_length_playernames

	if request.method == 'POST':
		query = request.POST
		context_dict = db.leaderboard_ring( dict(query.iterlists()) )
	return render(request, 'stats/top_ring.html', context_dict)


def top_players_tourney(request):
	context_dict = db.leaderboard_tourney()
	context_dict['max_length_playernames'] = max_length_playernames

	if request.method == 'POST':
		query = request.POST
		context_dict = db.leaderboard_tourney( dict(query.iterlists()) )
	return render(request, 'stats/top_tourney.html', context_dict)


def player_hud(request):
	context_dict = db.hud_stats()
	context_dict['max_length_playernames'] = max_length_playernames
	if request.method == 'POST':
		query = request.POST
		context_dict = db.hud_stats( dict(query.iterlists()) )
	return render(request, 'stats/hud.html', context_dict)


def tourney_search(request):
	context_dict = db.tourney_search()
	context_dict['max_length_playernames'] = max_length_playernames

	if request.method == "POST":
		query = request.POST

		context_dict = db.tourney_search(dict(query.iterlists()) )
	else:
		pass
	return render(request, 'stats/tourney_search.html', context_dict)


# Experimental
def site_stats(request):
	context_dict = {}
	context_dict = db.site_stats()
	return render(request, 'stats/site_stats.html', context_dict)

def test(request):
	context_dict = {}
	if request.method == 'POST':
		query = request.POST
		context_dict = db.test_stats( dict(query.iterlists()) )
	return render(request, 'stats/test.html', context_dict)