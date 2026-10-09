# Paso 11: Admin personalizado y datos de ejemplo

## Objetivo

Personalizar el panel de administración con `list_display`, `list_filter`
y `search_fields`, cargar **seis noticias en tres categorías** y comprobar
que aparecen en el portal.

## Qué se hizo

1. **`news/admin.py`** registra los tres modelos con `@admin.register`:

   | Modelo | `list_display` | `list_filter` | `search_fields` |
   |--------|----------------|---------------|-----------------|
   | `Category` | nombre, slug, nº de noticias | publicado | nombre, descripción |
   | `Author` | nombre, correo, nº de noticias | categorías de sus noticias | nombre, correo, biografía |
   | `Article` | miniatura, título, autor, categorías, fecha, publicado | publicado, categorías, autor, fecha | título, resumen, cuerpo, nombre del autor |

   Extras en `ArticleAdmin`: `prepopulated_fields` (el slug se completa
   desde el título), `list_editable` para publicar/despublicar desde el
   listado, `filter_horizontal` para las categorías, `date_hierarchy`,
   `fieldsets` por secciones, campos de auditoría de solo lectura y una
   miniatura generada con `format_html` (que escapa la URL y el texto).
   Los contadores usan `annotate(Count(...))` y el listado de noticias usa
   `list_select_related` / `prefetch_related` para no hacer una consulta
   por fila.
2. **Comando `load_sample_data`**
   (`news/management/commands/load_sample_data.py`):
   - Crea **3 categorías** (Tecnología, Deportes, Cultura), **3 autores** y
     **6 noticias** publicadas en los últimos días, varias en más de una
     categoría (cada categoría queda con al menos 2 noticias).
   - Genera con **Pillow** una imagen destacada de 1200×675 por noticia
     (degradado del color de la categoría con el título).
   - Es **idempotente**: usa `update_or_create` por slug/correo y solo
     genera la imagen si la noticia aún no tiene una; ejecutarlo dos veces
     no duplica filas ni archivos.
   - La noticia `como-proteger-tu-sitio-web-de-ataques-xss` guarda HTML en
     su cuerpo para la prueba de escapado del paso 12.

## Código relevante

`news/admin.py` (fragmento):

```python
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "thumbnail", "title", "author", "category_list",
        "published_at", "is_published",
    )
    list_filter = ("is_published", "categories", "author", "published_at")
    search_fields = ("title", "summary", "body", "author__name")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_published",)
    filter_horizontal = ("categories",)
    date_hierarchy = "published_at"
```

## Cómo probarlo

```bash
python manage.py load_sample_data
# Datos de ejemplo cargados: 3 categorías, 3 autores, 6 noticias (6 nuevas, 6 imágenes generadas).
python manage.py load_sample_data
# ... 6 noticias (0 nuevas, 0 imágenes generadas).
python manage.py test news.tests.AdminPagesTests news.tests.LoadSampleDataCommandTests -v 2
```

Verificación manual: entrar a <http://127.0.0.1:8000/admin/news/article/>,
buscar *"XSS"* o *"Diego"*, filtrar por categoría; luego abrir
<http://127.0.0.1:8000/> y comprobar que aparecen las 6 noticias con su
imagen y que la barra lateral muestra los contadores por categoría.

## Casos de prueba

| Prueba | Resultado esperado |
|--------|--------------------|
| `AdminPagesTests.test_changelist_pages_return_200` | Listados de categorías, autores y noticias → 200 |
| `AdminPagesTests.test_add_pages_return_200` | Formularios de alta de los 3 modelos → 200 |
| `AdminPagesTests.test_search_finds_results` | La búsqueda devuelve 1 resultado en cada modelo (también por nombre de autor) |
| `AdminPagesTests.test_article_filter_by_category` | El filtro por categoría deja solo sus noticias |
| `AdminPagesTests.test_article_change_page_returns_200` | Formulario de edición con *fieldsets* → 200 |
| `AdminPagesTests.test_anonymous_user_is_redirected_to_login` | Sin sesión → redirección al login |
| `LoadSampleDataCommandTests.test_creates_expected_data` | 3 / 3 / 6, todas publicadas, con imagen y categorías |
| `LoadSampleDataCommandTests.test_every_category_has_articles` | Cada categoría tiene al menos 2 noticias |
| `LoadSampleDataCommandTests.test_running_twice_is_idempotent` | Segunda ejecución: mismos totales, *0 nuevas, 0 imágenes generadas* |
| `LoadSampleDataCommandTests.test_sample_articles_appear_on_home` | La portada muestra las 6 noticias con imágenes de `/media/articles/` |

## Resultado

El admin permite gestionar el contenido cómodamente y el portal se llena
con datos realistas en un solo comando.

## Captura sugerida

Listado de noticias del admin con miniaturas, filtros laterales y la caja
de búsqueda; y la portada con las 6 noticias.
