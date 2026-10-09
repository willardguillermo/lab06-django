# Paso 6: Portada con `for`, `empty` y filtros de fecha y recorte

## Objetivo

Construir la portada (`/`) que lista las noticias publicadas con
`{% for %}`, muestra un mensaje con `{% empty %}` cuando no hay ninguna, y
usa los filtros `date` y `truncatewords`.

## Qué se hizo

1. **Vista `home`** (`news/views.py`): pasa `articles`, que son las noticias
   de `Article.published` con `select_related("author")` y
   `prefetch_related("categories")` para evitar una consulta por tarjeta.
2. **Plantilla `news/home.html`**: extiende `base.html`, recorre
   `articles` con `{% for %}` e incluye la tarjeta del paso 5.
3. **`{% empty %}`**: si no hay noticias publicadas se muestra
   *"Todavía no hay noticias publicadas."* con un enlace al admin.
4. **Filtros usados**:

   | Filtro | Dónde | Ejemplo de salida |
   |--------|-------|-------------------|
   | `date:"j \d\e F \d\e Y"` | Fecha en la tarjeta | `15 de marzo de 2025` (en español por `LANGUAGE_CODE = "es"`; `\d\e` escapa las letras para que no se interpreten como formato) |
   | `date:'c'` | Atributo `datetime` de `<time>` | `2025-03-15T10:30:00-05:00` (ISO 8601) |
   | `date:"j M Y"` | Barra lateral | `15 Mar 2025` |
   | `truncatewords:25` / `:45` | Resumen de la tarjeta | Corta a 25 palabras (45 en la destacada) y agrega `…` |
   | `first\|upper` | Imagen de reemplazo | Inicial del título |
   | `{% now "l j \d\e F \d\e Y" %}` | Encabezado | `viernes 9 de octubre de 2026` |

5. `forloop.first` marca la primera noticia como destacada.

## Código relevante

`news/views.py`:

```python
def published_articles():
    """Published articles with their author and categories preloaded."""
    return Article.published.select_related("author").prefetch_related(
        "categories"
    )


def home(request):
    """Front page: every published article, newest first."""
    context = {"articles": published_articles()}
    return render(request, "news/home.html", context)
```

`templates/news/home.html`:

```django
{% extends "base.html" %}

{% block title %}Portada{% endblock %}

{% block content %}
  <header class="page-header">
    <p class="eyebrow">{% now "l j \d\e F \d\e Y" %}</p>
    <h1 class="page-title">Últimas noticias</h1>
  </header>

  <div class="card-grid">
    {% for article in articles %}
      {% include "news/_article_card.html" with article=article featured=forloop.first %}
    {% empty %}
      <div class="empty-state">
        <p class="empty-state__title">Todavía no hay noticias publicadas.</p>
        <p class="muted">Vuelve pronto o publica la primera desde la
          <a href="{% url 'admin:index' %}">administración</a>.</p>
      </div>
    {% endfor %}
  </div>
{% endblock %}
```

## Cómo probarlo

```bash
python manage.py test news.tests.HomeViewTests -v 2
python manage.py runserver   # abrir http://127.0.0.1:8000/
```

## Casos de prueba

| Prueba | Resultado esperado |
|--------|--------------------|
| `test_home_returns_200_with_base_and_fragment` | 200 y plantillas `home`, `base` y fragmento |
| `test_home_lists_only_published_articles_newest_first` | Solo publicadas, de la más reciente a la más antigua; el borrador no aparece |
| `test_summary_is_truncated_with_truncatewords` | Aparece `palabra45 …` (destacada) y `palabra25 …`; nunca `palabra46` |
| `test_date_filter_renders_spanish_month` | `15 de marzo de 2025` y `2 de enero de 2025` |
| `test_empty_message_when_there_are_no_articles` | *"Todavía no hay noticias publicadas."* |
| `test_first_card_is_featured` | Una sola tarjeta destacada |

## Resultado

Portada con cuadrícula de tarjetas, la noticia más reciente destacada,
fechas en español y resúmenes de longitud uniforme.
