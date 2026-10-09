# Paso 10: `{% load static %}`, CSS y logo

## Objetivo

Cargar la hoja de estilos y el logo con la etiqueta `{% static %}` y
comprobar que tanto los archivos estáticos como las imágenes subidas se
sirven correctamente.

## Qué se hizo

1. `base.html` empieza con `{% load static %}` y enlaza:
   - `{% static 'news/css/styles.css' %}` → `/static/news/css/styles.css`
   - `{% static 'news/img/logo.svg' %}` → logo de la cabecera y favicon.
2. **`static/news/css/styles.css`** (CSS puro, sin *frameworks*):
   - Variables CSS en `:root` (colores, fuentes, radios); el tema oscuro
     solo las redefine dentro de `@media (prefers-color-scheme: dark)`.
   - Diseño en dos columnas (contenido + barra lateral) que pasa a una
     columna en pantallas angostas; cuadrícula de tarjetas responsiva.
   - Tipografías *Inter* y *Merriweather* (Google Fonts) con respaldo a
     fuentes del sistema; respeto de `prefers-reduced-motion`.
3. **`static/news/img/logo.svg`**: logo vectorial (pesa poco y se ve nítido
   en cualquier tamaño).
4. Diferencia entre **estáticos** y **medios**:

   | | Estáticos (`static/`) | Medios (`media/`) |
   |---|---|---|
   | Qué son | Archivos del proyecto (CSS, JS, logo) | Archivos subidos por usuarios (imágenes de noticias) |
   | Se versionan | Sí | No (`.gitignore`) |
   | En plantillas | `{% static 'ruta' %}` | `{{ article.featured_image.url }}` |
   | En desarrollo | `runserver` + `django.contrib.staticfiles` | `static()` en `config/urls.py` con `DEBUG=True` |
   | En producción | `collectstatic` → `STATIC_ROOT` | Servidor web o almacenamiento externo |

## Código relevante

`templates/base.html`:

```django
{% load static %}<!DOCTYPE html>
...
<link rel="icon" href="{% static 'news/img/logo.svg' %}" type="image/svg+xml">
<link rel="stylesheet" href="{% static 'news/css/styles.css' %}">
...
<img class="brand__logo" src="{% static 'news/img/logo.svg' %}" alt="" width="36" height="36">
```

## Cómo probarlo

```bash
python manage.py findstatic news/css/styles.css news/img/logo.svg
python manage.py test news.tests.StaticFilesTests -v 2
python manage.py runserver
# http://127.0.0.1:8000/static/news/css/styles.css → 200
# Herramientas de desarrollador → pestaña Red: styles.css, logo.svg y los .jpg de /media/ con estado 200
```

## Casos de prueba

| Prueba | Resultado esperado |
|--------|--------------------|
| `StaticFilesTests.test_finders_locate_css_and_logo` | `finders.find()` encuentra ambos archivos |
| `StaticFilesTests.test_base_template_links_static_files` | El HTML contiene `/static/news/css/styles.css` y `/static/news/img/logo.svg` |
| `StaticFilesTests.test_runserver_style_static_view_serves_css` | La vista de `staticfiles` responde 200 con `text/css` |
| `LoadSampleDataCommandTests.test_sample_articles_appear_on_home` | Las tarjetas enlazan imágenes de `/media/articles/` |

## Resultado

El portal se muestra con su diseño, su logo y las imágenes destacadas de
cada noticia.

## Captura sugerida

Portada con estilos y pestaña *Red* del navegador mostrando `styles.css`,
`logo.svg` y una imagen de `/media/articles/` con estado 200.
