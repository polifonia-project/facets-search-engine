from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name="index"),
    path('discovery/', views.search_results.DiscoveryView, name='discovery'),
    path('results/', views.search_results.results, name='results'),
    path('discovery_result/', views.search_results.DiscoveryResultView, name='discovery_result'),
    path('filtered_result/', views.search_results.FilteredResultView, name='filtered_result'),
    path('filtered_discovery_result/', views.search_results.DiscoveryFilteredResultView, name='filtered_discovery_result'),
    path('results/<str:index_name>/<str:doc_id>/', views.search_results.HighlightMusicDocView, name='highlight_musicdoc')
]
