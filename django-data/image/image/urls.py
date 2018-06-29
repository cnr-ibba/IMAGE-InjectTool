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
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views

# importing image views
from image_app.views import AboutView, IndexView

# renaming admin app (login, admin brand and page title)
# https://books.agiliq.com/projects/django-admin-cookbook/en/latest/change_text.html
admin.site.site_header = "IMAGE InjectTool Admin"
admin.site.site_title = "IMAGE InjectTool Admin Portal"
admin.site.index_title = "Welcome to IMAGE InjectTool Admin"

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^login/$',
        auth_views.LoginView.as_view(
            template_name='accounts/login.html'),
        name='login'),
    url(r'^logout/$',
        auth_views.LogoutView.as_view(
            template_name='accounts/logged_out.html'),
        name='logout'),
    url(r'^image_app/', include('image_app.urls', namespace="image_app")),
    url(r'^biosample/', include('biosample.urls', namespace="biosample")),
    url(r'^accounts/', include('accounts.urls', namespace="accounts")),
    url(r'^admin/', admin.site.urls),
    url(r'^about/$', AboutView.as_view(), name='about'),
]

# Activate django-debug-toolbar only when settings.DEBUG is True
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
