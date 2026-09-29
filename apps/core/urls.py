from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("nosotros/", views.about, name="about"),
    path("servicios/", views.service_list, name="service_list"),
    path("servicios/<slug:slug>/", views.service_detail, name="service_detail"),
    path("areas/<slug:slug>/", views.area_detail, name="area_detail"),
    path("planes/", views.plan_list, name="plan_list"),
    path("planes/<slug:slug>/", views.plan_detail, name="plan_detail"),
    path("equipo/", views.team_list, name="team_list"),
    path("equipo/<slug:slug>/", views.team_detail, name="team_detail"),
    path("preguntas-frecuentes/", views.faq_list, name="faq"),
    path("contacto/", views.contact, name="contact"),
    path("contacto/gracias/", views.contact_success, name="contact_success"),
    path("newsletter/", views.newsletter_subscribe, name="newsletter"),
    path("p/<slug:slug>/", views.page_detail, name="page_detail"),
]
