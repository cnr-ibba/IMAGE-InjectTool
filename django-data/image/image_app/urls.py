"""image URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import url
from django.contrib.auth.decorators import login_required

# TODO: remove old_views after migrating views in their apposite submodule
from image_app import views

# from django.conf.urls import include
# from django.contrib import admin


urlpatterns = [
    # to upload data in image database
    # TODO: deal with excel upload
    url(r'data_upload/$',
        login_required(views.DataSourceView.as_view()),
        name='data_upload'),

    url(r'^sampletab1/$', views.sampletab1, name='sampletab1'),
    url(r'^sampletab2/$', views.sampletab2, name='sampletab2'),
    url(r'^check_metadata/$', views.check_metadata, name='check_metadata'),
    url(r'^upload_cryoweb/$', views.upload_cryoweb, name='upload_cryoweb'),

    url(r'^import_from_cryoweb/$',
        views.import_from_cryoweb,
        name='import_from_cryoweb'),

    url(r'^truncate_image_tables/$',
        views.truncate_image_tables,
        name='truncate_image_tables'),

    url(r'^truncate_cryoweb_tables/$',
        views.truncate_cryoweb_tables,
        name='truncate_cryoweb_tables'),

    url(r'^truncate_databases/$',
        views.truncate_databases,
        name='truncate_databases'),

    url(r'^update_user/$',
        views.update_profile,
        name='update_profile'),

    url(r'^sample/(?P<pk>[0-9]+)/json/$',
        login_required(views.SampleJSON.as_view()),
        name='sample-json'),

    url(r'^samples/json/$',
        login_required(views.SampleListJSON.as_view()),
        name='samplelist-json'),

    url(r'^animal/(?P<pk>[0-9]+)/json/$',
        login_required(views.AnimalJSON.as_view()),
        name='animal-json'),

    url(r'^animals/json/$',
        login_required(views.AnimalListJSON.as_view()),
        name='animallist-json'),

    url(r'^animal/(?P<pk>[0-9]+)/biosample/$',
        login_required(views.BioSampleJSON.as_view()),
        name='animal-biosample'),

    url(r'^animals/biosample/$',
        login_required(views.BioSampleListJSON.as_view()),
        name='animallist-biosample'),
]
