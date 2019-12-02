from django.urls import path, re_path
from django.conf.urls import url
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about", views.about, name="about"),
    path("contact", views.contact, name="contact"),
    path("upload", views.simple_upload, name="upload"),
]
