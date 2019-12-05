from django.urls import path, re_path
from django.conf.urls import url
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("contact", views.contact, name="contact"),
    path("upload", views.simple_upload, name="upload"),
    path("accoutning", views.accounting, name="accounting"),
    path("downloadJE/<type>", views.download_accounting_JE, name="downloadJE"),
    path("schedule", views.schedule, name="schedule"),
]
