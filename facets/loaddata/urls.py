from django.urls import path

from . import views

urlpatterns = [
    path('', views.uploaddata, name="uploaddata"),
    path('results/', views.processdata, name="processdata"),
    path('index_added/', views.add_new_index, name = "index_added"),
    path('loaded_metadata/', views.add_metadata, name = "loaded_metadata")
    #path('<str:doc_id>/', views.viewdata, name = "viewdata")
]
