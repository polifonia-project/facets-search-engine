from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('results/', views.search_results.results, name='results'),
    path('query/', views.fetch_query, name="getabcquery")
    #path('results/<str:doc_id>/', views.search_results.HighlightMusicDocView, name='highlight_musicdoc')
]
