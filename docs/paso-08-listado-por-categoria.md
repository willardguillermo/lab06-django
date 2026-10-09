# Paso 8: Listado por categoría reutilizando el fragmento

## Objetivo

Mostrar en `/categorias/<slug>/` las noticias publicadas de una categoría,
reutilizando la tarjeta `_article_card.html` del paso 5.

## Qué se hizo

1. **Vista `category_detail`**: obtiene la categoría con
   `get_object_or_404(Category, slug=slug)` y filtra
   `published_articles().filter(categories=category)`.
2. **Plantilla `news/category_detail.html`**: extiende `base.html`,
   muestra migas de pan, nombre y descripción de la categoría y el total
   con `length` y `pluralize` (*"1 noticia publicada"*,
   *"3 noticias publicadas"*).
3. El listado usa el mismo `{% include "news/_article_card.html" %}` que la
   portada, con `{% empty %}` → *"No hay noticias publicadas en esta
   categoría."*
4. En la barra lateral (heredada) la categoría actual se resalta con la
   clase `is-active`.

## Código relevante

`news/views.py`:

```python
def category_detail(request, slug):
    """A category with the published articles that belong to it."""
    category = get_object_or_404(Category, slug=slug)
    context = {
        "category": category,
        "articles": published_articles().filter(categories=category),
    }
    return render(request, "news/category_detail.html", context)
```

`templates/news/category_detail.html` (fragmento):

```django
{% extends "base.html" %}

{% block title %}{{ category.name }}{% endblock %}

{% block content %}
  <header class="page-header">
    <h1 class="page-title">{{ category.name }}</h1>
    <p class="muted small">{{ articles|length }} noticia{{ articles|length|pluralize }} publicada{{ articles|length|pluralize }}</p>
  </header>

  <div class="card-grid">
    {% for article in articles %}
      {% include "news/_article_card.html" with article=article %}
    {% empty %}
      <div class="empty-state">
        <p class="empty-state__title">No hay noticias publicadas en esta categoría.</p>
      </div>
    {% endfor %}
  </div>
{% endblock %}
```

## Cómo probarlo

```bash
python manage.py test news.tests.CategoryDetailViewTests -v 2
# Navegador: hacer clic en una categoría de la barra lateral o en una etiqueta
```

## Casos de prueba

| Prueba | Resultado esperado |
|--------|--------------------|
| `test_category_page_uses_base_and_fragment` | Usa `category_detail.html`, `base.html` y `_article_card.html`; muestra la descripción |
| `test_category_lists_only_its_published_articles` | Solo las noticias de esa categoría; ni las de otra ni los borradores; *"1 noticia publicada"* |
| `test_active_category_is_highlighted_in_sidebar` | Una sola categoría con `is-active` |
| `test_empty_category_shows_message` | *"No hay noticias publicadas en esta categoría."* y *"0 noticias publicadas"* |
| `test_unknown_category_returns_404` | Slug inexistente → 404 |

## Resultado

Cada sección del portal tiene su propia página sin escribir de nuevo el
HTML de las tarjetas.
