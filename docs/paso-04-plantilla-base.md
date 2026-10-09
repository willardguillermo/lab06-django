# Paso 4: Plantilla base con bloques `title`, `content` y `sidebar`

## Objetivo

Escribir `templates/base.html` con la estructura común del portal
(cabecera, navegación, contenido, barra lateral y pie) y definir los
bloques que cada página puede reemplazar.

## Qué se hizo

1. `base.html` contiene el esqueleto HTML completo una sola vez: `<head>`
   con el CSS, cabecera con logo y menú, `<main>`, `<aside>` y `<footer>`.
2. Se definieron tres bloques:

   | Bloque | Contenido por defecto | Quién lo reemplaza |
   |--------|-----------------------|--------------------|
   | `{% block title %}` | `Portada` (se completa con `· El Observador`) | Cada página (título de la noticia, nombre de la categoría) |
   | `{% block content %}` | Vacío | Todas las páginas hijas |
   | `{% block sidebar %}` | Widgets *Categorías* y *Últimas noticias* | El detalle de noticia lo **amplía** con `{{ block.super }}` |

3. La barra lateral usa las variables `sidebar_categories` y
   `sidebar_latest_articles` del procesador de contexto
   `news.context_processors.portal_sidebar` (paso 2), por eso funciona en
   cualquier página sin repetir consultas en cada vista. Ambos `{% for %}`
   tienen `{% empty %}` (*"Aún no hay categorías."*).
4. Se resalta la categoría activa comparando `category.slug` con
   `request.resolver_match.kwargs.slug`.
5. Accesibilidad: enlace *"Saltar al contenido"*, `aria-label` en la
   navegación y `aria-current="page"` en la portada.

## Estructura de plantillas

```text
templates/                         # DIRS del proyecto (paso 2)
├── base.html                      # Esqueleto común: bloques title, content, sidebar
└── news/
    ├── _article_card.html         # Fragmento (prefijo "_"): tarjeta de una noticia
    ├── home.html                  # extends base  → include _article_card (for/empty)
    ├── article_detail.html        # extends base  → sidebar con {{ block.super }}
    └── category_detail.html       # extends base  → include _article_card (for/empty)

static/                            # STATICFILES_DIRS
└── news/
    ├── css/styles.css             # Estilos del portal (tema claro/oscuro, responsive)
    └── img/logo.svg               # Logo y favicon
```

Flujo de herencia e inclusión:

```text
                       base.html
         ┌──────────── title · content · sidebar ───────────┐
         │                     │                            │
     home.html        category_detail.html         article_detail.html
  (content: grid)      (content: grid)          (content: noticia completa;
         │                     │                 sidebar: autor + relacionadas
         └──── {% include "news/_article_card.html" %} ────  + {{ block.super }})
```

- **Herencia (`{% extends %}`)**: las páginas hijas solo escriben lo que
  cambia; el resto viene de `base.html`.
- **Inclusión (`{% include %}`)**: la tarjeta de noticia se escribe una vez
  y se reutiliza en la portada y en el listado por categoría.
- Convenciones: las plantillas de la app van en `templates/news/` (espacio
  de nombres, evita choques con otras apps) y los fragmentos empiezan con
  `_` para distinguirlos de las páginas completas.

## Código relevante

`templates/base.html` (fragmento):

```django
{% load static %}<!DOCTYPE html>
<html lang="es">
<head>
  <title>{% block title %}Portada{% endblock %} · El Observador</title>
  <link rel="stylesheet" href="{% static 'news/css/styles.css' %}">
</head>
<body>
  <header class="site-header">...</header>
  <div class="container layout">
    <main id="contenido" class="layout__main">
      {% block content %}{% endblock %}
    </main>
    <aside class="layout__sidebar" aria-label="Barra lateral">
      {% block sidebar %}
        <section class="widget">
          <h2 class="widget__title">Categorías</h2>
          <ul class="category-list">
            {% for category in sidebar_categories %}
              <li><a href="{% url 'news:category_detail' category.slug %}">
                {{ category.name }} <span class="badge">{{ category.article_count }}</span>
              </a></li>
            {% empty %}
              <li class="muted small">Aún no hay categorías.</li>
            {% endfor %}
          </ul>
        </section>
        ...
      {% endblock %}
    </aside>
  </div>
  <footer class="site-footer">...</footer>
</body>
</html>
```

`news/context_processors.py`:

```python
def portal_sidebar(request):
    published = Q(
        articles__is_published=True,
        articles__published_at__lte=timezone.now(),
    )
    return {
        "sidebar_categories": Category.objects.annotate(
            article_count=Count("articles", filter=published)
        ),
        "sidebar_latest_articles": Article.published.only(
            "title", "slug", "published_at"
        )[:LATEST_ARTICLES_LIMIT],
    }
```

## Cómo probarlo

```bash
python manage.py test news.tests.HomeViewTests -v 2
python manage.py runserver   # y revisar cabecera, barra lateral y pie en todas las páginas
```

## Casos de prueba

| Prueba | Resultado esperado |
|--------|--------------------|
| `HomeViewTests.test_home_returns_200_with_base_and_fragment` | Se usan `news/home.html`, `base.html` y `news/_article_card.html` |
| `HomeViewTests.test_title_block_is_overridden` | `<title>Portada · El Observador</title>` |
| `HomeViewTests.test_sidebar_counts_only_published_articles` | Los contadores no incluyen borradores |
| `HomeViewTests.test_sidebar_empty_messages` | Sin datos: *"Aún no hay categorías."* y *"Aún no hay noticias publicadas."* |
| `CategoryDetailViewTests.test_active_category_is_highlighted_in_sidebar` | Solo la categoría actual lleva `is-active` |

## Resultado

Todas las páginas comparten la misma cabecera, barra lateral y pie, y solo
definen su contenido propio.
