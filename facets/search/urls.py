from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('results/', views.results, name='results'),
    path('results/<str:index_name>/<str:doc_id>/', views.HighlightMusicDocView, name='highlight'),#name should be?
]
