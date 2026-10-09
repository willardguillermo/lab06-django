# Laboratorio 06 — Motor de plantillas con Django (portal de noticias)

Proyecto de laboratorio del curso de Desarrollo de Aplicaciones Empresariales.
Se construye **El Observador**, un portal de noticias que pone en práctica el
**motor de plantillas de Django**: herencia con bloques, fragmentos
reutilizables con `{% include %}`, etiquetas `for`/`empty`, filtros de fecha
y de texto, rutas con nombre, archivos estáticos y de medios, y el
**escapado automático** como defensa contra XSS.

- Proyecto Django: `config`
- Aplicación: `news`
- Modelos: `Category`, `Author`, `Article` (con imagen destacada)
- Base de datos: SQLite (local, no versionada)

## Requisitos

- Python 3.12 o superior (probado con Python 3.14.8)
- Django 6.1.2, Pillow 12.3 y python-decouple (ver `requirements.txt`)
- Git

## Instalación y ejecución

```bash
# 1. Crear y activar el entorno virtual
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Generar una SECRET_KEY aleatoria y pegarla en .env:
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"

# 4. Aplicar migraciones
python manage.py migrate

# 5. Crear un superusuario
python manage.py createsuperuser

# 6. Cargar datos de ejemplo (3 categorías, 3 autores, 6 noticias con imagen)
python manage.py load_sample_data

# 7. Ejecutar el servidor de desarrollo
python manage.py runserver
```

Luego abrir <http://127.0.0.1:8000/>.

## URLs

| URL | Nombre | Descripción |
|-----|--------|-------------|
| `/` | `news:home` | Portada con las noticias publicadas |
| `/noticias/<slug>/` | `news:article_detail` | Detalle de una noticia |
| `/categorias/<slug>/` | `news:category_detail` | Noticias de una categoría |
| `/admin/` | `admin:index` | Panel de administración |
| `/static/...` | — | CSS y logo (`static/`) |
| `/media/...` | — | Imágenes subidas (`media/`, solo con `DEBUG=True`) |

Ejemplo del paso 12 (escapado automático):
<http://127.0.0.1:8000/noticias/como-proteger-tu-sitio-web-de-ataques-xss/>

## Variables de entorno (`.env`)

| Variable        | Descripción                                  | Ejemplo                 |
|-----------------|----------------------------------------------|-------------------------|
| `SECRET_KEY`    | Clave secreta de Django (no compartir)       | `cadena-aleatoria`      |
| `DEBUG`         | Modo depuración (sirve `/media/` si es `True`) | `True`                |
| `ALLOWED_HOSTS` | Hosts permitidos separados por comas         | `127.0.0.1,localhost`   |

## Estructura de plantillas

```text
templates/                         # DIRS del proyecto (settings.TEMPLATES)
├── base.html                      # Esqueleto común: bloques title, content, sidebar
└── news/
    ├── _article_card.html         # Fragmento: tarjeta de una noticia
    ├── home.html                  # Portada
    ├── article_detail.html        # Detalle de noticia
    └── category_detail.html       # Listado por categoría

static/                            # STATICFILES_DIRS
└── news/
    ├── css/styles.css             # Estilos (tema claro/oscuro, responsive)
    └── img/logo.svg               # Logo y favicon

news/context_processors.py         # Datos de la barra lateral para todas las páginas
```

Cómo se combinan:

```text
                       base.html
         ┌──────────── title · content · sidebar ───────────┐
         │                     │                            │
     home.html        category_detail.html         article_detail.html
  (content: grid)      (content: grid)          (content: noticia completa;
         │                     │                 sidebar: autor + relacionadas
         └──── {% include "news/_article_card.html" %} ────  + {{ block.super }})
```

- **`base.html`** define la estructura una sola vez (cabecera, menú,
  `<main>`, `<aside>`, pie) y tres bloques: `title`, `content` y `sidebar`.
- Las **páginas** (`home`, `article_detail`, `category_detail`) usan
  `{% extends "base.html" %}` y solo rellenan los bloques que cambian.
- **`_article_card.html`** es un fragmento (prefijo `_`) que se incluye con
  `{% include ... with article=article %}` desde la portada y desde el
  listado por categoría: la tarjeta se escribe una vez.
- El detalle **amplía** la barra lateral con `{{ block.super }}`: agrega
  *Sobre el autor* y *Noticias relacionadas* y conserva *Categorías* y
  *Últimas noticias* de la base.
- La barra lateral de la base obtiene sus datos del procesador de contexto
  `portal_sidebar`, así ninguna vista tiene que repetir esas consultas.
- Las plantillas de la app viven en `templates/news/` (espacio de nombres)
  y todos los enlaces se generan con `{% url %}`.

Detalle completo en el [paso 4](docs/paso-04-plantilla-base.md).

## Pruebas

```bash
python manage.py test news -v 2
```

Resultado: **49 pruebas, OK**. Cubren modelos y el manager `published`,
vistas y plantillas (herencia, fragmento, `{% empty %}`, 404, filtros
`date` y `truncatewords`, `block.super`), rutas con nombre, archivos
estáticos, admin, el comando `load_sample_data` y el escapado automático.
Las pruebas que crean imágenes usan un `MEDIA_ROOT` temporal.

## Índice de pasos

<!-- INDEX -->
1. [Paso 1: Creación del proyecto, Pillow y la aplicación `news`](docs/paso-01-creacion-del-proyecto.md)
2. [Paso 2: Directorio de plantillas, archivos estáticos y de medios](docs/paso-02-plantillas-estaticos-y-medios.md)
3. [Paso 3: Modelos, migración y superusuario](docs/paso-03-modelos-y-migraciones.md)
4. [Paso 4: Plantilla base con bloques](docs/paso-04-plantilla-base.md)
5. [Paso 5: Fragmento `_article_card.html` reutilizable](docs/paso-05-fragmento-tarjeta.md)
6. [Paso 6: Portada con `for`, `empty` y filtros](docs/paso-06-portada.md)
7. [Paso 7: Detalle de noticia](docs/paso-07-detalle-de-noticia.md)
8. [Paso 8: Listado por categoría](docs/paso-08-listado-por-categoria.md)
9. [Paso 9: Rutas con nombre y `{% url %}`](docs/paso-09-rutas-con-nombre.md)
10. [Paso 10: `{% load static %}`, CSS y logo](docs/paso-10-archivos-estaticos.md)
11. [Paso 11: Admin personalizado y datos de ejemplo](docs/paso-11-admin-y-datos-de-ejemplo.md)
12. [Paso 12: Prueba del escapado automático](docs/paso-12-escapado-automatico.md)
