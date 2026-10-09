# Paso 2: Directorio de plantillas, archivos estáticos y de medios

## Objetivo

Indicar a Django dónde están las plantillas del proyecto, los archivos
estáticos (CSS, logo) y los archivos de medios (imágenes subidas desde el
admin), y servir estos últimos durante el desarrollo.

## Qué se hizo

1. **Plantillas.** En `TEMPLATES` se agregó `DIRS = [BASE_DIR / "templates"]`
   para tener una carpeta `templates/` a nivel de proyecto (allí viven
   `base.html` y `news/*.html`). `APP_DIRS = True` se mantiene para que el
   admin encuentre sus propias plantillas.
2. **Procesador de contexto.** Se registró
   `news.context_processors.portal_sidebar`, que entrega a *todas* las
   plantillas las categorías (con su número de noticias publicadas) y las
   últimas 5 noticias, usadas por la barra lateral de `base.html`.
3. **Estáticos.** `STATIC_URL = "static/"`,
   `STATICFILES_DIRS = [BASE_DIR / "static"]` (carpeta del proyecto) y
   `STATIC_ROOT = BASE_DIR / "staticfiles"` (destino de `collectstatic` en
   producción).
4. **Medios.** `MEDIA_URL = "media/"` y `MEDIA_ROOT = BASE_DIR / "media"`:
   las imágenes destacadas se guardan en `media/articles/` y las fotos de
   autores en `media/authors/`.
5. **Servir medios en desarrollo.** En `config/urls.py` se agrega
   `static(MEDIA_URL, document_root=MEDIA_ROOT)` solo si `DEBUG=True`
   (en producción los sirve el servidor web).

## Código relevante

`config/settings.py`:

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Categories and latest articles for the shared sidebar
                'news.context_processors.portal_sidebar',
            ],
        },
    },
]

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
```

`config/urls.py`:

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("news.urls")),
]

# Serve uploaded media files during development only
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
```

## Cómo probarlo

```bash
python manage.py findstatic news/css/styles.css
python manage.py runserver
# Abrir http://127.0.0.1:8000/media/articles/<archivo>.jpg (tras el paso 11)
```

## Casos de prueba

| Caso | Resultado esperado |
|------|--------------------|
| `findstatic news/css/styles.css` | Muestra la ruta `.../static/news/css/styles.css` |
| `StaticFilesTests.test_finders_locate_css_and_logo` | Los *finders* encuentran el CSS y `logo.svg` |
| `ArticleDetailViewTests.test_detail_shows_image_author_and_categories` | La imagen se enlaza como `/media/articles/...` |
| GET a `/media/articles/<archivo>.jpg` con `DEBUG=True` | 200 y se ve la imagen |

## Resultado

Las plantillas se buscan en `templates/`, el CSS y el logo en `static/` y
las imágenes subidas se sirven desde `/media/` en desarrollo.
