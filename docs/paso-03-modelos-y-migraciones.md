# Paso 3: Modelos `Article`, `Category` y `Author`, migración y superusuario

## Objetivo

Declarar los modelos del portal con su imagen destacada, su fecha de
publicación y sus relaciones; aplicar la migración y crear el superusuario.

## Qué se hizo

1. **`Category`**: `name` y `slug` únicos, `description` opcional.
   `get_absolute_url()` devuelve `/categorias/<slug>/`.
2. **`Author`**: `name`, `email`, `bio` y `photo` (`ImageField`, opcional,
   en `media/authors/`).
3. **`Article`**:
   - `title`, `slug` único (se usa en la URL), `summary` (resumen para las
     tarjetas) y `body` (texto completo, sin HTML).
   - `featured_image`: `ImageField(upload_to="articles/")`.
   - `author`: `ForeignKey` a `Author` con `on_delete=PROTECT` (no se puede
     borrar un autor que tiene noticias).
   - `categories`: `ManyToManyField` a `Category` (una noticia puede estar
     en varias secciones).
   - `published_at` (por defecto `timezone.now`) e `is_published`.
   - `created_at` / `updated_at` de auditoría.
   - Orden por defecto: `-published_at` (más recientes primero).
   - `get_absolute_url()` devuelve `/noticias/<slug>/`.
4. **Manager `published`**: `Article.published` solo devuelve noticias con
   `is_published=True` **y** `published_at <= ahora`; así los borradores y
   las noticias programadas a futuro nunca llegan a las plantillas.
   `Article.objects` sigue devolviendo todo (lo usa el admin).
5. Nombres en español (`verbose_name`) para que el admin se vea en español.
6. Se generó `news/migrations/0001_initial.py`, se migró y se creó el
   superusuario.

## Código relevante

`news/models.py` (fragmento):

```python
class PublishedArticleManager(models.Manager):
    """Only the articles that are published and already visible."""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(is_published=True, published_at__lte=timezone.now())
        )


class Article(models.Model):
    title = models.CharField("título", max_length=200)
    slug = models.SlugField("slug", max_length=200, unique=True)
    summary = models.TextField("resumen")
    body = models.TextField("cuerpo")
    featured_image = models.ImageField(
        "imagen destacada", upload_to="articles/", blank=True
    )
    author = models.ForeignKey(
        Author, on_delete=models.PROTECT, related_name="articles",
        verbose_name="autor",
    )
    categories = models.ManyToManyField(
        Category, related_name="articles", verbose_name="categorías"
    )
    published_at = models.DateTimeField(
        "fecha de publicación", default=timezone.now
    )
    is_published = models.BooleanField("publicado", default=True)

    objects = models.Manager()
    published = PublishedArticleManager()

    class Meta:
        ordering = ["-published_at"]

    def get_absolute_url(self):
        return reverse("news:article_detail", args=[self.slug])
```

## Cómo probarlo

```bash
python manage.py makemigrations news
python manage.py migrate
python manage.py createsuperuser
python manage.py test news.tests.ModelTests -v 2
```

## Casos de prueba

| Prueba | Resultado esperado |
|--------|--------------------|
| `test_str_methods` | `str()` devuelve el nombre / título |
| `test_get_absolute_url` | `/categorias/tecnologia/` y `/noticias/visible/` |
| `test_published_manager_hides_drafts_and_future_articles` | `Article.published` excluye borradores y noticias con fecha futura |
| `test_articles_are_ordered_newest_first` | Orden por `-published_at` |
| `test_reverse_relations` | `category.articles` y `author.articles` funcionan |

## Resultado

Tres tablas (`news_category`, `news_author`, `news_article`) más la tabla
intermedia de la relación muchos a muchos, y un superusuario para el admin.
