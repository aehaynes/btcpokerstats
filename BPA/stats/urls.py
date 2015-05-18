from django.conf.urls import patterns, include, url
from django.contrib import admin
from stats import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'BPA.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    #url(r'^$', views.index, name='index'),
    url(r'^site/', views.site_stats, name='site_stats'),
    url(r'^tournament_search/', views.tourney_search, name='tourney_search'),
    url(r'^leaderboard_ring/', views.top_players_ring, name='top_ring'),
    url(r'^leaderboard_tourney/', views.top_players_tourney, name='top_tourney'),
    url(r'^hud/', views.player_hud, name='hud'),
    url(r'^test/', views.test, name='test'),
    url(r'^$', views.search_redirect, name='search_redirect'),
    #url(r'^$', views.search_redirect, name='search_redirect'),
    url(r'^players/(?P<pname>[\w\W]*)/$', views.search, name='search'),


)
