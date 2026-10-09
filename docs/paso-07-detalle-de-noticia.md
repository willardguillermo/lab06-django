# Paso 7: Detalle de noticia con imagen, autor y categorías

## Objetivo

Mostrar una noticia completa en `/noticias/<slug>/` heredando de
`base.html`: imagen destacada, autor, categorías, fecha y cuerpo.

## Qué se hizo

1. **Vista `article_detail`**: busca la noticia con
   `get_object_or_404(published_articles(), slug=slug)`. Al partir de
   `Article.published`, un slug inexistente, un **borrador** o una noticia
   **programada a futuro** devuelven **404**.
2. Calcula hasta 3 **noticias relacionadas** (comparten alguna categoría,
   sin repetir y excluyendo la actual).
3. **Plantilla `news/article_detail.html`**:
   - `{% block title %}{{ article.title }}{% endblock %}`.
   - `{% block content %}`: migas de pan, etiquetas de categorías, título,
     resumen como entradilla, autor, fecha completa
     (`date:"l j \d\e F \d\e Y, H:i"` → *sábado 15 de marzo de 2025, 10:30*),
     imagen destacada con `alt` y el cuerpo con `|linebreaks` (cada línea
     en blanco crea un `<p>`; ver paso 12 sobre el escapado).
   - Si no hay imagen, se muestra un recuadro con la inicial.
4. **`{% block sidebar %}` con `{{ block.super }}`**: el detalle agrega
   *"Sobre el autor"* (foto o inicial, correo, biografía con
   `default` + `truncatewords:40`) y *"Noticias relacionadas"*, y luego
   imprime `{{ block.super }}`, que inserta el contenido original del bloque
   de `base.html` (*Categorías* y *Últimas noticias*). Así se **amplía** el
   bloque en lugar de reemplazarlo por completo.

## Código relevante

`news/views.py`:

```python
def article_detail(request, slug):
    """Full article plus a few related articles from the same categories."""
    article = get_object_or_404(published_articles(), slug=slug)
    related_articles = (
        published_articles()
        .filter(categories__in=article.categories.all())
        .exclude(pk=article.pk)
        .distinct()[:MAX_RELATED_ARTICLES]
    )
    context = {"article": article, "related_articles": related_articles}
    return render(request, "news/article_detail.html", context)
```

`templates/news/article_detail.html` (fragmento):

```django
{% extends "base.html" %}

{% block title %}{{ article.title }}{% endblock %}

{% block content %}
  ...
  <figure class="article__figure">
    {% if article.featured_image %}
      <img src="{{ article.featured_image.url }}" alt="{{ article.title }}">
    {% else %} ... {% endif %}
  </figure>

  {# Autoescaping stays on: any HTML in the body is shown as text. #}
  <div class="article__body">
    {{ article.body|linebreaks }}
  </div>
{% endblock %}

{% block sidebar %}
  <section class="widget author-box">
    <h2 class="widget__title">Sobre el autor</h2> ...
  </section>
  {% if related_articles %} ... {% endif %}

  {{ block.super }}
{% endblock %}
```

## Cómo probarlo

```bash
python manage.py test news.tests.ArticleDetailViewTests -v 2
# Navegador: hacer clic en el título de cualquier tarjeta de la portada
```

## Casos de prueba

| Prueba | Resultado esperado |
|--------|--------------------|
| `test_detail_returns_200_and_extends_base` | 200, usa `article_detail.html` y `base.html`, `<title>` con el título |
| `test_detail_shows_image_author_and_categories` | `<img src="/media/articles/...">`, autor, `mailto:` y enlaces a sus categorías |
| `test_full_date_in_spanish` | `sábado 15 de marzo de 2025, 10:30` |
| `test_body_paragraphs_use_linebreaks` | Cada párrafo del cuerpo va en su propio `<p>` |
| `test_sidebar_block_super_keeps_categories` | Aparecen *Sobre el autor* **y** *Categorías* / *Últimas noticias* de la base |
| `test_related_articles_share_a_category` | Solo noticias con una categoría en común |
| `test_unknown_slug_returns_404` | Slug inexistente → 404 |
| `test_draft_and_future_articles_return_404` | Borrador o fecha futura → 404 |
| `test_placeholder_when_there_is_no_image` | Sin imagen se muestra el recuadro de reemplazo |

Las pruebas que crean imágenes usan un `MEDIA_ROOT` temporal
(`override_settings` + `tempfile`) que se borra al terminar, para no
ensuciar la carpeta `media/` real.

## Resultado

Página de noticia completa que reutiliza la estructura de la base y
extiende su barra lateral sin duplicar código.
