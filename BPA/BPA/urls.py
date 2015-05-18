from django.conf.urls import patterns, include, url
from django.contrib import admin
from stats import views

urlpatterns = patterns('',
    # Examples:
     url(r'^$', views.search_redirect, name='search_redirect'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^stats/', include('stats.urls')),
)
