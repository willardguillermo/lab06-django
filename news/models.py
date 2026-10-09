"""Data models for the news portal."""

from django.db import models
from django.urls import reverse
from django.utils import timezone


class Category(models.Model):
    """A news section, e.g. Technology or Sports."""

    name = models.CharField("nombre", max_length=100, unique=True)
    slug = models.SlugField("slug", max_length=100, unique=True)
    description = models.TextField("descripción", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "categoría"
        verbose_name_plural = "categorías"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("news:category_detail", args=[self.slug])


class Author(models.Model):
    """A person who writes articles for the portal."""

    name = models.CharField("nombre", max_length=150)
    email = models.EmailField("correo", blank=True)
    bio = models.TextField("biografía", blank=True)
    photo = models.ImageField("foto", upload_to="authors/", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "autor"
        verbose_name_plural = "autores"

    def __str__(self):
        return self.name


class PublishedArticleManager(models.Manager):
    """Only the articles that are published and already visible."""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(is_published=True, published_at__lte=timezone.now())
        )


class Article(models.Model):
    """A news article with its featured image, author and categories."""

    title = models.CharField("título", max_length=200)
    slug = models.SlugField("slug", max_length=200, unique=True)
    summary = models.TextField("resumen")
    body = models.TextField("cuerpo")
    featured_image = models.ImageField(
        "imagen destacada", upload_to="articles/", blank=True
    )
    author = models.ForeignKey(
        Author,
        on_delete=models.PROTECT,
        related_name="articles",
        verbose_name="autor",
    )
    categories = models.ManyToManyField(
        Category, related_name="articles", verbose_name="categorías"
    )
    published_at = models.DateTimeField(
        "fecha de publicación", default=timezone.now
    )
    is_published = models.BooleanField("publicado", default=True)
    created_at = models.DateTimeField("creado el", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado el", auto_now=True)

    objects = models.Manager()
    published = PublishedArticleManager()

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "noticia"
        verbose_name_plural = "noticias"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("news:article_detail", args=[self.slug])
