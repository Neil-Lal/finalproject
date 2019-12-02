"""final_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf.urls import url
from datetime import datetime
from django.conf.urls.static import static
from django.conf import settings

import django.contrib.auth.views
import app.forms
import app.views

urlpatterns = [
    path("", include("app.urls")),
    path('admin/', admin.site.urls),
    #url(r'^login/$', include('django.contrib.auth.urls')),
    url(r'^login/$',
        django.contrib.auth.views.LoginView.as_view(),
        {
            'template_name': 'app/login.html',
            'authentication_form': app.forms.BootstrapAuthenticationForm,
            'extra_context':
            {
                'title': 'Log in',
                'year': datetime.now().year,
            }
        },
        name='login'),
    url(r'^logout$',
        django.contrib.auth.views.LogoutView.as_view(),
        {
            'next_page': '/',
        },
        name='logout'),
]

# Removed media folder and moved to storing data in database
#if settings.DEBUG:
#    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)