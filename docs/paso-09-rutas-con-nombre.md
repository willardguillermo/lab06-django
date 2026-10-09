# Paso 9: Rutas con nombre y la etiqueta `{% url %}`

## Objetivo

Dar nombre a las rutas y generar todos los enlaces con `{% url %}` (y
`reverse()` en Python) en lugar de escribir las direcciones a mano.

## Qué se hizo

1. `news/urls.py` declara `app_name = "news"` (espacio de nombres) y tres
   rutas con nombre; `config/urls.py` las incluye con `include("news.urls")`.

   | URL | Nombre | Vista |
   |-----|--------|-------|
   | `/` | `news:home` | `home` |
   | `/noticias/<slug>/` | `news:article_detail` | `article_detail` |
   | `/categorias/<slug>/` | `news:category_detail` | `category_detail` |
   | `/admin/` | `admin:index` | Panel de administración |

2. Las plantillas usan `{% url 'news:home' %}`,
   `{% url 'news:article_detail' article.slug %}`,
   `{% url 'news:category_detail' category.slug %}` y
   `{% url 'admin:index' %}`.
3. Los modelos usan `reverse()` en `get_absolute_url()` (lo aprovecha el
   botón *"Ver en el sitio"* del admin).
4. **Ventaja**: si mañana `/noticias/` pasa a llamarse `/articulos/`, solo
   se cambia `news/urls.py`; ninguna plantilla se toca y no quedan enlaces
   rotos. El conversor `<slug:slug>` además rechaza (404) valores con
   caracteres no válidos.

## Código relevante

`news/urls.py`:

```python
app_name = "news"

urlpatterns = [
    path("", views.home, name="home"),
    path("noticias/<slug:slug>/", views.article_detail, name="article_detail"),
    path("categorias/<slug:slug>/", views.category_detail, name="category_detail"),
]
```

## Cómo probarlo

```bash
python manage.py test news.tests.UrlTests -v 2
python manage.py shell -c "from django.urls import reverse; print(reverse('news:article_detail', args=['demo']))"
# /noticias/demo/
```

## Casos de prueba

| Prueba | Resultado esperado |
|--------|--------------------|
| `UrlTests.test_named_urls_reverse` | `/`, `/noticias/mi-noticia/`, `/categorias/deportes/` |
| `UrlTests.test_urls_resolve_to_view_names` | Cada URL se resuelve al nombre correcto |
| `ModelTests.test_get_absolute_url` | `get_absolute_url()` coincide con la ruta con nombre |
| `HomeViewTests.test_navigation_links_use_named_urls` | El HTML contiene los `href` generados por `{% url %}` |

## Resultado

Ningún enlace interno está escrito a mano: todos dependen del nombre de la
ruta.
