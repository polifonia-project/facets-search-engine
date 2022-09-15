from django.urls import path

from . import views

urlpatterns = [
    path('', views.uploaddata, name="uploaddata"),
    path('results/', views.processdata, name="processdata")
    #path('<str:doc_id>/', views.viewdata, name = "viewdata")
]
