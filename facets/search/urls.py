from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('results/', views.search_results.results, name='results'),
    path('filtered_result/', views.search_results.FilteredResultView, name='filtered_result'),
    path('results/<str:index_name>/<str:doc_id>/', views.search_results.HighlightMusicDocView, name='highlight_musicdoc')
]
