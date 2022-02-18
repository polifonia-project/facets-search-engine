from rest_framework import routers
from . import views
from django.conf.urls import include
from django.views.decorators.csrf import csrf_exempt
from django.contrib import admin
from django.urls import path, re_path

from .views import *


from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from rest_framework.documentation import include_docs_urls

app_name="rest"

schema_view = get_schema_view(
   openapi.Info(
      title="Facets REST API",
      default_version='v1',
      description="List and usage of Facets REST services",
   ),
   public=False,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
	#url -> re_path because django 4 no longer support
	path('', views.welcome, name='welcome'),
	   #### Swagger documentation
	re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
	path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
	# Index management
	path('<str:index_name>/', views.index, name='index'),
	# Search in an index
	path('<str:index_name>/_search', views.search, name='search'),
	# Music document management
	path('<str:index_name>/<str:doc_id>/', views.document, name='document'),
	path('admin/', admin.site.urls),
]
