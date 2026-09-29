from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("categoria/<slug:slug>/", views.category_detail, name="category"),
    path("etiqueta/<slug:slug>/", views.tag_detail, name="tag"),
    path("<slug:slug>/", views.post_detail, name="post_detail"),
]
