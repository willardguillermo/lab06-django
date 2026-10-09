"""URL patterns for the public pages of the news portal."""

from django.urls import path

from . import views

app_name = "news"

urlpatterns = [
    path("", views.home, name="home"),
    path(
        "noticias/<slug:slug>/",
        views.article_detail,
        name="article_detail",
    ),
    path(
        "categorias/<slug:slug>/",
        views.category_detail,
        name="category_detail",
    ),
]
